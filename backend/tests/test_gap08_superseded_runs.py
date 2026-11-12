import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun
from backend.app.webhooks.routes import _enqueue_review
from backend.app.review.service import run_review
from backend.app.review.provider import LocalProvider


def _setup_repo_and_pr(db: Session, pr_number: int = 100):
    org = Organization(name=f"Supersede Org {pr_number}")
    db.add(org)
    db.flush()

    project = Project(name=f"Supersede Proj {pr_number}", organization_id=org.id)
    db.add(project)
    db.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id=f"gh_sup_{pr_number}",
        github_owner="testowner",
        github_name=f"testrepo_{pr_number}",
    )
    db.add(repo)
    db.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id=f"gh_pr_{pr_number}",
        github_number=pr_number,
        title="Supersede Test PR",
        head_sha="sha_v1",
        created_at=datetime.now(timezone.utc),
    )
    db.add(pr)
    db.commit()
    return org, project, repo, pr


def test_gap_08_new_head_sha_supersedes_pending_and_running_runs(db_session: Session):
    """
    GAP-08: When a new commit SHA arrives for a PR, any existing pending or running
    review runs for older SHAs on that PR must transition to 'superseded'.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=101)

    # 1. Enqueue initial review for sha_v1
    payload_v1 = {
        "number": 101,
        "head": {"sha": "sha_v1", "ref": "feature"},
        "base": {"sha": "main_sha", "ref": "main"},
        "title": "PR 101",
    }
    run1 = _enqueue_review(db_session, repo.id, payload_v1)
    db_session.commit()
    assert run1.status == "pending"
    assert run1.commit_sha == "sha_v1"

    # Simulate worker picking it up to 'running'
    run1.status = "running"
    db_session.commit()

    # 2. Enqueue another run for sha_v1 (should skip duplicate)
    run1_dup = _enqueue_review(db_session, repo.id, payload_v1)
    assert run1_dup.id == run1.id

    # 3. New commit arrives: sha_v2
    payload_v2 = {
        "number": 101,
        "head": {"sha": "sha_v2", "ref": "feature"},
        "base": {"sha": "main_sha", "ref": "main"},
        "title": "PR 101 with update",
    }
    run2 = _enqueue_review(db_session, repo.id, payload_v2)
    db_session.commit()

    assert run2.id != run1.id
    assert run2.status == "pending"
    assert run2.commit_sha == "sha_v2"

    # Verify run1 was superseded!
    db_session.refresh(run1)
    assert run1.status == "superseded"
    assert "superseded by newer commit sha_v2" in run1.progress_message.lower()


def test_gap_08_completed_historical_runs_are_preserved(db_session: Session):
    """
    GAP-08: Completed historical runs for older SHAs must NOT be superseded.
    They must remain completed for auditability.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=102)

    # Create a completed historical run for sha_v1
    historical_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_v1",
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(historical_run)
    db_session.commit()

    # New commit arrives: sha_v2
    payload_v2 = {
        "number": 102,
        "head": {"sha": "sha_v2", "ref": "feature"},
        "base": {"sha": "main_sha", "ref": "main"},
        "title": "PR 102 update",
    }
    run2 = _enqueue_review(db_session, repo.id, payload_v2)
    db_session.commit()

    # historical_run must STILL be completed
    db_session.refresh(historical_run)
    assert historical_run.status == "completed"


def test_gap_08_superseded_worker_aborts_without_overwriting(db_session: Session):
    """
    GAP-08: If a worker was already executing a run that gets marked 'superseded'
    or has become stale relative to the PR's latest commit, the pipeline must abort
    without persisting findings, risk assessments, or overwriting run.status to 'completed'.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=103)

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_stale",
        status="superseded",
        progress_message="Superseded by newer commit",
    )
    db_session.add(run)
    db_session.commit()

    mock_provider = LocalProvider()
    result_run = run_review(
        db=db_session,
        pull_request_id=pr.id,
        organization_id=org.id,
        provider=mock_provider,
        existing_review_run_id=run.id,
    )

    db_session.refresh(run)
    assert run.status == "superseded"
    assert len(run.findings) == 0
    assert run.risk_assessment is None


def test_gap_08_worker_ownership_fencing_token_invalidation(db_session: Session):
    """
    GAP-08: If a worker holds a stale claim_token and the run's claim_token in the DB
    was cleared or rotated (e.g. superseded or reclaimed), the worker's execution must abort
    without persisting findings or risk assessment.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=104)

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        claim_token="token_worker_2",  # DB already has a new token
        progress_message="Running by worker 2",
    )
    db_session.add(run)
    db_session.commit()

    mock_provider = LocalProvider()
    # Worker 1 tries to run using its old token "token_worker_1"
    result = run_review(
        db=db_session,
        pull_request_id=pr.id,
        organization_id=org.id,
        provider=mock_provider,
        existing_review_run_id=run.id,
        claim_token="token_worker_1",  # Mismatch!
    )

    db_session.refresh(run)
    # Status and token in DB must remain intact, and no findings written by Worker 1
    assert run.claim_token == "token_worker_2"
    assert len(run.findings) == 0
    assert run.risk_assessment is None


def test_gap_08_stale_worker_attempting_to_publish_while_requeued_run_is_inflight(db_session: Session):
    """
    GAP-08: Even if the run is still in status 'running' (because another worker claimed it),
    a stale worker with an outdated claim token must NOT overwrite or publish results.
    """
    from backend.app.review.service import _update_progress

    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=105)

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        claim_token="fresh_token_worker_b",
        progress_message="Worker B working",
    )
    db_session.add(run)
    db_session.commit()

    # Worker A tries to send heartbeat or progress with stale token
    heartbeat_ok = _update_progress(
        db=db_session,
        run=run,
        message="Worker A updating heartbeat",
        claim_token="stale_token_worker_a",
    )
    assert heartbeat_ok is False

    # Worker A tries to run_review to publish results
    mock_provider = LocalProvider()
    run_review(
        db=db_session,
        pull_request_id=pr.id,
        organization_id=org.id,
        provider=mock_provider,
        existing_review_run_id=run.id,
        claim_token="stale_token_worker_a",
    )

    db_session.refresh(run)
    assert run.claim_token == "fresh_token_worker_b"
    assert run.status == "running"  # Still running under Worker B
    assert len(run.findings) == 0


def test_gap_08_concurrent_duplicate_webhooks_serialization(db_session: Session):
    """
    GAP-08: Concurrency integration test using separate PostgreSQL sessions and concurrent threads.
    Verifies that concurrent duplicate webhooks for the same PR are serialized by row locking
    and do not generate duplicate ReviewRun records.
    """
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy.orm import sessionmaker

    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=106)
    repo_id = repo.id
    pr_number = pr.github_number

    payload = {
        "number": pr_number,
        "head": {"sha": "sha_concurrent", "ref": "feature"},
        "base": {"sha": "main_sha", "ref": "main"},
        "title": "PR Concurrent Test",
    }

    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)

    def deliver_webhook():
        with session_factory() as session:
            run = _enqueue_review(session, repo_id, payload)
            session.commit()
            return run.id if run else None

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(deliver_webhook)
        f2 = executor.submit(deliver_webhook)
        run_id_1 = f1.result()
        run_id_2 = f2.result()

    # Both deliveries should resolve to the exact same ReviewRun id
    assert run_id_1 is not None
    assert run_id_2 is not None
    assert run_id_1 == run_id_2

    with session_factory() as session:
        runs = session.query(ReviewRun).filter(ReviewRun.commit_sha == "sha_concurrent").all()
        assert len(runs) == 1
