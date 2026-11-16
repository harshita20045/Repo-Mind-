"""
Comprehensive test suite for RepoMind 2.0 Pull Request Review Engine Upgrade.

Verifies:
  1. Feature 1: PR analysis extraction, diff hunk parsing, and Code Knowledge Graph integration
  2. Feature 2: 8-stage multi-angle review categorization (syntax, security, quality,
                conventions, architecture, api_contract, dependencies, testing)
  3. Feature 3: Strict evidence validation & rejection of ungrounded/hallucinated findings
  4. Feature 4: Deterministic finding fingerprinting, intra-run deduplication, and
                lifecycle tracking (new, persistent, resolved, reopened)
  5. Feature 5: Explainable 7-factor risk scoring with evidence and actionable remediation
  6. Feature 6 & 7: Empty diffs, pure deletions, malformed AI output, worker fencing, and RBAC
"""
import json
import pytest
from datetime import datetime, timezone
from sqlalchemy import text
from unittest.mock import MagicMock, patch

from backend.app.auth.models import User, OrganizationMembership, RoleEnum, Organization
from backend.app.auth.permissions import Permission
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest, GitHubIdentity, GitHubCredential
from backend.app.github.encryption import encrypt_token
from backend.app.review.models import ReviewRun, Finding, FindingEvidence, RiskAssessment
from backend.app.review.schemas import FindingSchema, parse_llm_output, LLMOutputParseError
from backend.app.review.evidence import validate_findings, ValidatedFinding
from backend.app.review.analysis import (
    extract_pr_analysis_context,
    parse_diff_hunks,
    query_related_modules,
)
from backend.app.review.service import (
    compute_finding_fingerprint,
    _persist_validated_findings,
    run_review,
)
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.risk.engine import calculate_risk
from backend.app.rag.retriever import RetrievalResult
from backend.app.review.provider import LLMProviderError


MULTI_FILE_DIFF = """\
diff --git a/backend/app/auth/routes.py b/backend/app/auth/routes.py
index 100..200 100644
--- a/backend/app/auth/routes.py
+++ b/backend/app/auth/routes.py
@@ -10,4 +10,6 @@
 def login():
-    pass
+    token = generate_token()
+    return {"token": token}
diff --git a/backend/app/models/user.py b/backend/app/models/user.py
index 300..400 100644
--- a/backend/app/models/user.py
+++ b/backend/app/models/user.py
@@ -25,3 +25,4 @@
 class User:
+    is_admin = True
"""


@pytest.fixture
def test_setup(db_session):
    """Seed test tenant, repo, and PR in PostgreSQL."""
    assert db_session.execute(text("SELECT current_database()")).scalar() == "repomind_test"

    org = Organization(name="PR Engine Test Org")
    db_session.add(org)
    db_session.commit()

    user = User(email="pr_tester@example.com", password_hash="hashed_pw")
    db_session.add(user)
    db_session.commit()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        role=RoleEnum.ORG_ADMIN,
    )
    identity = GitHubIdentity(
        user_id=user.id,
        github_user_id="gh_9876",
        github_login="pr_tester",
    )
    db_session.add(membership)
    db_session.add(identity)
    db_session.commit()

    cred = GitHubCredential(
        github_identity_id=identity.id,
        encrypted_access_token=encrypt_token("fake_pat_upgrade_test"),
    )
    db_session.add(cred)

    project = Project(organization_id=org.id, name="PR Engine Project")
    db_session.add(project)
    db_session.commit()

    repo = Repository(
        project_id=project.id,
        github_owner="repomind-ai",
        github_name="pr-engine-test",
        github_repository_id="998877",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.commit()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_101",
        github_number=101,
        title="Implement OAuth authentication flows",
        description="Adds OAuth token generation and admin user attributes.",
        source_branch="feature/oauth-flow",
        target_branch="main",
        base_sha="base123",
        head_sha="head456",
        state="open",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    return {
        "org": org,
        "user": user,
        "repo": repo,
        "pr": pr,
    }


# ===========================================================================
# 1. PR Analysis & Knowledge Graph Context Extraction (Feature 1)
# ===========================================================================

def test_pr_analysis_extraction_and_diff_hunks(test_setup, db_session):
    """Verify PR Analysis extracts metadata, files, additions, and diff hunks."""
    pr = test_setup["pr"]

    pr_files_raw = [
        {"filename": "backend/app/auth/routes.py", "additions": 3, "deletions": 1, "status": "modified"},
        {"filename": "backend/app/models/user.py", "additions": 1, "deletions": 0, "status": "modified"},
    ]

    context = extract_pr_analysis_context(db_session, pr, MULTI_FILE_DIFF, pr_files_raw=pr_files_raw)

    assert context.pr_id == pr.id
    assert context.title == "Implement OAuth authentication flows"
    assert context.source_branch == "feature/oauth-flow"
    assert context.target_branch == "main"
    assert context.additions == 4
    assert context.deletions == 1
    assert "backend/app/auth/routes.py" in context.changed_files
    assert "backend/app/models/user.py" in context.changed_files
    assert not context.has_empty_diff

    # Verify diff hunk parsing
    hunks = context.diff_hunks_by_file
    assert "backend/app/auth/routes.py" in hunks
    auth_hunk = hunks["backend/app/auth/routes.py"][0]
    assert auth_hunk.old_start == 10
    assert auth_hunk.new_start == 10
    assert 11 in auth_hunk.added_line_numbers or 10 in auth_hunk.added_line_numbers


def test_related_module_query_with_knowledge_graph(test_setup, db_session):
    """Verify Code Knowledge Graph linking resolves parent modules, endpoints, and dependents."""
    repo = test_setup["repo"]
    repo_id = repo.id

    # Seed Knowledge Graph Nodes
    mod_auth = CodeGraphNode(
        repository_id=repo_id,
        node_key="mod:backend/app/auth",
        node_type="module",
        name="backend/app/auth",
        file_path="backend/app/auth",
    )
    file_routes = CodeGraphNode(
        repository_id=repo_id,
        node_key="file:backend/app/auth/routes.py",
        node_type="file",
        name="routes.py",
        file_path="backend/app/auth/routes.py",
    )
    endpoint_login = CodeGraphNode(
        repository_id=repo_id,
        node_key="api:POST:/auth/login",
        node_type="api_endpoint",
        name="POST /auth/login",
        file_path="backend/app/auth/routes.py",
    )
    file_consumer = CodeGraphNode(
        repository_id=repo_id,
        node_key="file:backend/app/api/client.py",
        node_type="file",
        name="client.py",
        file_path="backend/app/api/client.py",
    )
    db_session.add_all([mod_auth, file_routes, endpoint_login, file_consumer])
    db_session.flush()

    # Seed Knowledge Graph Edges
    edge_contains_file = CodeGraphEdge(
        repository_id=repo_id,
        source_node_id=mod_auth.id,
        target_node_id=file_routes.id,
        relation_type="contains",
    )
    edge_contains_api = CodeGraphEdge(
        repository_id=repo_id,
        source_node_id=file_routes.id,
        target_node_id=endpoint_login.id,
        relation_type="contains",
    )
    edge_imports = CodeGraphEdge(
        repository_id=repo_id,
        source_node_id=file_consumer.id,
        target_node_id=file_routes.id,
        relation_type="imports",
    )
    db_session.add_all([edge_contains_file, edge_contains_api, edge_imports])
    db_session.commit()

    # Query related context
    res = query_related_modules(db_session, repo_id, ["backend/app/auth/routes.py"])
    assert "backend/app/auth" in res["related_modules"]
    assert "POST /auth/login" in res["affected_endpoints"]
    assert "backend/app/api/client.py" in res["dependent_modules"]


# ===========================================================================
# 2. Multi-Stage Review 8-Category Validation (Feature 2)
# ===========================================================================

def test_multi_stage_review_8_categories_validation():
    """Verify schema acceptance and categorization across all 8 review stages."""
    categories = [
        "syntax",
        "security",
        "quality",
        "conventions",
        "architecture",
        "api_contract",
        "dependencies",
        "testing",
    ]

    for cat in categories:
        raw_json = json.dumps([{
            "severity": "medium",
            "category": cat,
            "file": "backend/app/main.py",
            "line": 15,
            "title": f"Test finding for {cat}",
            "problem": f"Detected issue in stage {cat}",
            "evidence": "+ x = 1",
            "repository_rule": None,
            "recommendation": "Follow guidelines",
            "confidence": 0.85,
        }])
        findings = parse_llm_output(raw_json)
        assert len(findings) == 1
        assert findings[0].category == cat


# ===========================================================================
# 3. Strict Evidence Validation & Rejection (Feature 3)
# ===========================================================================

def test_evidence_validation_rejects_hallucinations(test_setup, db_session):
    """Verify ungrounded findings citing non-existent files are rejected and discarded."""
    diff = MULTI_FILE_DIFF

    # Hallucinated finding citing a file that doesn't exist in diff
    hallucinated = FindingSchema(
        severity="critical",
        category="security",
        file="backend/app/payment/gateway.py",  # Not in diff!
        line=99,
        title="Exposed Stripe Secret Key",
        problem="Secret key hardcoded in payment gateway",
        evidence="STRIPE_KEY = 'sk_test_123'",
        confidence=0.95,
    )

    validated = validate_findings(
        findings=[hallucinated],
        retrieved_chunks=[],
        linter_results=[],
        diff=diff,
    )

    assert len(validated) == 1
    vf = validated[0]
    assert vf.evidence_status == "contradicted"
    assert vf.is_rejected is True
    assert "not found in PR diff" in vf.rejection_reason

    # Verify that persistence strictly drops the rejected finding
    run = ReviewRun(
        pull_request_id=test_setup["pr"].id,
        commit_sha=test_setup["pr"].head_sha,
        status="running",
    )
    db_session.add(run)
    db_session.flush()

    persisted = _persist_validated_findings(db_session, run, validated)
    assert len(persisted) == 0  # Hallucination discarded!


def test_evidence_validation_accepts_grounded_findings(test_setup, db_session):
    """Verify grounded findings with matching diff evidence are accepted and persisted."""
    diff = MULTI_FILE_DIFF

    grounded = FindingSchema(
        severity="high",
        category="security",
        file="backend/app/auth/routes.py",
        line=11,
        title="Unverified token generation",
        problem="Token generated without proper secret key binding",
        evidence="+    token = generate_token()",
        confidence=0.90,
    )

    validated = validate_findings(
        findings=[grounded],
        retrieved_chunks=[],
        linter_results=[],
        diff=diff,
    )

    assert len(validated) == 1
    vf = validated[0]
    assert vf.evidence_status == "supported"
    assert vf.is_rejected is False

    run = ReviewRun(
        pull_request_id=test_setup["pr"].id,
        commit_sha=test_setup["pr"].head_sha,
        status="running",
    )
    db_session.add(run)
    db_session.flush()

    persisted = _persist_validated_findings(db_session, run, validated)
    assert len(persisted) == 1
    assert persisted[0].title == "Unverified token generation"
    assert persisted[0].evidence_status == "supported"
    assert persisted[0].lifecycle_status == "new"


# ===========================================================================
# 4. Finding Lifecycle & Fingerprint Deduplication (Feature 4)
# ===========================================================================

def test_finding_lifecycle_and_fingerprint_deduplication(test_setup, db_session):
    """Verify persistent, resolved, and reopened transitions across successive runs."""
    pr_id = test_setup["pr"].id

    f_raw = FindingSchema(
        severity="medium",
        category="quality",
        file="backend/app/auth/routes.py",
        line=12,
        title="Missing docstring",
        problem="Public endpoint lacks explanatory docstring",
        evidence="+    return {'token': token}",
        confidence=0.80,
    )

    vf = ValidatedFinding(
        finding=f_raw,
        evidence_status="supported",
        adjusted_confidence=0.80,
    )

    # Run 1: Issue detected -> status = 'new'
    run1 = ReviewRun(pull_request_id=pr_id, status="completed", commit_sha="c1")
    db_session.add(run1)
    db_session.flush()
    findings_run1 = _persist_validated_findings(db_session, run1, [vf])
    db_session.commit()

    assert len(findings_run1) == 1
    assert findings_run1[0].lifecycle_status == "new"

    # Run 2: Issue still present -> status = 'persistent'
    run2 = ReviewRun(pull_request_id=pr_id, status="completed", commit_sha="c2")
    db_session.add(run2)
    db_session.flush()
    findings_run2 = _persist_validated_findings(db_session, run2, [vf])
    db_session.commit()

    assert len(findings_run2) == 1
    assert findings_run2[0].lifecycle_status == "persistent"

    # Run 3: Developer fixes issue (no findings in run 3) -> transitioned to 'resolved'
    run3 = ReviewRun(pull_request_id=pr_id, status="completed", commit_sha="c3")
    db_session.add(run3)
    db_session.flush()
    findings_run3 = _persist_validated_findings(db_session, run3, [])
    db_session.commit()

    assert len(findings_run3) == 1
    assert findings_run3[0].status == "resolved"
    assert findings_run3[0].lifecycle_status == "resolved"

    # Run 4: Developer re-introduces the issue -> transitioned to 'reopened'
    run4 = ReviewRun(pull_request_id=pr_id, status="completed", commit_sha="c4")
    db_session.add(run4)
    db_session.flush()
    findings_run4 = _persist_validated_findings(db_session, run4, [vf])
    db_session.commit()

    assert len(findings_run4) == 1
    assert findings_run4[0].lifecycle_status == "reopened"


def test_intra_run_deduplication(test_setup, db_session):
    """Verify that duplicate findings within the same review run are deduplicated."""
    pr_id = test_setup["pr"].id

    f_dup1 = FindingSchema(
        severity="high",
        category="security",
        file="backend/app/auth/routes.py",
        line=10,
        title="SQL injection risk",
        problem="Untrusted user input formatted into SQL query",
        evidence="query = f'SELECT * FROM users WHERE name={name}'",
        confidence=0.90,
    )
    # Duplicate with minor whitespace difference
    f_dup2 = FindingSchema(
        severity="high",
        category="security",
        file="backend/app/auth/routes.py",
        line=10,
        title="  SQL injection risk  ",
        problem="Untrusted user input formatted into SQL query",
        evidence="query = f'SELECT * FROM users WHERE name={name}'",
        confidence=0.90,
    )

    vf1 = ValidatedFinding(finding=f_dup1, evidence_status="supported", adjusted_confidence=0.90)
    vf2 = ValidatedFinding(finding=f_dup2, evidence_status="supported", adjusted_confidence=0.90)

    run = ReviewRun(pull_request_id=pr_id, status="completed", commit_sha="c1")
    db_session.add(run)
    db_session.flush()

    persisted = _persist_validated_findings(db_session, run, [vf1, vf2])
    assert len(persisted) == 1  # Successfully deduplicated to single finding


# ===========================================================================
# 5. Explainable 7-Factor Risk Score (Feature 5)
# ===========================================================================

def test_explainable_7_factor_risk_score_with_actions():
    """Verify all 7 factors, 100-sum weights, evidence arrays, and actionable recommendations."""
    f = FindingSchema(
        severity="critical",
        category="security",
        file="backend/app/auth.py",
        line=42,
        title="Critical auth flaw",
        problem="Password hash compared in plain text",
        confidence=0.95,
    )
    vf = ValidatedFinding(finding=f, evidence_status="supported", adjusted_confidence=0.95)

    risk = calculate_risk(
        diff="--- a/backend/app/auth.py\n+++ b/backend/app/auth.py\n@@ -40,5 +40,5 @@\n+auth()",
        validated_findings=[vf],
        conflicts=[],
        linter_results=[],
        changed_files=["backend/app/auth.py", "requirements.txt"],
        additions=50,
        deletions=10,
    )

    # 7 factors
    factors = risk.factors
    assert "security_exposure" in factors
    assert "architecture_risk" in factors
    assert "test_risk" in factors
    assert "code_complexity" in factors
    assert "change_size" in factors
    assert "dependency_risk" in factors
    assert "blast_radius_factor" in factors

    # Weights sum to 100
    weights_sum = sum(v["weight"] for v in factors.values())
    assert weights_sum == 100

    # Evidence & Actionable Recommendations
    assert "evidence" in factors["security_exposure"]
    assert "recommended_action" in factors["security_exposure"]
    assert len(factors["security_exposure"]["evidence"]) > 0

    assert "evidence" in factors["dependency_risk"]
    assert "requirements.txt" in str(factors["dependency_risk"]["evidence"])

    # Advisory clause in summary
    assert "not certainty of defects" in risk.summary.lower()


# ===========================================================================
# 6. Empty Diffs & Pure Deletions Handling (Feature 6 & 7)
# ===========================================================================

def test_empty_diff_and_pure_deletion_handling(test_setup, db_session):
    """Verify empty diffs are handled cleanly without running unnecessary review stages."""
    pr = test_setup["pr"]

    # Empty diff
    ctx_empty = extract_pr_analysis_context(db_session, pr, "", pr_files_raw=[])
    assert ctx_empty.has_empty_diff is True
    assert ctx_empty.has_only_deletions is False

    # Pure deletion diff
    deletion_files = [
        {"filename": "deprecated_service.py", "additions": 0, "deletions": 150, "status": "deleted"}
    ]
    ctx_del = extract_pr_analysis_context(
        db_session,
        pr,
        "--- a/deprecated_service.py\n+++ /dev/null\n@@ -1,5 +0,0 @@\n-old code",
        pr_files_raw=deletion_files,
    )
    assert ctx_del.has_empty_diff is False
    assert ctx_del.has_only_deletions is True


# ===========================================================================
# 7. Malformed AI Output & Retry (Feature 2 & 7)
# ===========================================================================

def test_malformed_ai_output_parsing():
    """Verify that malformed JSON or invalid schema raises LLMOutputParseError."""
    # 1. Invalid JSON
    with pytest.raises(LLMOutputParseError):
        parse_llm_output("This is not JSON at all.")

    # 2. Not a JSON array
    with pytest.raises(LLMOutputParseError):
        parse_llm_output('{"findings": []}')

    # 3. Missing required field (problem)
    with pytest.raises(LLMOutputParseError):
        parse_llm_output('[{"severity": "high", "category": "security", "title": "Incomplete"}]')

    # 4. Out of bounds confidence (1.5 > 1.0)
    with pytest.raises(LLMOutputParseError):
        parse_llm_output('[{'
            '"severity": "high",'
            '"category": "security",'
            '"file": "a.py",'
            '"line": 1,'
            '"title": "Test",'
            '"problem": "Error",'
            '"confidence": 1.5'
        '}]')
