import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from backend.app.main import app
from backend.app.db import get_db
from backend.app.webhooks.models import WebhookEvent
from backend.app.review.models import ReviewRun
from backend.app.github.models import PullRequest
from backend.app.organizations.models import Repository, Project
from backend.app.auth.models import Organization

def get_test_db():
    yield db_session

app.dependency_overrides[get_db] = get_test_db
client = TestClient(app)

def _setup_repo_and_pr(db: Session):
    org = Organization(name="Test Org")
    db.add(org)
    db.flush()

    project = Project(name="Test Project", organization_id=org.id)
    db.add(project)
    db.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="123456",
        github_owner="testowner",
        github_name="testrepo",
    )
    db.add(repo)
    db.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="12345",
        github_number=1,
        title="Test PR",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(pr)
    db.flush()

    run = ReviewRun(
        pull_request_id=pr.id,
        status="completed",
        progress_message="Done",
        commit_sha="abcd123",
    )
    db.add(run)
    db.flush()

    db.commit()
    return repo.id, pr.id, run.id

@patch("backend.app.webhooks.routes._verify_github_signature")
def test_review_comment_updates_existing_run(mock_verify, db_session: Session):
    mock_verify.return_value = True

    global db_session_global
    db_session_global = db_session
    
    app.dependency_overrides[get_db] = lambda: db_session

    repo_id, pr_id, run_id = _setup_repo_and_pr(db_session)

    payload = {
        "action": "created",
        "repository": {
            "owner": {"login": "testowner"},
            "name": "testrepo",
        },
        "pull_request": {
            "id": 12345,
            "number": 1,
        }
    }

    # Trigger comment webhook
    response = client.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-GitHub-Event": "pull_request_review_comment",
            "X-GitHub-Delivery": "test-delivery-1",
            "X-Hub-Signature-256": "sha256=dummy"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processed"
    
    # Assert ReviewRun is re-used (ID is the same)
    assert data["review_run_id"] == run_id

    # Verify run status is pending now
    db_session.expire_all()
    run = db_session.query(ReviewRun).filter(ReviewRun.id == run_id).first()
    assert run.status == "pending"
    assert run.progress_message == "Re-queued via comment webhook"

    # Verify no duplicate ReviewRun created
    run_count = db_session.query(ReviewRun).filter(ReviewRun.pull_request_id == pr_id).count()
    assert run_count == 1
