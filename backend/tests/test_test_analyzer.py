"""
Unit tests for AI Test Intelligence Analyzer — RepoMind 2.0.
"""
import pytest
from datetime import datetime, timezone

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.rag.models import Document
from backend.app.intelligence.models import CodeGraphNode, CodeGraphEdge
from backend.app.testing.models import TestScenario
from backend.app.testing.analyzer import TestIntelligenceAnalyzer, run_test_intelligence_analysis


@pytest.fixture
def test_data(db_session):
    """Seed test fixtures in test database."""
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.flush()

    project = Project(name="Test Project", organization_id=org.id)
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="101",
        github_name="test-repo",
        github_owner="test-owner",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    # Seed existing test document
    doc = Document(
        repository_id=repo.id,
        path="backend/tests/test_calculator.py",
        content_hash="abc",
    )
    db_session.add(doc)

    # Seed knowledge graph node and edge
    calc_node = CodeGraphNode(
        repository_id=repo.id,
        node_key="calc_key",
        node_type="function",
        name="add_numbers",
        file_path="backend/app/calculator.py",
        start_line=1,
        end_line=10,
    )
    api_node = CodeGraphNode(
        repository_id=repo.id,
        node_key="api_key",
        node_type="api_endpoint",
        name="calculate_route",
        file_path="backend/app/routes/calc.py",
        start_line=15,
        end_line=25,
    )
    db_session.add_all([calc_node, api_node])
    db_session.flush()

    edge = CodeGraphEdge(
        repository_id=repo.id,
        source_node_id=api_node.id,
        target_node_id=calc_node.id,
        relation_type="calls",
    )
    db_session.add(edge)

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_101",
        github_number=1,
        title="Add subtract feature",
        head_sha="sha1",
        base_sha="sha0",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    return db_session, repo, pr


def test_analyzer_identifies_modified_functions_and_generates_8_categories(test_data):
    db_session, repo, pr = test_data

    diff = """diff --git a/backend/app/math_ops.py b/backend/app/math_ops.py
--- a/backend/app/math_ops.py
+++ b/backend/app/math_ops.py
@@ -1,4 +1,8 @@
+def subtract_numbers(a: int, b: int) -> int:
+    \"\"\"Subtract b from a.\"\"\"
+    return a - b
"""

    scenarios = run_test_intelligence_analysis(
        db=db_session,
        repository_id=repo.id,
        diff=diff,
        pull_request_id=pr.id,
    )

    assert len(scenarios) == 8

    categories = {s.category for s in scenarios}
    expected_categories = {
        "positive", "negative", "boundary", "validation",
        "authentication", "authorization", "integration", "regression"
    }
    assert categories == expected_categories

    for sc in scenarios:
        assert sc.target_symbol == "subtract_numbers"
        assert sc.target_file == "backend/app/math_ops.py"
        assert sc.coverage_gap is True  # math_ops has no existing test file
        assert sc.existing_test_file == "backend/tests/test_math_ops.py"
        assert len(sc.suggested_assertions) > 0


def test_analyzer_detects_existing_test_mapping(test_data):
    db_session, repo, pr = test_data

    diff = """diff --git a/backend/app/calculator.py b/backend/app/calculator.py
--- a/backend/app/calculator.py
+++ b/backend/app/calculator.py
@@ -1,5 +1,5 @@
-def add_numbers(a, b):
+def add_numbers(a: int, b: int) -> int:
     return a + b
"""

    scenarios = run_test_intelligence_analysis(
        db=db_session,
        repository_id=repo.id,
        diff=diff,
        pull_request_id=pr.id,
    )

    assert len(scenarios) == 8
    pos_scenario = next(s for s in scenarios if s.category == "positive")
    assert pos_scenario.target_symbol == "add_numbers"
    # test_calculator.py exists in DB
    assert pos_scenario.existing_test_file == "backend/tests/test_calculator.py"
    assert pos_scenario.coverage_gap is False  # Already mapped to test_calculator.py
    # Impacted endpoint traced from knowledge graph
    assert any("calculate_route" in ep for ep in pos_scenario.impacted_endpoints)


def test_analyzer_empty_diff_returns_empty(test_data):
    db_session, repo, pr = test_data
    scenarios = run_test_intelligence_analysis(
        db=db_session,
        repository_id=repo.id,
        diff="",
    )
    assert scenarios == []
