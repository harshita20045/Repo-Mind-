import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.auth.models import OrganizationMembership, User, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest, GitHubIdentity
from backend.app.review.models import ReviewRun
from backend.app.main import app
from backend.app.auth.dependencies import get_current_user
from backend.app.db import get_db

@pytest.fixture
def test_setup(db_session):
    from backend.app.auth.models import Organization
    org = Organization(name="test_org")
    db_session.add(org)
    db_session.commit()
    
    project = Project(organization_id=org.id, name="test_project")
    db_session.add(project)
    db_session.commit()
    
    repo = Repository(project_id=project.id, github_repository_id="test_repo", github_owner="owner", github_name="repo")
    db_session.add(repo)
    db_session.commit()
    
    pr = PullRequest(repository_id=repo.id, github_number=1, head_sha="sha1", github_pr_id="123", title="test pr", created_at=datetime.now(timezone.utc))
    db_session.add(pr)
    db_session.commit()

    run = ReviewRun(pull_request_id=pr.id, commit_sha="sha1", status="completed", repomind_version="1", prompt_version="1", llm_model="test")
    db_session.add(run)
    db_session.commit()
    
    return org, project, repo, pr, run

def run_decision_test(db_session, test_setup, role: str, action: str, expected_status: int):
    org, project, repo, pr, run = test_setup
    
    user = User(email=f"test_{role}_{action}@example.com")
    db_session.add(user)
    db_session.commit()
    
    identity = GitHubIdentity(user_id=user.id, github_login=f"gh_{role}_{action}", github_user_id=f"100_{role}_{action}")
    db_session.add(identity)
    
    mem = OrganizationMembership(user_id=user.id, organization_id=org.id, role=role)
    db_session.add(mem)
    db_session.commit()
    
    def override_get_current_user():
        db_session.refresh(user)
        return user
        
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    
    try:
        with TestClient(app) as client:
            response = client.post(f"/review-runs/{run.id}/decide", json={"action": action, "note": "test"})
            assert response.status_code == expected_status
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)

def test_approve_org_admin(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.ORG_ADMIN.value, "APPROVE", 200)

def test_approve_team_lead(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.TEAM_LEAD.value, "APPROVE", 200)

def test_approve_reviewer(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.REVIEWER.value, "APPROVE", 403)

def test_approve_developer(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.DEVELOPER.value, "APPROVE", 403)

def test_reject_org_admin(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.ORG_ADMIN.value, "REQUEST_CHANGES", 200)

def test_reject_team_lead(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.TEAM_LEAD.value, "REQUEST_CHANGES", 200)

def test_reject_reviewer(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.REVIEWER.value, "REQUEST_CHANGES", 200)

def test_reject_developer(db_session, test_setup):
    run_decision_test(db_session, test_setup, RoleEnum.DEVELOPER.value, "REQUEST_CHANGES", 403)
