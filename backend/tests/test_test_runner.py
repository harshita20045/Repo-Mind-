"""
Unit tests for Isolated Test Sandbox Runner & Security Review — RepoMind 2.0.
"""
import pytest

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.testing.models import TestScenario, GeneratedTestCase
from backend.app.testing.runner import IsolatedTestRunner, review_code_security
from backend.app.testing.generator import TestCodeGenerator


@pytest.fixture
def test_runner_data(db_session):
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.flush()

    project = Project(name="Test Project", organization_id=org.id)
    db_session.add(project)
    db_session.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id="102",
        github_name="test-repo",
        github_owner="test-owner",
        default_branch="main",
    )
    db_session.add(repo)
    db_session.flush()

    scenario = TestScenario(
        repository_id=repo.id,
        target_file="backend/app/auth.py",
        target_symbol="verify_token",
        category="positive",
        title="Verify nominal token verification",
        description="Check valid token returns user object",
        coverage_gap=True,
    )
    db_session.add(scenario)
    db_session.commit()

    return db_session, repo, scenario


def test_security_review_detects_dangerous_calls():
    # 1. os.system
    code_with_system = """
import os
def test_hack():
    os.system("rm -rf /")
"""
    is_safe, reason = review_code_security(code_with_system, "python")
    assert is_safe is False
    assert "Prohibited method call: system()" in reason

    # 2. eval()
    code_with_eval = """
def test_eval():
    eval("__import__('os').system('ls')")
"""
    is_safe, reason = review_code_security(code_with_eval, "python")
    assert is_safe is False
    assert "Prohibited built-in call: eval()" in reason

    # 3. Disallowed module
    code_with_shutil = """
import shutil
def test_shutil():
    pass
"""
    is_safe, reason = review_code_security(code_with_shutil, "python")
    assert is_safe is False
    assert "Prohibited module imported" in reason

    # 4. Safe test code
    safe_code = """
import pytest
def test_addition():
    assert 1 + 1 == 2
"""
    is_safe, reason = review_code_security(safe_code, "python")
    assert is_safe is True
    assert reason is None


def test_generator_creates_pending_test_case(test_runner_data):
    db_session, repo, scenario = test_runner_data
    generator = TestCodeGenerator(db=db_session)

    test_case = generator.generate_for_scenario(scenario.id)

    assert test_case.id is not None
    assert test_case.execution_status == "pending"  # Crucial rule: never passed before execution
    assert test_case.security_reviewed is False
    assert "def test_verify_token_positive_nominal_flow" in test_case.test_code


def test_runner_executes_safe_test_and_captures_pass(test_runner_data):
    db_session, repo, scenario = test_runner_data

    # Create a safe passing test
    test_case = GeneratedTestCase(
        test_scenario_id=scenario.id,
        language="python",
        framework="pytest",
        test_file_path="backend/tests/test_verify.py",
        test_code="""
def test_dummy_passing():
    assert 2 * 2 == 4
""",
        execution_status="pending",
    )
    db_session.add(test_case)
    db_session.commit()

    runner = IsolatedTestRunner(db=db_session)
    executed = runner.execute_test(test_case.id)

    assert executed.execution_status == "passed"
    assert executed.security_reviewed is True
    assert executed.execution_result["returncode"] == 0
    assert executed.execution_result["assertions_passed"] == 1
    assert executed.execution_result["duration_ms"] > 0
    assert executed.executed_at is not None


def test_runner_blocks_malicious_code_and_marks_error(test_runner_data):
    db_session, repo, scenario = test_runner_data

    malicious_test = GeneratedTestCase(
        test_scenario_id=scenario.id,
        language="python",
        framework="pytest",
        test_file_path="backend/tests/test_hack.py",
        test_code="""
import os
def test_dangerous():
    os.system("echo hacked")
""",
        execution_status="pending",
    )
    db_session.add(malicious_test)
    db_session.commit()

    runner = IsolatedTestRunner(db=db_session)
    executed = runner.execute_test(malicious_test.id)

    assert executed.execution_status == "error"
    assert executed.security_reviewed is False
    assert "Security pre-execution check failed" in executed.execution_result["stderr"]


def test_runner_captures_assertion_failure_without_false_pass(test_runner_data):
    db_session, repo, scenario = test_runner_data

    failing_test = GeneratedTestCase(
        test_scenario_id=scenario.id,
        language="python",
        framework="pytest",
        test_file_path="backend/tests/test_fail.py",
        test_code="""
def test_intentional_failure():
    assert 1 == 2
""",
        execution_status="pending",
    )
    db_session.add(failing_test)
    db_session.commit()

    runner = IsolatedTestRunner(db=db_session)
    executed = runner.execute_test(failing_test.id)

    assert executed.execution_status == "failed"
    assert executed.execution_result["returncode"] != 0
    assert executed.execution_result["assertions_failed"] == 1
    assert "assert 1 == 2" in executed.execution_result["stdout"]
