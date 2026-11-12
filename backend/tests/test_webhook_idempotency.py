"""
Tests for Batch A — GitHub Webhook Idempotency & Delivery Reliability.

Covers:
1. Valid HMAC-SHA256 signature verification and rejection of invalid signatures (401).
2. Deduplication of identical X-GitHub-Delivery requests (200 with duplicate status).
3. Concurrent requests with the same X-GitHub-Delivery handled safely (no 500 error).
4. Safe retry of previously failed webhook deliveries without creating duplicate review runs.
5. Legitimate events with different delivery IDs processed independently.
"""
import hmac
import hashlib
import json
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.main import app
from backend.app.db import get_db, SessionLocal
from backend.app.core.config import settings
from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun
from backend.app.webhooks.models import WebhookEvent


WEBHOOK_SECRET = "test-secret-12345"


def compute_signature(payload_bytes: bytes, secret: str = WEBHOOK_SECRET) -> str:
    sig = hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={sig}"


@pytest.fixture
def webhook_repo_fixture(db_session: Session):
    org = Organization(name="Webhook Org")
    db_session.add(org)
    db_session.flush()

    project = Project(name="Webhook Project", organization_id=org.id)
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="gh-hook-999",
        github_owner="repomind-test",
        github_name="hook-repo",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr-gh-101",
        github_number=101,
        title="Webhook Test PR",
        state="open",
        head_sha="head1111",
        base_sha="base0000",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    return {
        "org": org,
        "project": project,
        "repo": repo,
        "pr": pr,
    }


def test_invalid_webhook_signature_rejected(webhook_repo_fixture):
    """Webhook requests with missing, invalid, or tampered signatures MUST return 401."""
    payload = {"action": "opened"}
    payload_bytes = json.dumps(payload).encode("utf-8")

    with patch.object(settings, "GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET):
        with TestClient(app) as client:
            # 1. Missing signature
            r1 = client.post(
                "/webhooks/github",
                content=payload_bytes,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "deliv-sig-1",
                    "Content-Type": "application/json",
                },
            )
            assert r1.status_code == 401

            # 2. Tampered / incorrect signature
            r2 = client.post(
                "/webhooks/github",
                content=payload_bytes,
                headers={
                    "X-GitHub-Event": "pull_request",
                    "X-GitHub-Delivery": "deliv-sig-2",
                    "X-Hub-Signature-256": "sha256=invalidhexsignature00000000000000",
                    "Content-Type": "application/json",
                },
            )
            assert r2.status_code == 401


def test_same_delivery_received_twice_is_idempotent(db_session, webhook_repo_fixture):
    """
    Submitting the same X-GitHub-Delivery twice must return 200 on both,
    with the second marked as duplicate, and only 1 ReviewRun created.
    """
    f = webhook_repo_fixture
    repo = f["repo"]

    payload = {
        "action": "opened",
        "repository": {
            "owner": {"login": repo.github_owner},
            "name": repo.github_name,
        },
        "pull_request": {
            "id": 10101,
            "number": 101,
            "head": {"sha": "head1111"},
            "base": {"sha": "base0000"},
            "title": "Webhook Test PR",
            "state": "open",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)
    delivery_id = "deliv-idempotent-001"

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.object(settings, "GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET):
            with TestClient(app) as client:
                # First delivery
                resp1 = client.post(
                    "/webhooks/github",
                    content=payload_bytes,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": delivery_id,
                        "X-Hub-Signature-256": sig,
                        "Content-Type": "application/json",
                    },
                )
                assert resp1.status_code == 200
                data1 = resp1.json()
                assert data1["status"] == "processed"
                run_id1 = data1["review_run_id"]
                assert run_id1 is not None

                # Second delivery with exact same X-GitHub-Delivery
                resp2 = client.post(
                    "/webhooks/github",
                    content=payload_bytes,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": delivery_id,
                        "X-Hub-Signature-256": sig,
                        "Content-Type": "application/json",
                    },
                )
                assert resp2.status_code == 200
                data2 = resp2.json()
                assert data2["status"] == "duplicate"

                # Check exactly one WebhookEvent and one ReviewRun
                db_session.expire_all()
                events = db_session.query(WebhookEvent).filter_by(github_delivery_id=delivery_id).all()
                assert len(events) == 1

                runs = db_session.query(ReviewRun).filter_by(pull_request_id=f["pr"].id).all()
                assert len(runs) == 1
    finally:
        app.dependency_overrides.clear()


def test_different_delivery_ids_processed_independently(db_session, webhook_repo_fixture):
    """Different delivery IDs for new commits must each be accepted and processed."""
    f = webhook_repo_fixture
    repo = f["repo"]

    def make_payload(sha):
        return {
            "action": "synchronize",
            "repository": {
                "owner": {"login": repo.github_owner},
                "name": repo.github_name,
            },
            "pull_request": {
                "id": 10101,
                "number": 101,
                "head": {"sha": sha},
                "base": {"sha": "base0000"},
                "title": "Webhook Test PR",
                "state": "open",
            },
        }

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.object(settings, "GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET):
            with TestClient(app) as client:
                # Delivery A
                body_a = json.dumps(make_payload("headAAAA")).encode("utf-8")
                resp_a = client.post(
                    "/webhooks/github",
                    content=body_a,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": "deliv-legit-A",
                        "X-Hub-Signature-256": compute_signature(body_a),
                        "Content-Type": "application/json",
                    },
                )
                assert resp_a.status_code == 200
                assert resp_a.json()["status"] == "processed"

                # Delivery B (different delivery ID)
                body_b = json.dumps(make_payload("headBBBB")).encode("utf-8")
                resp_b = client.post(
                    "/webhooks/github",
                    content=body_b,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": "deliv-legit-B",
                        "X-Hub-Signature-256": compute_signature(body_b),
                        "Content-Type": "application/json",
                    },
                )
                assert resp_b.status_code == 200
                assert resp_b.json()["status"] == "processed"

                db_session.expire_all()
                assert db_session.query(WebhookEvent).filter_by(github_delivery_id="deliv-legit-A").count() == 1
                assert db_session.query(WebhookEvent).filter_by(github_delivery_id="deliv-legit-B").count() == 1
    finally:
        app.dependency_overrides.clear()


def test_retry_after_processing_failure_succeeds_without_duplicate_records(db_session, webhook_repo_fixture):
    """
    If a previous attempt failed (event.status='failed'), a redelivery of the same
    X-GitHub-Delivery must safely re-attempt processing, mark status='processed',
    and avoid creating duplicate WebhookEvent or ReviewRun records.
    """
    f = webhook_repo_fixture
    repo = f["repo"]
    delivery_id = "deliv-retry-failure-001"

    payload = {
        "action": "opened",
        "repository": {
            "owner": {"login": repo.github_owner},
            "name": repo.github_name,
        },
        "pull_request": {
            "id": 10101,
            "number": 101,
            "head": {"sha": "headFAIL"},
            "base": {"sha": "base0000"},
            "title": "Webhook Test PR",
            "state": "open",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    # 1. Insert an existing failed webhook event
    failed_event = WebhookEvent(
        github_delivery_id=delivery_id,
        event_type="pull_request",
        action="opened",
        repository_id=repo.id,
        payload=payload,
        status="failed",
        error_message="Simulated prior database transient error",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(failed_event)
    db_session.commit()

    app.dependency_overrides[get_db] = lambda: db_session

    try:
        with patch.object(settings, "GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET):
            with TestClient(app) as client:
                resp = client.post(
                    "/webhooks/github",
                    content=payload_bytes,
                    headers={
                        "X-GitHub-Event": "pull_request",
                        "X-GitHub-Delivery": delivery_id,
                        "X-Hub-Signature-256": sig,
                        "Content-Type": "application/json",
                    },
                )
                assert resp.status_code == 200
                data = resp.json()
                # Must not just blindly return status="duplicate" while leaving it failed!
                # Must retry and report processed / retried
                assert data["status"] in ("processed", "retried")

                db_session.expire_all()
                # Verify exactly 1 WebhookEvent exists (updated in place)
                events = db_session.query(WebhookEvent).filter_by(github_delivery_id=delivery_id).all()
                assert len(events) == 1
                assert events[0].status == "processed"
                assert events[0].error_message is None

                # Verify a ReviewRun was created for the retried event
                runs = db_session.query(ReviewRun).filter_by(commit_sha="headFAIL").all()
                assert len(runs) == 1
                assert runs[0].status == "pending"
    finally:
        app.dependency_overrides.clear()


def test_concurrent_requests_with_same_delivery_id_handled_safely(webhook_repo_fixture):
    """
    Two concurrent requests with the same X-GitHub-Delivery must not raise 500.
    Database uniqueness constraint and conflict handling must guarantee:
    - Exactly 1 WebhookEvent is persisted.
    - Exactly 1 ReviewRun is enqueued.
    - Both requests complete with 200 (one processed, one duplicate).
    """
    f = webhook_repo_fixture
    repo = f["repo"]
    delivery_id = "deliv-concurrent-001"

    payload = {
        "action": "opened",
        "repository": {
            "owner": {"login": repo.github_owner},
            "name": repo.github_name,
        },
        "pull_request": {
            "id": 10101,
            "number": 101,
            "head": {"sha": "headCONC"},
            "base": {"sha": "base0000"},
            "title": "Webhook Concurrent PR",
            "state": "open",
        },
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    sig = compute_signature(payload_bytes)

    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": delivery_id,
        "X-Hub-Signature-256": sig,
        "Content-Type": "application/json",
    }

    from sqlalchemy.orm import sessionmaker
    bind = repo._sa_instance_state.session.bind
    ThreadSession = sessionmaker(bind=bind, autocommit=False, autoflush=False)

    def get_thread_db():
        db = ThreadSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_thread_db

    try:
        def post_webhook(_):
            with TestClient(app) as client:
                return client.post("/webhooks/github", content=payload_bytes, headers=headers)

        with patch.object(settings, "GITHUB_WEBHOOK_SECRET", WEBHOOK_SECRET):
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(post_webhook, i) for i in range(2)]
                responses = [f.result() for f in futures]

        statuses = [r.status_code for r in responses]
        assert statuses == [200, 200], f"Expected both 200, got: {statuses} with texts: {[r.text for r in responses]}"

        resp_data = [r.json()["status"] for r in responses]
        assert "processed" in resp_data
        assert "duplicate" in resp_data

        # Verify database state
        with ThreadSession() as db:
            events = db.query(WebhookEvent).filter_by(github_delivery_id=delivery_id).all()
            assert len(events) == 1
            assert events[0].status == "processed"
            runs = db.query(ReviewRun).filter_by(commit_sha="headCONC").all()
            assert len(runs) == 1
    finally:
        app.dependency_overrides.clear()
