"""
Integration tests for AI Test Intelligence API Routes — RepoMind 2.0.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, RoleEnum, OrganizationMembership, Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.testing.models import TestScenario, GeneratedTestCase


def make_client_for_user(db_session, user):
    """Create a TestClient with overridden get_current_user and get_db."""
    def _override_get_current_user():
        db_session.refresh(user)
        return user

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_current_user] = _override_get_current_user
    app.dependency_overrides[get_db] = _override_get_db
    return TestClient(app)


@pytest.fixture
def routes_data(db_session):
    user = User(
        email="developer@example.com",
        password_hash="pw",
    )
    db_session.add(user)
    db_session.flush()

    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        role=RoleEnum.DEVELOPER,
    )
    db_session.add(membership)
    db_session.flush()

    project = Project(name="Test Project", organization_id=org.id)
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="103",
        github_name="test-repo",
        github_owner="test-owner",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_103",
        github_number=1,
        title="Test PR",
        head_sha="sha1",
        base_sha="sha0",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    return db_session, user, repo, pr


def test_trigger_test_analysis_endpoint(routes_data):
    db_session, user, repo, pr = routes_data
    client = make_client_for_user(db_session, user)

    diff = """diff --git a/backend/app/service.py b/backend/app/service.py
--- a/backend/app/service.py
+++ b/backend/app/service.py
@@ -1,3 +1,6 @@
+def process_payment(amount: float) -> bool:
+    return amount > 0
"""

    resp = client.post(
        f"/repositories/{repo.id}/test-intelligence/analyze",
        json={
            "pull_request_id": pr.id,
            "diff": diff,
        },
    )

    assert resp.status_code == 201
    scenarios = resp.json()
    assert len(scenarios) == 8
    assert any(s["category"] == "positive" for s in scenarios)
    assert any(s["category"] == "boundary" for s in scenarios)


def test_get_pr_test_scenarios_and_filtering(routes_data):
    db_session, user, repo, pr = routes_data
    client = make_client_for_user(db_session, user)

    # Seed two scenarios
    s1 = TestScenario(
        repository_id=repo.id,
        pull_request_id=pr.id,
        target_file="app/order.py",
        target_symbol="create_order",
        category="positive",
        title="Order success",
        description="Creates order",
        coverage_gap=True,
    )
    s2 = TestScenario(
        repository_id=repo.id,
        pull_request_id=pr.id,
        target_file="app/order.py",
        target_symbol="create_order",
        category="negative",
        title="Order failure",
        description="Handles invalid order",
        coverage_gap=False,
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    # 1. Fetch all
    resp = client.get(f"/repositories/{repo.id}/pull-requests/{pr.id}/test-intelligence")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # 2. Filter by category
    resp_cat = client.get(f"/repositories/{repo.id}/pull-requests/{pr.id}/test-intelligence?category=positive")
    assert resp_cat.status_code == 200
    assert len(resp_cat.json()) == 1
    assert resp_cat.json()[0]["category"] == "positive"

    # 3. Filter by coverage gap
    resp_gap = client.get(f"/repositories/{repo.id}/pull-requests/{pr.id}/test-intelligence?coverage_gap_only=true")
    assert resp_gap.status_code == 200
    assert len(resp_gap.json()) == 1
    assert resp_gap.json()[0]["category"] == "positive"


def test_generate_and_execute_test_case_endpoints(routes_data):
    db_session, user, repo, pr = routes_data
    client = make_client_for_user(db_session, user)

    scenario = TestScenario(
        repository_id=repo.id,
        pull_request_id=pr.id,
        target_file="app/math_ops.py",
        target_symbol="compute_sum",
        category="positive",
        title="Valid sum",
        description="Sums two integers",
        suggested_assertions=["Result equals expected sum"],
    )
    db_session.add(scenario)
    db_session.commit()

    # 1. Generate test case
    gen_resp = client.post(f"/test-scenarios/{scenario.id}/generate", json={})
    assert gen_resp.status_code == 201
    test_case = gen_resp.json()
    test_id = test_case["id"]
    assert test_case["execution_status"] == "pending"

    # 2. Execute test case in sandbox
    exec_resp = client.post(f"/generated-tests/{test_id}/execute")
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["status"] == "passed"
    assert exec_data["returncode"] == 0
    assert exec_data["duration_ms"] > 0


def test_get_test_dashboard_endpoint(routes_data):
    db_session, user, repo, pr = routes_data
    client = make_client_for_user(db_session, user)

    scenario = TestScenario(
        repository_id=repo.id,
        pull_request_id=pr.id,
        target_file="app/user.py",
        target_symbol="get_user",
        category="positive",
        title="Get user",
        description="Gets user by id",
        coverage_gap=True,
    )
    db_session.add(scenario)
    db_session.commit()

    resp = client.get(f"/test-intelligence/dashboard/{pr.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository_id"] == repo.id
    assert data["pull_request_id"] == pr.id
    assert data["total_scenarios_count"] == 1
    assert data["coverage_gaps_count"] == 1
    assert data["category_counts"]["positive"] == 1
