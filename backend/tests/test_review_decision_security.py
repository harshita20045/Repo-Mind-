import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.models import Organization, OrganizationMembership, User, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest, GitHubIdentity, AutomationAction
from backend.app.review.models import ReviewRun
from backend.app.auth.dependencies import get_current_user
from backend.app.db import get_db
from backend.app.github.automation import process_automation_actions
from unittest.mock import patch, MagicMock


@pytest.fixture
def decision_fixture(db_session):
    org = Organization(name="Decision Org")
    db_session.add(org)
    db_session.commit()

    proj = Project(organization_id=org.id, name="Decision Project")
    db_session.add(proj)
    db_session.commit()

    repo = Repository(
        project_id=proj.id,
        github_repository_id="gh_dec_repo",
        github_owner="org",
        github_name="repo"
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_number=10,
        head_sha="commit123456789012345678901234567890123456",
        github_pr_id="pr_10",
        title="PR 10",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(pr)
    db_session.commit()

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="completed",
        repomind_version="1",
        prompt_version="1",
        llm_model="test"
    )
    db_session.add(run)
    db_session.commit()

    # Users
    lead = User(email="lead@dec.com")
    reviewer = User(email="reviewer@dec.com")
    developer = User(email="dev@dec.com")
    db_session.add_all([lead, reviewer, developer])
    db_session.commit()

    db_session.add_all([
        GitHubIdentity(user_id=lead.id, github_login="gh_lead", github_user_id="1"),
        GitHubIdentity(user_id=reviewer.id, github_login="gh_rev", github_user_id="2"),
        GitHubIdentity(user_id=developer.id, github_login="gh_dev", github_user_id="3"),
        OrganizationMembership(user_id=lead.id, organization_id=org.id, role=RoleEnum.TEAM_LEAD.value),
        OrganizationMembership(user_id=reviewer.id, organization_id=org.id, role=RoleEnum.REVIEWER.value),
        OrganizationMembership(user_id=developer.id, organization_id=org.id, role=RoleEnum.DEVELOPER.value),
    ])
    db_session.commit()

    return {
        "org": org,
        "repo": repo,
        "pr": pr,
        "run": run,
        "lead": lead,
        "reviewer": reviewer,
        "developer": developer,
    }


def test_def_02_action_casing_cannot_bypass_approve_permission(db_session, decision_fixture):
    """
    DEF-02: A reviewer sending action="approve" (lowercase) MUST NOT bypass
    the PRS_APPROVE permission check. It must return 403 Forbidden.
    """
    f = decision_fixture
    reviewer = f["reviewer"]
    run = f["run"]

    def override_user():
        db_session.refresh(reviewer)
        return reviewer

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/review-runs/{run.id}/decide",
                json={"action": "approve", "note": "trying to bypass with lowercase"}
            )
            # Reviewer lacks PRS_APPROVE: must return 403 even with lowercase action
            assert resp.status_code == 403, f"Expected 403, got {resp.status_code}: {resp.text}"
    finally:
        app.dependency_overrides.clear()


def test_def_02_lead_approve_normalized_and_triggers_merge_policy(db_session, decision_fixture):
    """
    Team Lead sending action="approve" or "APPROVE" gets normalized to "APPROVE",
    succeeds with 200, and triggers merge policy evaluation.
    """
    f = decision_fixture
    lead = f["lead"]
    run = f["run"]

    def override_user():
        db_session.refresh(lead)
        return lead

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with patch("backend.app.github.automation.evaluate_merge_policy") as mock_eval:
            with TestClient(app) as client:
                resp = client.post(
                    f"/review-runs/{run.id}/decide",
                    json={"action": "approve", "note": "lead approval"}
                )
                assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
                assert resp.json()["action"] == "APPROVE"
                mock_eval.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_def_02_reject_permission_and_queue_worker(db_session, decision_fixture):
    """
    REJECT requires PRS_REQUEST_CHANGES (Reviewer has it, Developer does not).
    The automation worker must process REJECT without throwing Unknown action_type.
    """
    f = decision_fixture
    developer = f["developer"]
    reviewer = f["reviewer"]
    run = f["run"]
    pr = f["pr"]

    # 1. Developer cannot REJECT
    def override_dev():
        db_session.refresh(developer)
        return developer

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_dev
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            resp_dev = client.post(
                f"/review-runs/{run.id}/decide",
                json={"action": "REJECT", "note": "dev reject"}
            )
            assert resp_dev.status_code == 403
    finally:
        app.dependency_overrides.clear()

    # 2. Reviewer can REJECT
    def override_rev():
        db_session.refresh(reviewer)
        return reviewer

    app.dependency_overrides[get_current_user] = override_rev
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            resp_rev = client.post(
                f"/review-runs/{run.id}/decide",
                json={"action": "reject", "note": "reviewer reject"}
            )
            assert resp_rev.status_code == 200
            assert resp_rev.json()["action"] == "REJECT"

            # Check PR status updated to REJECTED
            db_session.refresh(pr)
            assert pr.status == "REJECTED"

            # 3. Test that background worker executes the queued action
            with patch("backend.app.github.automation._get_token_for_identity", return_value="dummy_pat"):
                with patch("backend.app.github.automation.GitHubClient") as mock_gh_cls:
                    mock_client = MagicMock()
                    mock_client.submit_pull_request_review.return_value = {"id": 12345}
                    mock_gh_cls.return_value = mock_client

                    process_automation_actions(db_session)

                    # Action should be COMPLETED, not FAILED with Unknown action_type
                    action = db_session.query(AutomationAction).filter_by(pull_request_id=pr.id).first()
                    assert action is not None
                    assert action.status == "COMPLETED"
    finally:
        app.dependency_overrides.clear()


def test_def_02_arbitrary_unsupported_action_rejected(db_session, decision_fixture):
    """
    Arbitrary decision actions like 'DISMISS' or 'FOOBAR' must be rejected with 422 Unprocessable Entity.
    """
    f = decision_fixture
    lead = f["lead"]
    run = f["run"]

    def override_user():
        db_session.refresh(lead)
        return lead

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            resp = client.post(
                f"/review-runs/{run.id}/decide",
                json={"action": "DISMISS", "note": "arbitrary action"}
            )
            assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_def_06_missing_pull_request_returns_404_no_500(db_session, decision_fixture):
    """
    DEF-06: When a review run exists but its associated PullRequest is missing,
    the endpoint must return 404 Not Found cleanly without throwing AttributeError (500).
    """
    f = decision_fixture
    lead = f["lead"]
    run = f["run"]
    run_id = run.id

    def override_user():
        db_session.refresh(lead)
        return lead

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    # Simulate scenario where db.get(PullRequest, run.pull_request_id) returns None
    with patch("backend.app.review.router.Session.get") as mock_get:
        def side_effect(entity, ident):
            if entity == ReviewRun and ident == run_id:
                return run
            if entity == PullRequest:
                return None
            return db_session.get(entity, ident)
        
        mock_get.side_effect = side_effect

        try:
            with TestClient(app) as client:
                resp = client.post(
                    f"/review-runs/{run_id}/decide",
                    json={"action": "APPROVE", "note": "Approving orphan run"}
                )
                assert resp.status_code == 404
                assert "Pull request associated with this review run not found" in resp.json()["detail"]
        finally:
            app.dependency_overrides.clear()
