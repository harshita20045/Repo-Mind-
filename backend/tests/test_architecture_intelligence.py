"""
RepoMind 2.0 Architecture Intelligence Engine Test Suite.

Verifies:
  1. Architecture pattern inference (Layered MVC, Clean/Hexagonal, Modular Monolith, Fullstack)
  2. Layer and module classification (Presentation, Business Logic, Domain, Data Access, Infra, Utility)
  3. Circular dependency detection (Direct A<->B, Transitive A->B->C->A, Acyclic graphs)
  4. Forbidden dependency & layer boundary enforcement (ARCH-001, ARCH-002, ARCH-003, disabled rules)
  5. API-to-Service-to-Database flow analysis (Clean flows vs. Leaky controller bypasses)
  6. Architecture health score & Mermaid layer topology generation
  7. End-to-end engine orchestrator & database persistence
  8. Rule governance CRUD, reset-to-defaults, and multi-tenant RBAC isolation
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
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.architecture.models import (
    ArchitectureRule,
    ArchitectureAnalysis,
    ArchitectureViolation,
)
from backend.app.architecture.patterns import (
    infer_architecture_pattern,
    detect_architecture_pattern,
    InferredPatternResult,
    DEFAULT_BASELINE_RULES,
)
from backend.app.architecture.layers import classify_layer, get_layer_rank
from backend.app.architecture.circular import (
    detect_circular_dependencies,
    CircularDependency,
)
from backend.app.architecture.flows import (
    trace_architecture_flows,
    FlowAnalysisResult,
    FlowChain,
)
from backend.app.architecture.checker import (
    check_architecture_rules,
    GroundedViolation,
    _matches_pattern,
)
from backend.app.architecture.engine import (
    run_architecture_analysis,
    ensure_baseline_architecture_rules,
    generate_architecture_mermaid,
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
def arch_test_env(db_session):
    """Seed test tenants, projects, repositories, users, and code graph."""
    assert db_session.execute(text("SELECT current_database()")).scalar() == "repomind_test"

    org1 = Organization(name="Arch Test Org 1")
    org2 = Organization(name="Arch Test Org 2")
    db_session.add_all([org1, org2])
    db_session.commit()

    admin_user = User(email="arch_admin@example.com", password_hash="hashed_pw")
    dev_user = User(email="arch_dev@example.com", password_hash="hashed_pw")
    other_user = User(email="arch_other@example.com", password_hash="hashed_pw")
    db_session.add_all([admin_user, dev_user, other_user])
    db_session.commit()

    mem1 = OrganizationMembership(user_id=admin_user.id, organization_id=org1.id, role=RoleEnum.ORG_ADMIN)
    mem2 = OrganizationMembership(user_id=dev_user.id, organization_id=org1.id, role=RoleEnum.DEVELOPER)
    mem3 = OrganizationMembership(user_id=other_user.id, organization_id=org2.id, role=RoleEnum.ORG_ADMIN)
    db_session.add_all([mem1, mem2, mem3])
    db_session.commit()

    project1 = Project(organization_id=org1.id, name="Arch Test Project")
    db_session.add(project1)
    db_session.commit()

    repo = Repository(
        project_id=project1.id,
        github_owner="repomind-ai",
        github_name="arch-test-repo",
        github_repository_id="998877",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()

    # Seed Code Graph Nodes (Layered Architecture with intentional violations)
    node_route = CodeGraphNode(
        repository_id=repo.id,
        node_key=f"{repo.id}:backend/app/api/orders.py:route",
        file_path="backend/app/api/orders.py",
        name="get_orders_endpoint",
        node_type="route",
        start_line=15,
        end_line=30,
        metadata_json={"method": "GET", "path": "/orders"},
    )
    node_service = CodeGraphNode(
        repository_id=repo.id,
        node_key=f"{repo.id}:backend/app/orders/service.py:service",
        file_path="backend/app/orders/service.py",
        name="OrderService",
        node_type="class",
        start_line=10,
        end_line=50,
        metadata_json={},
    )
    node_model = CodeGraphNode(
        repository_id=repo.id,
        node_key=f"{repo.id}:backend/app/models/order.py:model",
        file_path="backend/app/models/order.py",
        name="Order",
        node_type="model",
        start_line=5,
        end_line=40,
        metadata_json={},
    )
    node_ui = CodeGraphNode(
        repository_id=repo.id,
        node_key=f"{repo.id}:frontend/src/components/OrderView.jsx:component",
        file_path="frontend/src/components/OrderView.jsx",
        name="OrderView",
        node_type="component",
        start_line=1,
        end_line=60,
        metadata_json={},
    )
    db_session.add_all([node_route, node_service, node_model, node_ui])
    db_session.commit()

    # Edge 1: Clean route -> service call
    edge1 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_route.id,
        target_node_id=node_service.id,
        relation_type="calls",
        metadata_json={"line": 20, "caller_file": node_route.file_path, "callee_file": node_service.file_path, "caller_name": "get_orders_endpoint", "callee_name": "OrderService"},
    )
    # Edge 2: Service -> model interaction
    edge2 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_service.id,
        target_node_id=node_model.id,
        relation_type="interacts_with",
        metadata_json={"line": 35, "model_name": "Order", "file_path": node_service.file_path},
    )
    # Edge 3 (VIOLATION ARCH-001): Direct Route -> Model import bypassing service!
    edge3 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_route.id,
        target_node_id=node_model.id,
        relation_type="imports",
        metadata_json={
            "source_file": node_route.file_path,
            "target_file": node_model.file_path,
            "line": 4,
            "imported_names": ["Order"],
            "raw_statement": "from backend.app.models.order import Order",
        },
    )
    # Edge 4 & 5 (CIRCULAR VIOLATION): Mutual import between service and model
    edge4 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_service.id,
        target_node_id=node_model.id,
        relation_type="imports",
        metadata_json={"source_file": node_service.file_path, "target_file": node_model.file_path, "line": 2},
    )
    edge5 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_model.id,
        target_node_id=node_service.id,
        relation_type="imports",
        metadata_json={"source_file": node_model.file_path, "target_file": node_service.file_path, "line": 3},
    )

    db_session.add_all([edge1, edge2, edge3, edge4, edge5])
    db_session.commit()

    return {
        "org1": org1,
        "org2": org2,
        "admin_user": admin_user,
        "dev_user": dev_user,
        "other_user": other_user,
        "project": project1,
        "repo": repo,
        "node_route": node_route,
        "node_service": node_service,
        "node_model": node_model,
        "node_ui": node_ui,
    }


# =====================================================================
# 1. Pattern Inference Engine Tests
# =====================================================================

def test_pattern_inference_layered_mvc():
    file_paths = [
        "backend/app/api/routes.py",
        "backend/app/controllers/user_controller.py",
        "backend/app/services/user_service.py",
        "backend/app/models/user.py",
        "backend/app/schemas/user.py",
    ]
    res = infer_architecture_pattern(file_paths, frameworks=["fastapi"])
    assert res.pattern in ("layered_mvc", "fullstack_monorepo")
    assert res.confidence > 0.5
    assert len(res.suggested_rules) >= 4
    rule_codes = [r["rule_code"] for r in res.suggested_rules]
    assert "ARCH-001" in rule_codes
    assert "ARCH-002" in rule_codes


def test_pattern_inference_clean_hexagonal():
    file_paths = [
        "src/domain/entities/order.py",
        "src/domain/events/order_created.py",
        "src/usecases/create_order.py",
        "src/adapters/database/order_repository.py",
        "src/infrastructure/stripe_client.py",
    ]
    res = infer_architecture_pattern(file_paths, frameworks=["fastapi"])
    assert res.pattern == "clean_hexagonal"
    assert res.confidence > 0.6
    assert any("domain/entities" in e.lower() for e in res.evidence)


def test_pattern_inference_modular_monolith():
    file_paths = [
        "backend/app/auth/routes.py",
        "backend/app/auth/services.py",
        "backend/app/billing/routes.py",
        "backend/app/billing/models.py",
        "backend/app/inventory/routes.py",
        "backend/app/inventory/services.py",
        "backend/app/notifications/worker.py",
    ]
    res = infer_architecture_pattern(file_paths)
    assert res.pattern == "modular_monolith"
    assert res.confidence > 0.5


# =====================================================================
# 2. Layer & Module Classifier Tests
# =====================================================================

def test_layer_classification():
    assert classify_layer("backend/app/api/orders.py") == "presentation"
    assert classify_layer("backend/app/controllers/checkout.ts") == "presentation"
    assert classify_layer("backend/app/services/payment.py") == "business_logic"
    assert classify_layer("backend/app/usecases/place_order.py") == "business_logic"
    assert classify_layer("src/domain/entities/user.py") == "domain"
    assert classify_layer("backend/app/models/order.py") == "data_access"
    assert classify_layer("backend/app/repositories/order_repo.py") == "data_access"
    assert classify_layer("backend/app/infrastructure/email_client.py") == "infrastructure"
    assert classify_layer("backend/app/utils/crypto.py") == "shared_utility"
    assert classify_layer("frontend/src/components/Header.jsx") == "frontend_ui"
    assert classify_layer("backend/app/workers/cleanup.py") == "worker"
    assert classify_layer("backend/tests/test_architecture.py") == "test"
    assert classify_layer("some/unknown/file.txt") == "unknown"


def test_layer_ranks():
    assert get_layer_rank("presentation") > get_layer_rank("business_logic")
    assert get_layer_rank("business_logic") > get_layer_rank("domain")
    assert get_layer_rank("domain") > get_layer_rank("data_access")
    assert get_layer_rank("shared_utility") < get_layer_rank("data_access")


# =====================================================================
# 3. Circular Dependency Detector Tests
# =====================================================================

def test_circular_dependency_direct_cycle():
    edges = [
        ("backend/app/auth.py", "backend/app/user.py"),
        ("backend/app/user.py", "backend/app/auth.py"),
    ]
    cycles = detect_circular_dependencies(edges)
    assert len(cycles) == 1
    c = cycles[0]
    assert c.length == 2
    assert c.severity == "critical"
    assert "Direct circular dependency" in c.title
    assert "mutually import" in c.decoupling_recommendation


def test_circular_dependency_transitive_cycle():
    edges = [
        ("pkg/a.py", "pkg/b.py"),
        ("pkg/b.py", "pkg/c.py"),
        ("pkg/c.py", "pkg/a.py"),
    ]
    cycles = detect_circular_dependencies(edges)
    assert len(cycles) == 1
    c = cycles[0]
    assert c.length == 3
    assert c.severity == "high"
    assert c.cycle_path[0] == c.cycle_path[-1]  # Closed loop


def test_circular_dependency_acyclic_graph():
    edges = [
        ("pkg/controller.py", "pkg/service.py"),
        ("pkg/service.py", "pkg/model.py"),
        ("pkg/controller.py", "pkg/model.py"),
    ]
    cycles = detect_circular_dependencies(edges)
    assert len(cycles) == 0


# =====================================================================
# 4. Architecture Rule Compliance & Violation Grounding Tests
# =====================================================================

def test_rule_checking_forbidden_dependency():
    rules = [
        {
            "id": 1,
            "rule_code": "ARCH-001",
            "rule_type": "api_db_isolation",
            "source_layer": "presentation",
            "target_layer": "data_access",
            "severity": "critical",
            "name": "Controllers must not access DB models",
            "suggested_fix": "Delegate through service",
            "is_enabled": True,
        },
        {
            "id": 2,
            "rule_code": "ARCH-002",
            "rule_type": "forbidden_dependency",
            "source_layer": "frontend_ui",
            "target_layer": "backend",
            "severity": "critical",
            "name": "Frontend must not import backend",
            "suggested_fix": "Call REST API",
            "is_enabled": True,
        },
    ]

    import_records = [
        # Violation 1: Route imports DB Model
        {
            "source_file": "backend/app/api/orders.py",
            "target_file": "backend/app/models/order.py",
            "line": 4,
            "raw_statement": "from backend.app.models.order import Order",
        },
        # Violation 2: Frontend imports backend secret/config
        {
            "source_file": "frontend/src/components/Payment.jsx",
            "target_file": "backend/app/config.py",
            "line": 2,
            "raw_statement": "import { STRIPE_KEY } from '../../backend/app/config'",
        },
        # Clean import: Controller imports Service
        {
            "source_file": "backend/app/api/orders.py",
            "target_file": "backend/app/services/order_service.py",
            "line": 1,
            "raw_statement": "from backend.app.services.order_service import OrderService",
        },
    ]

    flow_res = FlowAnalysisResult(total_flows=0)
    violations = check_architecture_rules(rules, import_records, [], flow_res)

    assert len(violations) == 2
    rule_codes = {v.rule_code for v in violations}
    assert "ARCH-001" in rule_codes
    assert "ARCH-002" in rule_codes

    v1 = next(v for v in violations if v.rule_code == "ARCH-001")
    assert v1.source_file == "backend/app/api/orders.py"
    assert v1.source_line == 4
    assert v1.target_file == "backend/app/models/order.py"
    assert "Order" in (v1.evidence or "")
    assert v1.severity == "critical"


def test_rule_disabled_suppression():
    rules = [
        {
            "id": 1,
            "rule_code": "ARCH-001",
            "rule_type": "api_db_isolation",
            "source_layer": "presentation",
            "target_layer": "data_access",
            "severity": "critical",
            "name": "Controllers must not access DB models",
            "is_enabled": False,  # DISABLED!
        }
    ]

    import_records = [
        {
            "source_file": "backend/app/api/orders.py",
            "target_file": "backend/app/models/order.py",
            "line": 4,
            "raw_statement": "from backend.app.models.order import Order",
        }
    ]

    violations = check_architecture_rules(rules, import_records, [], FlowAnalysisResult(total_flows=0))
    # Disabled rule must produce zero violations
    assert len(violations) == 0


# =====================================================================
# 5. Flow Analysis Tracer Tests
# =====================================================================

def test_flow_tracing_clean_vs_leaky():
    api_routes = [
        {"endpoint_name": "GET /orders", "path": "/orders", "method": "GET", "file_path": "backend/app/api/orders.py"},
        {"endpoint_name": "POST /checkout", "path": "/checkout", "method": "POST", "file_path": "backend/app/api/checkout.py"},
    ]
    service_files = ["backend/app/orders/service.py"]
    db_model_files = ["backend/app/models/order.py"]

    call_edges = [
        {
            "caller_file": "backend/app/api/orders.py",
            "caller_name": "get_orders",
            "callee_file": "backend/app/orders/service.py",
            "callee_name": "OrderService",
            "line": 15,
        }
    ]

    db_interactions = [
        # Service interacts with DB model (clean)
        {"file_path": "backend/app/orders/service.py", "model_name": "Order", "operation": "query", "line": 30},
        # Checkout route directly queries Order model (leaky)
        {"file_path": "backend/app/api/checkout.py", "model_name": "Order", "operation": "insert", "line": 22},
    ]

    res = trace_architecture_flows(api_routes, service_files, db_model_files, call_edges, db_interactions)
    assert res.total_flows == 2
    assert len(res.clean_flows) == 1
    assert len(res.leaky_flows) == 1

    clean = res.clean_flows[0]
    assert clean.endpoint_name == "GET /orders"
    assert clean.service_file == "backend/app/orders/service.py"
    assert clean.is_leaky is False

    leaky = res.leaky_flows[0]
    assert leaky.endpoint_name == "POST /checkout"
    assert leaky.is_leaky is True
    assert leaky.model_name == "Order"
    assert "directly executes DB" in leaky.evidence


# =====================================================================
# 6. End-to-End Orchestrator & Persistence Tests
# =====================================================================

def test_engine_run_architecture_analysis(db_session, arch_test_env):
    repo = arch_test_env["repo"]

    # Run complete architecture audit
    analysis = run_architecture_analysis(db_session, repo.id)
    assert analysis is not None
    assert analysis.repository_id == repo.id
    assert analysis.inferred_pattern in ("layered_mvc", "fullstack_monorepo", "modular_monolith")
    assert 0 <= analysis.health_score <= 100
    assert analysis.mermaid_diagram.startswith("flowchart TD")

    # Baseline rules must have been seeded
    rules = db_session.query(ArchitectureRule).filter(ArchitectureRule.repository_id == repo.id).all()
    assert len(rules) >= 4

    # Check violations persisted in DB
    violations = db_session.query(ArchitectureViolation).filter(ArchitectureViolation.analysis_id == analysis.id).all()
    assert len(violations) > 0
    # Direct route -> model access violation should be recorded
    v_codes = [v.rule_code for v in violations]
    assert any("ARCH" in code or "CIRC" in code for code in v_codes)

    # Re-running analysis overwrites or produces fresh analysis
    second_analysis = run_architecture_analysis(db_session, repo.id)
    assert second_analysis.id != analysis.id
    assert second_analysis.repository_id == repo.id


# =====================================================================
# 7. REST API & Multi-Tenant Authorization Tests
# =====================================================================

def test_api_get_latest_analysis(db_session, arch_test_env):
    repo = arch_test_env["repo"]
    admin = arch_test_env["admin_user"]
    other = arch_test_env["other_user"]

    # Trigger analysis first
    run_architecture_analysis(db_session, repo.id)

    # 1. Authorized member access
    client_admin = make_client_for_user(db_session, admin)
    res = client_admin.get(f"/repositories/{repo.id}/architecture/analysis")
    assert res.status_code == 200
    data = res.json()
    assert data["repository_id"] == repo.id
    assert "health_score" in data
    assert "violations" in data
    assert isinstance(data["violations"], list)
    cleanup_overrides()

    # 2. Unauthorized cross-tenant user access (403 Forbidden or 404 Not Found to prevent tenant enumeration)
    client_other = make_client_for_user(db_session, other)
    res_other = client_other.get(f"/repositories/{repo.id}/architecture/analysis")
    assert res_other.status_code in (403, 404)
    cleanup_overrides()


def test_api_trigger_analysis_post(db_session, arch_test_env):
    repo = arch_test_env["repo"]
    admin = arch_test_env["admin_user"]

    client = make_client_for_user(db_session, admin)
    res = client.post(f"/repositories/{repo.id}/architecture/analyze")
    assert res.status_code in (200, 201)
    data = res.json()
    assert data["repository_id"] == repo.id
    assert data["health_score"] >= 0
    cleanup_overrides()


def test_api_rule_governance_lifecycle(db_session, arch_test_env):
    repo = arch_test_env["repo"]
    admin = arch_test_env["admin_user"]
    dev = arch_test_env["dev_user"]

    # 1. Admin creates custom rule
    client_admin = make_client_for_user(db_session, admin)
    payload = {
        "rule_code": "CUSTOM-001",
        "name": "Strict Service Encapsulation",
        "description": "Custom rule testing",
        "rule_type": "forbidden_dependency",
        "source_layer": "shared_utility",
        "target_layer": "business_logic",
        "severity": "high",
        "suggested_fix": "Extract shared types",
        "is_enabled": True,
    }
    res_create = client_admin.post(f"/repositories/{repo.id}/architecture/rules", json=payload)
    assert res_create.status_code == 201
    created_rule = res_create.json()
    rule_id = created_rule["id"]
    assert created_rule["rule_code"] == "CUSTOM-001"
    assert created_rule["is_system_inferred"] is False

    # 2. Non-admin (Developer role) cannot create rules (403 Forbidden)
    client_dev = make_client_for_user(db_session, dev)
    res_dev = client_dev.post(f"/repositories/{repo.id}/architecture/rules", json=payload)
    assert res_dev.status_code == 403

    # Switch back to admin client
    client_admin = make_client_for_user(db_session, admin)

    # 3. Admin toggles/updates rule
    res_patch = client_admin.patch(
        f"/repositories/{repo.id}/architecture/rules/{rule_id}",
        json={"is_enabled": False, "severity": "medium"},
    )
    assert res_patch.status_code == 200
    assert res_patch.json()["is_enabled"] is False
    assert res_patch.json()["severity"] == "medium"

    # 4. Admin deletes custom rule
    res_del = client_admin.delete(f"/repositories/{repo.id}/architecture/rules/{rule_id}")
    assert res_del.status_code in (200, 204)

    # 5. Reset rules to pattern defaults
    res_reset = client_admin.post(f"/repositories/{repo.id}/architecture/rules/reset-defaults")
    assert res_reset.status_code == 200
    reset_rules = res_reset.json()
    assert len(reset_rules) >= 4
    assert any(r["rule_code"] == "ARCH-001" for r in reset_rules)

    cleanup_overrides()


def test_api_circular_dependencies_endpoint(db_session, arch_test_env):
    repo = arch_test_env["repo"]
    admin = arch_test_env["admin_user"]

    client = make_client_for_user(db_session, admin)
    res = client.get(f"/repositories/{repo.id}/architecture/circular")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Edge 4 and 5 form a direct cycle between service and model
    assert len(data) >= 1
    assert data[0]["length"] == 2
    cleanup_overrides()


def test_api_flows_endpoint(db_session, arch_test_env):
    repo = arch_test_env["repo"]
    admin = arch_test_env["admin_user"]

    client = make_client_for_user(db_session, admin)
    res = client.get(f"/repositories/{repo.id}/architecture/flows")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    cleanup_overrides()
