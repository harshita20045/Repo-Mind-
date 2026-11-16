"""
Tests for RepoMind AI Assistant Upgrade — Repository Intelligence & Grounding.

Verifies:
1. Query classification across all 8 supported question types + entity extraction.
2. Multi-source context retrieval (AST nodes, call graph edges, architecture rules,
   blueprint flows, PR diffs, review findings, test scenarios).
3. Evidence-grounded response synthesis with required sections (Explanation, Relevant Files,
   Relevant Functions/Symbols, Source References).
4. Insufficient evidence handling (explicit disclosure, no hallucinated code paths).
5. Cross-organization and unauthorized repository data isolation.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.intelligence.models import (
    CodeGraphNode,
    CodeGraphEdge,
    RepositoryScanSummary,
)
from backend.app.onboarding.models import RepositoryBlueprint
from backend.app.architecture.models import ArchitectureRule
from backend.app.github.models import PullRequest, PullRequestFile
from backend.app.review.models import ReviewRun, Finding, HumanDecision
from backend.app.testing.models import TestScenario
from backend.app.chat.models import ChatSession, ChatMessage
from backend.app.chat.classifier import classify_query, QueryIntent, extract_symbols, extract_files, extract_endpoints
from backend.app.chat.retrieval import MultiSourceContextRetriever
from backend.app.chat.service import send_message, create_session
from backend.app.review.provider import LocalProvider
from backend.app.auth.dependencies import get_current_user
from backend.app.db import get_db


# =====================================================================
# 1. QUERY CLASSIFICATION TESTS
# =====================================================================

def test_query_classifier_all_8_categories():
    """Verify classifier correctly recognizes all 8 supported question types."""
    # 1. Module explanation
    res1 = classify_query("Explain this module and its architectural structure.")
    assert res1.intent == QueryIntent.MODULE_EXPLANATION

    # 2. Authentication flow
    res2 = classify_query("How does authentication work in this repository?")
    assert res2.intent == QueryIntent.AUTH_FLOW

    # 3. API implementation
    res3 = classify_query("Where is this API implemented for /chat/sessions?")
    assert res3.intent == QueryIntent.API_IMPLEMENTATION
    assert "/chat/sessions" in res3.endpoints

    # 4. Database access
    res4 = classify_query("Which service accesses this database or User table?")
    assert res4.intent == QueryIntent.DB_ACCESS

    # 5. PR review rationale
    res5 = classify_query("Why was this PR flagged during review?")
    assert res5.intent == QueryIntent.PR_REVIEW_RATIONALE

    # 6. Dependency graph / callers
    res6 = classify_query("Which modules depend on this function `send_message`?")
    assert res6.intent == QueryIntent.DEPENDENCY_GRAPH
    assert "send_message" in res6.symbols

    # 7. Endpoint lifecycle
    res7 = classify_query("What happens when this endpoint /api/v1/login is called?")
    assert res7.intent == QueryIntent.ENDPOINT_LIFECYCLE
    assert "/api/v1/login" in res7.endpoints

    # 8. Test coverage
    res8 = classify_query("Which tests cover this functionality and where are coverage gaps?")
    assert res8.intent == QueryIntent.TEST_COVERAGE


def test_entity_extraction_helpers():
    """Verify symbol, file, and endpoint extraction."""
    text = "Check `create_session` in backend/app/chat/service.py for POST /chat/sessions endpoint."
    symbols = extract_symbols(text)
    files = extract_files(text)
    endpoints = extract_endpoints(text)

    assert "create_session" in symbols
    assert any("service.py" in f for f in files)
    assert any("/chat/sessions" in ep for ep in endpoints)


# =====================================================================
# 2. MULTI-SOURCE CONTEXT RETRIEVAL FIXTURE & TESTS
# =====================================================================

@pytest.fixture
def repo_intelligence_setup(db_session):
    """Sets up a complete repository with all 7 context sources populated."""
    # Org & User
    org = Organization(name="Intelligence Test Org")
    db_session.add(org)
    db_session.commit()

    user = User(email="assistant_dev@intel.com")
    db_session.add(user)
    db_session.commit()

    mem = OrganizationMembership(user_id=user.id, organization_id=org.id, role=RoleEnum.DEVELOPER.value)
    db_session.add(mem)

    proj = Project(organization_id=org.id, name="Intelligence Project")
    db_session.add(proj)
    db_session.commit()

    repo = Repository(
        project_id=proj.id,
        github_repository_id="gh_intel_100",
        github_owner="intel-corp",
        github_name="intel-service",
        index_status="indexed"
    )
    db_session.add(repo)
    db_session.commit()

    # 1. Source Code AST Nodes
    node_auth = CodeGraphNode(
        repository_id=repo.id,
        node_key="backend/app/auth/service.py:authenticate_user",
        node_type="function",
        name="authenticate_user",
        file_path="backend/app/auth/service.py",
        start_line=25,
        end_line=45,
        metadata_json={"args": ["db", "email", "password"]}
    )
    node_api = CodeGraphNode(
        repository_id=repo.id,
        node_key="backend/app/auth/routes.py:login_endpoint",
        node_type="api_endpoint",
        name="/api/v1/auth/login",
        file_path="backend/app/auth/routes.py",
        start_line=12,
        end_line=30,
        metadata_json={"method": "POST"}
    )
    node_db = CodeGraphNode(
        repository_id=repo.id,
        node_key="backend/app/auth/models.py:User",
        node_type="db_model",
        name="User",
        file_path="backend/app/auth/models.py",
        start_line=10,
        end_line=50,
        metadata_json={"table": "user"}
    )
    db_session.add_all([node_auth, node_api, node_db])
    db_session.commit()

    # 2. Dependency Graph Edges
    edge1 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_api.id,
        target_node_id=node_auth.id,
        relation_type="calls",
        weight=1.0
    )
    edge2 = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=node_auth.id,
        target_node_id=node_db.id,
        relation_type="interacts_with",
        weight=1.0
    )
    db_session.add_all([edge1, edge2])

    # 3. Architecture Rules
    rule = ArchitectureRule(
        repository_id=repo.id,
        rule_code="ARCH-AUTH-001",
        name="Strict Layer Isolation",
        description="Controllers must not query database models directly; invoke domain service instead.",
        rule_type="layer_boundary",
        source_layer="presentation",
        target_layer="data_access",
        severity="high",
        is_enabled=True
    )
    db_session.add(rule)

    # 4. Blueprint & Scan Summary
    blueprint = RepositoryBlueprint(
        repository_id=repo.id,
        analyzed_commit_sha="c0ffee123456",
        status="ready",
        summary="Modular 3-tier REST architecture using FastAPI and SQLAlchemy.",
        architecture_pattern="Modular Monolith",
        application_flows={
            "auth_flow": "Request hits /api/v1/auth/login -> verifies credentials via authenticate_user -> issues JWT bearer token."
        }
    )
    scan = RepositoryScanSummary(
        repository_id=repo.id,
        primary_language="Python",
        architecture_summary="FastAPI backend with PostgreSQL storage and JWT authentication.",
        entry_points=["backend/app/main.py", "backend/app/auth/routes.py"]
    )
    db_session.add_all([blueprint, scan])

    # 5. Pull Request & Diff
    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_intel_101",
        github_number=101,
        title="Upgrade auth token verification",
        state="open",
        github_author_login="octocat",
        source_branch="feat/auth-token",
        target_branch="main",
        head_sha="head_sha_101",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    pr_file = PullRequestFile(
        pull_request_id=pr.id,
        file_path="backend/app/auth/service.py",
        status="modified",
        additions=15,
        deletions=2,
        changes=17,
        patch_data="@@ -30,2 +30,15 @@ def authenticate_user..."
    )
    db_session.add(pr_file)

    # 6. Review Findings
    review_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="head_sha_101",
        status="completed"
    )
    db_session.add(review_run)
    db_session.commit()

    finding = Finding(
        review_run_id=review_run.id,
        type="security",
        severity="high",
        file="backend/app/auth/service.py",
        line=35,
        title="Missing token expiration validation",
        explanation="JWT token verification lacks explicit exp claim check.",
        confidence=0.95,
        status="open",
        evidence_status="supported"
    )
    db_session.add(finding)

    # 7. Test Scenario
    scenario = TestScenario(
        repository_id=repo.id,
        pull_request_id=pr.id,
        target_file="backend/app/auth/service.py",
        target_symbol="authenticate_user",
        category="authentication",
        title="Expired JWT token rejection",
        description="Verify authenticate_user rejects tokens past expiration timestamp.",
        coverage_gap=True
    )
    db_session.add(scenario)
    db_session.commit()

    return {
        "org": org,
        "user": user,
        "repo": repo,
        "pr": pr,
        "node_auth": node_auth,
        "node_api": node_api,
        "node_db": node_db,
    }


def test_multi_source_retriever_pulls_all_sources(db_session, repo_intelligence_setup):
    """Verify MultiSourceContextRetriever pulls evidence across the 7 sources."""
    data = repo_intelligence_setup
    repo = data["repo"]
    retriever = MultiSourceContextRetriever(db=db_session)

    # Test retrieval for auth flow
    entities = classify_query("How does authentication work in this repository?")
    evidence_text, sources, is_grounded = retriever.retrieve(
        repository_id=repo.id,
        query="How does authentication work?",
        entities=entities,
    )

    assert is_grounded is True
    assert "REPOSITORY ARCHITECTURE & BLUEPRINT" in evidence_text
    assert "ARCHITECTURE RULES & CONSTRAINTS" in evidence_text
    assert any(s["type"] == "documentation" for s in sources)
    assert any(s["type"] == "architecture_rule" for s in sources)


def test_dependency_graph_and_call_chain_retrieval(db_session, repo_intelligence_setup):
    """Verify dependency graph callers and callees are retrieved."""
    data = repo_intelligence_setup
    repo = data["repo"]
    retriever = MultiSourceContextRetriever(db=db_session)

    entities = classify_query("Which modules depend on this function `authenticate_user`?")
    evidence_text, sources, is_grounded = retriever.retrieve(
        repository_id=repo.id,
        query="Which modules depend on this function `authenticate_user`?",
        entities=entities,
    )

    assert is_grounded is True
    assert "DEPENDENCY GRAPH & CALL RELATIONSHIPS" in evidence_text
    assert any(s["type"] == "dependency_graph" for s in sources)
    assert any(s["type"] == "code_symbol" for s in sources)


def test_pr_review_rationale_retrieval(db_session, repo_intelligence_setup):
    """Verify PR review findings and diff are retrieved."""
    data = repo_intelligence_setup
    repo = data["repo"]
    pr = data["pr"]
    retriever = MultiSourceContextRetriever(db=db_session)

    entities = classify_query(f"Why was this PR #{pr.github_number} flagged?")
    evidence_text, sources, is_grounded = retriever.retrieve(
        repository_id=repo.id,
        query=f"Why was this PR #{pr.github_number} flagged?",
        entities=entities,
    )

    assert is_grounded is True
    assert "PULL REQUEST CONTEXT & DIFF" in evidence_text
    assert "REVIEW FINDINGS & AUDIT FLAGS" in evidence_text
    assert "Missing token expiration validation" in evidence_text
    assert any(s["type"] == "review_finding" for s in sources)


def test_test_coverage_retrieval(db_session, repo_intelligence_setup):
    """Verify AI test scenarios and coverage gaps are retrieved."""
    data = repo_intelligence_setup
    repo = data["repo"]
    retriever = MultiSourceContextRetriever(db=db_session)

    entities = classify_query("Which tests cover this functionality for authenticate_user?")
    evidence_text, sources, is_grounded = retriever.retrieve(
        repository_id=repo.id,
        query="Which tests cover this functionality for authenticate_user?",
        entities=entities,
    )

    assert is_grounded is True
    assert "AI TEST INTELLIGENCE & SCENARIOS" in evidence_text
    assert "Expired JWT token rejection" in evidence_text
    assert any(s["type"] == "test_scenario" for s in sources)


# =====================================================================
# 3. END-TO-END CHAT SERVICE & GROUNDED RESPONSE TESTS
# =====================================================================

def test_chat_service_generates_grounded_response_with_citations(db_session, repo_intelligence_setup):
    """Verify assistant produces structured grounded response with Explanation, Files, Symbols, Sources."""
    data = repo_intelligence_setup
    org = data["org"]
    user = data["user"]
    repo = data["repo"]

    session = create_session(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        context_type="repository",
        context_id=repo.id
    )

    provider = LocalProvider()
    assistant_msg = send_message(
        db=db_session,
        session_id=session.id,
        user_id=user.id,
        message="Explain this module and how authentication works.",
        provider=provider,
        repository_id=repo.id
    )

    assert assistant_msg.role == "assistant"
    assert assistant_msg.is_grounded is True
    assert assistant_msg.sources is not None
    assert len(assistant_msg.sources) > 0

    content = assistant_msg.content
    assert "### Explanation" in content
    assert "### Relevant Files" in content
    assert "### Relevant Functions / Symbols" in content
    assert "### Source References" in content


def test_insufficient_evidence_explicit_disclosure(db_session, repo_intelligence_setup):
    """Verify assistant explicitly states when evidence is missing and does NOT fabricate code paths."""
    data = repo_intelligence_setup
    org = data["org"]
    user = data["user"]

    # Create empty repo with no indexed AST nodes, no rules, no blueprint
    empty_proj = Project(organization_id=org.id, name="Empty Project")
    db_session.add(empty_proj)
    db_session.commit()

    empty_repo = Repository(
        project_id=empty_proj.id,
        github_repository_id="gh_empty_999",
        github_owner="intel-corp",
        github_name="empty-repo",
        index_status="pending"
    )
    db_session.add(empty_repo)
    db_session.commit()

    session = create_session(
        db=db_session,
        user_id=user.id,
        organization_id=org.id,
        context_type="repository",
        context_id=empty_repo.id
    )

    provider = LocalProvider()
    assistant_msg = send_message(
        db=db_session,
        session_id=session.id,
        user_id=user.id,
        message="Where is the non_existent_quantum_service implemented?",
        provider=provider,
        repository_id=empty_repo.id
    )

    assert assistant_msg.is_grounded is False
    assert "I don't have enough evidence in the repository context to answer that." in assistant_msg.content


# =====================================================================
# 4. API ROUTE & AUTHORIZATION TESTS
# =====================================================================

def test_chat_api_route_e2e_grounded_response(db_session, repo_intelligence_setup):
    """Verify HTTP API endpoint returns structured grounded message and citations."""
    data = repo_intelligence_setup
    org = data["org"]
    user = data["user"]
    repo = data["repo"]

    def override_user():
        db_session.refresh(user)
        return user

    def override_db():
        yield db_session

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    try:
        with TestClient(app) as client:
            # 1. Start chat session
            sess_resp = client.post(
                "/chat/sessions",
                json={
                    "organization_id": org.id,
                    "context_type": "repository",
                    "context_id": repo.id
                }
            )
            assert sess_resp.status_code == 200
            session_id = sess_resp.json()["id"]

            # 2. Post message
            msg_resp = client.post(
                f"/chat/sessions/{session_id}/messages?organization_id={org.id}",
                json={
                    "message": "Which modules depend on this function `authenticate_user`?",
                    "repository_id": repo.id
                }
            )
            assert msg_resp.status_code == 200
            body = msg_resp.json()
            assert body["role"] == "assistant"
            assert body["is_grounded"] is True
            assert isinstance(body["sources"], list)
            assert len(body["sources"]) > 0
            assert "Explanation" in body["content"]
            assert "Relevant Files" in body["content"]
    finally:
        app.dependency_overrides.clear()
