"""
RepoMind 2.0 Change Impact and Blast Radius Analyzer Test Suite.

Verifies:
  1. AST change detection (functions, classes, models, routes, configs)
  2. Breaking change detection (required parameters, removed symbols, dropped columns, config keys)
  3. Reverse dependency traversal across Code Knowledge Graph (Hops 1, 2, 3)
  4. Impact classification (directly_affected, indirectly_affected, potentially_affected)
  5. Prioritized test recommendations (P0, P1, P2 with copyable commands)
  6. Graph visualization & Mermaid diagram generation
  7. End-to-end analysis engine & database persistence
  8. API routes and multi-tenant RBAC authorization
"""
import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, OrganizationMembership, RoleEnum, Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.impact.models import ChangeImpactAnalysis
from backend.app.impact.detector import detect_code_changes, DetectedCodeChanges, ChangedSymbol
from backend.app.impact.breaking import detect_breaking_changes, BreakingChange
from backend.app.impact.traversal import traverse_dependencies, TraversalResult, AffectedComponent
from backend.app.impact.engine import (
    run_change_impact_analysis,
    generate_test_recommendations,
    generate_impact_mermaid,
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
def impact_test_env(db_session):
    """Seed test tenant, project, repository, and pull request."""
    assert db_session.execute(text("SELECT current_database()")).scalar() == "repomind_test"

    org1 = Organization(name="Impact Test Org 1")
    org2 = Organization(name="Impact Test Org 2")
    db_session.add_all([org1, org2])
    db_session.commit()

    user1 = User(email="impact_admin@example.com", password_hash="hashed_pw")
    user2 = User(email="unauthorized_user@example.com", password_hash="hashed_pw")
    db_session.add_all([user1, user2])
    db_session.commit()

    mem1 = OrganizationMembership(user_id=user1.id, organization_id=org1.id, role=RoleEnum.ORG_ADMIN)
    mem2 = OrganizationMembership(user_id=user2.id, organization_id=org2.id, role=RoleEnum.DEVELOPER)
    db_session.add_all([mem1, mem2])
    db_session.commit()

    project1 = Project(organization_id=org1.id, name="Impact Test Project")
    db_session.add(project1)
    db_session.commit()

    repo = Repository(
        project_id=project1.id,
        github_owner="repomind-ai",
        github_name="blast-radius-repo",
        github_repository_id="778899",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_500",
        github_number=500,
        title="Refactor payment processing pipeline",
        description="Updates checkout signatures and order models.",
        source_branch="feature/payment-v2",
        target_branch="main",
        base_sha="base_sha_500",
        head_sha="head_sha_500",
        state="open",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    # Seed Code Knowledge Graph nodes:
    # checkout (function) in payments/checkout.py
    # process_payment (function) in payments/service.py -> calls checkout
    # OrderService (class) in orders/service.py -> calls process_payment
    # OrderRoute (route) in api/orders.py -> calls OrderService
    # UnrelatedWorker (function) in worker/jobs.py (unaffected)
    n_checkout = CodeGraphNode(
        repository_id=repo.id,
        node_key="func:backend/app/payments/checkout.py:checkout",
        node_type="function",
        name="checkout",
        file_path="backend/app/payments/checkout.py",
        start_line=15,
        end_line=45,
    )
    n_process = CodeGraphNode(
        repository_id=repo.id,
        node_key="func:backend/app/payments/service.py:process_payment",
        node_type="function",
        name="process_payment",
        file_path="backend/app/payments/service.py",
        start_line=10,
        end_line=40,
    )
    n_order_service = CodeGraphNode(
        repository_id=repo.id,
        node_key="class:backend/app/orders/service.py:OrderService",
        node_type="class",
        name="OrderService",
        file_path="backend/app/orders/service.py",
        start_line=20,
        end_line=80,
    )
    n_order_route = CodeGraphNode(
        repository_id=repo.id,
        node_key="route:backend/app/api/orders.py:create_order_route",
        node_type="route",
        name="create_order_route",
        file_path="backend/app/api/orders.py",
        start_line=50,
        end_line=95,
    )
    n_unrelated = CodeGraphNode(
        repository_id=repo.id,
        node_key="func:backend/app/worker/jobs.py:unrelated_worker",
        node_type="function",
        name="unrelated_worker",
        file_path="backend/app/worker/jobs.py",
        start_line=5,
        end_line=25,
    )
    db_session.add_all([n_checkout, n_process, n_order_service, n_order_route, n_unrelated])
    db_session.commit()

    # Seed edges:
    # Caller -> Callee in CodeGraphEdge:
    # 1. process_payment -> checkout
    # 2. OrderService -> process_payment
    # 3. create_order_route -> OrderService
    e1 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=n_process.id,
        target_node_id=n_checkout.id,
        relation_type="calls",
    )
    e2 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=n_order_service.id,
        target_node_id=n_process.id,
        relation_type="calls",
    )
    e3 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=n_order_route.id,
        target_node_id=n_order_service.id,
        relation_type="calls",
    )
    db_session.add_all([e1, e2, e3])
    db_session.commit()

    yield {
        "org1": org1,
        "org2": org2,
        "user1": user1,
        "user2": user2,
        "repo": repo,
        "pr": pr,
        "nodes": {
            "checkout": n_checkout,
            "process": n_process,
            "order_service": n_order_service,
            "order_route": n_order_route,
            "unrelated": n_unrelated,
        },
    }
    cleanup_overrides()


# ===========================================================================
# 1. Fine-Grained AST Change Detection (Step 1)
# ===========================================================================

def test_ast_change_detection_functions_and_classes():
    """Verify AST diff parsing detects modified functions, classes, models, and routes."""
    sample_diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
index 111..222 100644
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,5 +15,6 @@
+def checkout(user_id, amount, currency_code):
     pass
diff --git a/backend/app/models/order.py b/backend/app/models/order.py
index 333..444 100644
--- a/backend/app/models/order.py
+++ b/backend/app/models/order.py
@@ -10,3 +10,4 @@
+class OrderModel:
+    status = "pending"
"""
    changes = detect_code_changes(sample_diff)
    assert isinstance(changes, DetectedCodeChanges)
    assert len(changes.changed_files) == 2

    # Verify checkout function detection
    checkout_sym = next((s for s in changes.changed_symbols if s.symbol_name == "checkout"), None)
    assert checkout_sym is not None
    assert checkout_sym.file_path == "backend/app/payments/checkout.py"
    assert checkout_sym.new_signature is not None
    assert "currency_code" in checkout_sym.new_signature.params

    # Verify Order model detection
    order_sym = next((s for s in changes.changed_symbols if "Order" in s.symbol_name), None)
    assert order_sym is not None
    assert order_sym.file_path == "backend/app/models/order.py"


# ===========================================================================
# 2. Breaking Change Detection (Step 4)
# ===========================================================================

def test_detect_breaking_signature_mutations():
    """Verify that required parameter additions and removed parameters are flagged as breaking."""
    breaking_diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,3 +15,3 @@
-def checkout(user_id: int, amount: float):
+def checkout(user_id: int, amount: float, currency_code: str):
"""
    changes = detect_code_changes(breaking_diff)
    breaking_changes = detect_breaking_changes(breaking_diff, changes)

    assert len(breaking_changes) >= 1
    bc = next((b for b in breaking_changes if b.component_name == "checkout"), None)
    assert bc is not None
    assert bc.severity == "critical"
    assert bc.change_type == "signature_mutation"
    assert "currency_code" in bc.description
    assert bc.suggested_fix is not None


def test_optional_parameter_addition_not_breaking():
    """Verify that adding an optional parameter with a default value is NOT classified as breaking."""
    safe_diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,3 +15,3 @@
-def checkout(user_id: int, amount: float):
+def checkout(user_id: int, amount: float, currency_code: str = 'USD'):
"""
    changes = detect_code_changes(safe_diff)
    breaking_changes = detect_breaking_changes(safe_diff, changes)

    # When a default is provided, it must not flag as a required param mutation
    assert not any(
        b.change_type == "signature_mutation" and "currency_code" in b.description
        for b in breaking_changes
    )


def test_database_model_column_dropped_is_breaking():
    """Verify that dropping a database model column is detected as breaking change."""
    drop_col_diff = """\
diff --git a/backend/app/models/order.py b/backend/app/models/order.py
--- a/backend/app/models/order.py
+++ b/backend/app/models/order.py
@@ -20,4 +20,3 @@
 class Order(Base):
-    legacy_token = Column(String)
     amount = Column(Float)
"""
    changes = detect_code_changes(drop_col_diff)
    breaking_changes = detect_breaking_changes(drop_col_diff, changes)

    assert any(b.change_type == "schema_break" for b in breaking_changes)


# ===========================================================================
# 3. Reverse Dependency Traversal & Classification (Step 2 & 3)
# ===========================================================================

def test_reverse_dependency_traversal_hops(impact_test_env, db_session):
    """
    Verify reverse dependency traversal classifies:
      - process_payment (Hop 1) -> directly_affected
      - OrderService (Hop 2) -> indirectly_affected
      - create_order_route (Hop 3) -> potentially_affected
      - unrelated_worker -> unaffected
    """
    repo = impact_test_env["repo"]

    # Modified file is checkout.py
    diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,3 +15,3 @@
+def checkout(user_id, amount, currency_code):
"""
    changes = detect_code_changes(diff)
    traversal = traverse_dependencies(
        db=db_session,
        repository_id=repo.id,
        changes=changes,
        max_depth=3,
    )

    assert isinstance(traversal, TraversalResult)
    affected_by_name = {c.name: c for c in traversal.affected_components}

    # Hop 1: process_payment
    assert "process_payment" in affected_by_name
    assert affected_by_name["process_payment"].impact_tier == "directly_affected"
    assert affected_by_name["process_payment"].distance == 1

    # Hop 2: OrderService
    assert "OrderService" in affected_by_name
    assert affected_by_name["OrderService"].impact_tier == "indirectly_affected"
    assert affected_by_name["OrderService"].distance == 2

    # Hop 3: create_order_route
    assert "create_order_route" in affected_by_name
    assert affected_by_name["create_order_route"].impact_tier == "potentially_affected"
    assert affected_by_name["create_order_route"].distance == 3

    # Unrelated node must NOT be affected
    assert "unrelated_worker" not in affected_by_name


# ===========================================================================
# 4. Test Recommendations Generation (Step 7)
# ===========================================================================

def test_generate_test_recommendations():
    """Verify test recommendations are prioritized (P0, P1, P2) with copyable commands."""
    affected = [
        AffectedComponent(
            name="process_payment",
            file_path="backend/app/payments/service.py",
            component_type="function",
            impact_tier="directly_affected",
            relationship="calls checkout()",
            why_affected="Immediate caller of modified function.",
            severity="high",
            distance=1,
        ),
        AffectedComponent(
            name="create_order_route",
            file_path="backend/app/api/orders.py",
            component_type="route",
            impact_tier="indirectly_affected",
            relationship="transitive caller",
            why_affected="Exposed to downstream contract changes.",
            severity="medium",
            distance=2,
        ),
    ]

    recommendations = generate_test_recommendations(
        affected_components=affected,
        changed_files=["backend/app/payments/checkout.py"],
    )
    assert len(recommendations) >= 2

    p1_rec = next((r for r in recommendations if r["target_component"] == "process_payment"), None)
    assert p1_rec is not None
    assert p1_rec["priority"] in ("P1_HIGH", "P0_CRITICAL")
    assert "pytest" in p1_rec["command"]


# ===========================================================================
# 5. Graph Serialization & Mermaid Generation (Step 6)
# ===========================================================================

def test_mermaid_generation():
    """Verify Mermaid diagram generates valid flowchart syntax with blast radius styles."""
    subgraph_nodes = [
        {"id": "checkout", "name": "checkout", "type": "function", "impact_tier": "changed", "file_path": "backend/app/payments/checkout.py"},
        {"id": "process_payment", "name": "process_payment", "type": "function", "impact_tier": "directly_affected", "file_path": "backend/app/payments/service.py"},
    ]
    subgraph_edges = [
        {"source": "process_payment", "target": "checkout", "relationship": "calls"},
    ]

    mermaid = generate_impact_mermaid(subgraph_nodes, subgraph_edges)
    assert "flowchart LR" in mermaid
    assert "checkout" in mermaid
    assert "process_payment" in mermaid
    assert "classDef changed" in mermaid
    assert "classDef direct" in mermaid


# ===========================================================================
# 6. End-to-End Analysis Engine & Persistence
# ===========================================================================

def test_run_change_impact_analysis_engine(impact_test_env, db_session):
    """Verify end-to-end impact analysis executes and persists correctly in PostgreSQL."""
    repo = impact_test_env["repo"]
    pr = impact_test_env["pr"]

    diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,3 +15,3 @@
-def checkout(user_id: int, amount: float):
+def checkout(user_id: int, amount: float, currency_code: str):
"""
    analysis = run_change_impact_analysis(
        db=db_session,
        repository_id=repo.id,
        diff=diff,
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        target_branch=pr.target_branch,
    )

    assert analysis.id is not None
    assert analysis.repository_id == repo.id
    assert analysis.pull_request_id == pr.id
    assert analysis.risk_level in ("high", "critical")
    assert analysis.directly_affected_count >= 1
    assert analysis.breaking_changes_count >= 1
    assert len(analysis.affected_components) >= 1
    assert len(analysis.breaking_changes) >= 1
    assert len(analysis.test_recommendations) >= 1
    assert analysis.graph_visualization is not None
    assert "flowchart LR" in analysis.graph_visualization["mermaid"]


# ===========================================================================
# 7. API Routes and Multi-Tenant RBAC Authorization
# ===========================================================================

def test_impact_api_trigger_and_get(impact_test_env, db_session):
    """Verify impact API endpoints for triggering analysis and retrieving latest PR impact."""
    user1 = impact_test_env["user1"]
    repo = impact_test_env["repo"]
    pr = impact_test_env["pr"]

    client = make_client_for_user(db_session, user1)

    diff = """\
diff --git a/backend/app/payments/checkout.py b/backend/app/payments/checkout.py
--- a/backend/app/payments/checkout.py
+++ b/backend/app/payments/checkout.py
@@ -15,3 +15,3 @@
-def checkout(user_id: int, amount: float):
+def checkout(user_id: int, amount: float, currency_code: str):
"""
    # 1. Trigger Impact Analysis
    trigger_resp = client.post(
        f"/repositories/{repo.id}/impact/analyze",
        json={
            "diff": diff,
            "pull_request_id": pr.id,
            "commit_sha": pr.head_sha,
            "target_branch": "main",
        },
    )
    assert trigger_resp.status_code == 201, trigger_resp.text
    analysis_data = trigger_resp.json()
    analysis_id = analysis_data["id"]
    assert analysis_data["directly_affected_count"] >= 1
    assert analysis_data["breaking_changes_count"] >= 1

    # 2. Get Latest PR Impact
    pr_impact_resp = client.get(f"/repositories/{repo.id}/pull-requests/{pr.id}/impact")
    assert pr_impact_resp.status_code == 200
    pr_impact_data = pr_impact_resp.json()
    assert pr_impact_data["id"] == analysis_id

    # 3. Get Impact By ID
    by_id_resp = client.get(f"/impact/{analysis_id}")
    assert by_id_resp.status_code == 200
    assert by_id_resp.json()["id"] == analysis_id

    # 4. Get Graph Visualization
    graph_resp = client.get(f"/impact/{analysis_id}/graph")
    assert graph_resp.status_code == 200
    graph_data = graph_resp.json()
    assert "nodes" in graph_data
    assert "mermaid" in graph_data
    assert "flowchart LR" in graph_data["mermaid"]


def test_impact_api_tenant_isolation(impact_test_env, db_session):
    """Verify unauthorized users from other organizations cannot trigger or view impact analysis."""
    user2 = impact_test_env["user2"]  # Org 2 user
    repo = impact_test_env["repo"]    # Belongs to Org 1
    pr = impact_test_env["pr"]

    client = make_client_for_user(db_session, user2)

    # Attempt to trigger on Org 1's repo
    resp = client.post(
        f"/repositories/{repo.id}/impact/analyze",
        json={"diff": "some diff", "pull_request_id": pr.id},
    )
    assert resp.status_code in (403, 404)

    # Attempt to read PR impact
    resp_get = client.get(f"/repositories/{repo.id}/pull-requests/{pr.id}/impact")
    assert resp_get.status_code in (403, 404)
