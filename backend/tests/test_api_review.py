import pytest
from unittest.mock import patch
from datetime import datetime
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.models import Organization, User, OrganizationMembership
from backend.app.auth.service import hash_password
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun, Finding

@pytest.fixture
def api_test_data(db_session):
    """Seed data for API tests."""
    org = Organization(name="API Test Org")
    db_session.add(org)
    db_session.commit()

    user = User(email="api_user@test.com", password_hash=hash_password("password123"))
    db_session.add(user)
    db_session.commit()

    membership = OrganizationMembership(user_id=user.id, organization_id=org.id, role="developer")
    db_session.add(membership)
    db_session.commit()

    from backend.app.organizations.models import GithubConnection
    from backend.app.github.service import encrypt_token
    github_conn = GithubConnection(
        organization_id=org.id,
        encrypted_token=encrypt_token("dummy_pat")
    )
    db_session.add(github_conn)
    db_session.commit()

    user2 = User(email="other_user@test.com", password_hash=hash_password("password123"))
    db_session.add(user2)
    db_session.commit()

    project = Project(organization_id=org.id, name="Test Project")
    db_session.add(project)
    db_session.commit()

    repo = Repository(
        project_id=project.id,
        github_owner="test_owner",
        github_name="test_repo",
        default_branch="main"
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_number=1,
        title="Test PR",
        state="open",
        author="author1",
        head_sha="sha1",
        created_at=datetime.utcnow()
    )
    db_session.add(pr)
    db_session.commit()
    db_session.refresh(pr)

    return {
        "org": org,
        "user": user,
        "repo": repo,
        "pr": pr,
        "user2": user2
    }

@pytest.fixture
def auth_client(client, api_test_data):
    # Login
    response = client.post("/auth/login", json={"email": "api_user@test.com", "password": "password123"})
    assert response.status_code == 200
    return client

@pytest.fixture
def auth_client2(client, api_test_data):
    response = client.post("/auth/login", json={"email": "other_user@test.com", "password": "password123"})
    assert response.status_code == 200
    return client

def test_trigger_review_unauthenticated(client, api_test_data):
    pr = api_test_data["pr"]
    response = client.post(f"/pull-requests/{pr.id}/review")
    assert response.status_code == 401

def test_trigger_review_cross_tenant(auth_client2, api_test_data):
    pr = api_test_data["pr"]
    response = auth_client2.post(f"/pull-requests/{pr.id}/review")
    # user2 is not in org1, so verify_org_member raises 404
    assert response.status_code == 404

def test_trigger_review_creates_pending_job_and_returns_202(auth_client, api_test_data, db_session):
    pr = api_test_data["pr"]

    with patch("backend.app.review.router.GitHubClient") as MockClient:
        # Mock github client to return a new sha
        MockClient.return_value.get_pull_request.return_value = {"head": {"sha": "sha_new"}}

        response = auth_client.post(f"/pull-requests/{pr.id}/review")
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"

        run = db_session.get(ReviewRun, data["job_id"])
        assert run is not None
        assert run.commit_sha == "sha_new"
        assert run.status == "pending"

        db_session.refresh(pr)
        assert pr.head_sha == "sha_new"

def test_trigger_review_duplicate_returns_idempotent(auth_client, api_test_data, db_session):
    pr = api_test_data["pr"]

    with patch("backend.app.review.router.GitHubClient") as MockClient:
        MockClient.return_value.get_pull_request.return_value = {"head": {"sha": "sha2"}}

        # First request
        res1 = auth_client.post(f"/pull-requests/{pr.id}/review")
        assert res1.status_code == 202
        job_id1 = res1.json()["job_id"]

        # Second request
        res2 = auth_client.post(f"/pull-requests/{pr.id}/review")
        assert res2.status_code == 202
        job_id2 = res2.json()["job_id"]

        # Must return the identical job_id
        assert job_id1 == job_id2

        # Verify only one was created
        runs = db_session.query(ReviewRun).filter(ReviewRun.pull_request_id == pr.id).all()
        assert len(runs) == 1

def test_get_review_run(auth_client, api_test_data, db_session):
    pr = api_test_data["pr"]

    # Create a dummy run
    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha1",
        status="completed",
        repomind_version="1",
        prompt_version="1",
        llm_model="model",
        rag_enabled=True,
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    finding = Finding(
        review_run_id=run.id,
        type="style",
        severity="low",
        title="Title",
        explanation="Explain",
        confidence=0.9,
        status="open"
    )
    db_session.add(finding)
    db_session.commit()

    response = auth_client.get(f"/review-runs/{run.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == run.id
    assert data["status"] == "completed"
    assert len(data["findings"]) == 1
    assert data["findings"][0]["title"] == "Title"

def test_get_review_run_cross_tenant(auth_client2, api_test_data, db_session):
    pr = api_test_data["pr"]

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha1",
        status="pending",
        repomind_version="1",
        prompt_version="1",
        llm_model="model",
        rag_enabled=True,
        started_at=datetime.utcnow()
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    response = auth_client2.get(f"/review-runs/{run.id}")
    assert response.status_code == 404
