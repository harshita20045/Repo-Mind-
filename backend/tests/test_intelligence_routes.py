import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    PackageDependency,
    RepositoryScanSummary,
)


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


def cleanup_overrides():
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def auth_context(db_session):
    # Setup Org 1 + User 1
    org1 = Organization(name="Intelligence Test Org 1")
    db_session.add(org1)
    db_session.commit()

    user1 = User(email="intel_user1@example.com", password_hash="hash")
    db_session.add(user1)
    db_session.commit()

    membership1 = OrganizationMembership(
        user_id=user1.id,
        organization_id=org1.id,
        role=RoleEnum.DEVELOPER,
    )
    db_session.add(membership1)
    db_session.commit()

    project1 = Project(organization_id=org1.id, name="Project Alpha")
    db_session.add(project1)
    db_session.commit()

    repo1 = Repository(
        project_id=project1.id,
        github_owner="org1",
        github_name="repo1",
        github_repository_id="7701",
        default_branch="main",
    )
    db_session.add(repo1)
    db_session.commit()

    # Populate sample intelligence data for repo1
    summary = RepositoryScanSummary(
        repository_id=repo1.id,
        primary_language="Python",
        frameworks=["FastAPI", "SQLAlchemy"],
        entry_points=["backend/main.py"],
        stats={"total_files": 10, "nodes_count": 5, "dependencies_count": 2},
        architecture_summary="FastAPI + PostgreSQL architecture.",
        mermaid_diagram="flowchart TD\n    A --> B",
        scanned_commit_sha="sha123",
    )
    node1 = CodeGraphNode(
        repository_id=repo1.id,
        node_key="fn:backend/main.py:app",
        node_type="function",
        name="app",
        file_path="backend/main.py",
        start_line=1,
        end_line=10,
    )
    node2 = CodeGraphNode(
        repository_id=repo1.id,
        node_key="model:backend/models.py:User",
        node_type="db_model",
        name="User",
        file_path="backend/models.py",
        start_line=12,
        end_line=30,
    )
    dep1 = PackageDependency(
        repository_id=repo1.id,
        ecosystem="pypi",
        package_name="fastapi",
        version_spec=">=0.115.0",
    )
    db_session.add_all([summary, node1, node2, dep1])
    db_session.commit()

    edge = CodeGraphEdge(
        repository_id=repo1.id,
        source_node_id=node1.id,
        target_node_id=node2.id,
        relation_type="interacts_with",
    )
    db_session.add(edge)
    db_session.commit()

    # Org 2 + User 2 (for cross-tenant checks)
    org2 = Organization(name="Intelligence Test Org 2")
    user2 = User(email="intel_user2@example.com", password_hash="hash")
    db_session.add_all([org2, user2])
    db_session.commit()
    membership2 = OrganizationMembership(
        user_id=user2.id,
        organization_id=org2.id,
        role=RoleEnum.DEVELOPER,
    )
    db_session.add(membership2)
    db_session.commit()

    yield {
        "repo1_id": repo1.id,
        "user1": user1,
        "user2": user2,
    }
    cleanup_overrides()


def test_get_summary_authorized(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["primary_language"] == "Python"
    assert "FastAPI" in data["frameworks"]
    assert data["scanned_commit_sha"] == "sha123"


def test_get_summary_cross_tenant_forbidden(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user2"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/summary")
    assert resp.status_code in (403, 404)


def test_get_graph_and_filtering(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/graph?node_type=function")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_nodes"] >= 2
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["name"] == "app"


def test_get_architecture_diagram(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/architecture-diagram")
    assert resp.status_code == 200
    assert "mermaid_diagram" in resp.json()
    assert "flowchart TD" in resp.json()["mermaid_diagram"]


def test_get_dependencies(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/dependencies")
    assert resp.status_code == 200
    deps = resp.json()
    assert len(deps) >= 1
    assert deps[0]["package_name"] == "fastapi"


def test_get_symbols_search(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.get(f"/repositories/{auth_context['repo1_id']}/intelligence/symbols?search=User")
    assert resp.status_code == 200
    symbols = resp.json()
    assert len(symbols) == 1
    assert symbols[0]["name"] == "User"
    assert symbols[0]["symbol_type"] == "db_model"


def test_trigger_indexing_endpoint(db_session, auth_context):
    client = make_client_for_user(db_session, auth_context["user1"])
    resp = client.post(f"/repositories/{auth_context['repo1_id']}/intelligence/index")
    assert resp.status_code == 202
    data = resp.json()
    assert data["status"] == "unindexed"
    assert data["repository_id"] == auth_context["repo1_id"]
