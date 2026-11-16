"""
AI Test Intelligence API Routes — RepoMind 2.0.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.organizations.models import Repository, Project
from backend.app.organizations.service import verify_org_member
from backend.app.github.models import PullRequest
from backend.app.testing.models import TestScenario, GeneratedTestCase
from backend.app.testing.schemas import (
    TestScenarioResponse,
    GeneratedTestCaseResponse,
    TestIntelligenceTriggerRequest,
    TestGenerationRequest,
    TestExecutionResponse,
    TestIntelligenceDashboardResponse,
    ExistingTestFileSummary,
)
from backend.app.testing.analyzer import run_test_intelligence_analysis, TestIntelligenceAnalyzer
from backend.app.testing.generator import TestCodeGenerator
from backend.app.testing.runner import IsolatedTestRunner

router = APIRouter(tags=["test-intelligence"])


def _get_authorized_repo(db: Session, repository_id: int, current_user: User) -> Repository:
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = db.get(Project, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_org_member(db, current_user.id, project.organization_id)
    return repo


@router.post(
    "/repositories/{repository_id}/test-intelligence/analyze",
    response_model=List[TestScenarioResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Trigger AI Test Intelligence analysis for a diff or PR",
)
def trigger_test_analysis(
    repository_id: int,
    payload: TestIntelligenceTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyzes changed code and generates structured test scenarios across 8 categories."""
    _get_authorized_repo(db, repository_id, current_user)

    diff = payload.diff or ""
    if payload.pull_request_id and not diff:
        pr = db.get(PullRequest, payload.pull_request_id)
        if pr and pr.repository_id == repository_id:
            # Try fetching diff from GitHub or PR files
            from backend.app.github.service import get_pull_request_diff
            try:
                diff = get_pull_request_diff(db, pr.id) or ""
            except Exception:
                diff = ""

    scenarios = run_test_intelligence_analysis(
        db=db,
        repository_id=repository_id,
        diff=diff,
        pull_request_id=payload.pull_request_id,
        review_run_id=payload.review_run_id,
    )
    return scenarios


@router.get(
    "/repositories/{repository_id}/pull-requests/{pull_request_id}/test-intelligence",
    response_model=List[TestScenarioResponse],
    summary="Get test intelligence scenarios for a pull request",
)
def get_pr_test_scenarios(
    repository_id: int,
    pull_request_id: int,
    category: Optional[str] = Query(None, description="Filter by category (positive, negative, boundary, validation, auth, etc.)"),
    coverage_gap_only: bool = Query(False, description="Filter only scenarios with missing coverage"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieves all generated test scenarios for a given PR."""
    _get_authorized_repo(db, repository_id, current_user)

    stmt = select(TestScenario).where(
        TestScenario.repository_id == repository_id,
        TestScenario.pull_request_id == pull_request_id,
    )
    if category:
        stmt = stmt.where(TestScenario.category == category)
    if coverage_gap_only:
        stmt = stmt.where(TestScenario.coverage_gap == True)

    stmt = stmt.order_by(TestScenario.id.asc())
    scenarios = list(db.execute(stmt).scalars().all())
    return scenarios


@router.post(
    "/test-scenarios/{scenario_id}/generate",
    response_model=GeneratedTestCaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate concrete test code for a scenario",
)
def generate_test_case(
    scenario_id: int,
    payload: Optional[TestGenerationRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generates runnable pytest / vitest code for the requested test scenario."""
    scenario = db.get(TestScenario, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="TestScenario not found")

    _get_authorized_repo(db, scenario.repository_id, current_user)

    generator = TestCodeGenerator(db=db)
    framework = payload.framework if payload else None
    language = payload.language if payload else None

    test_case = generator.generate_for_scenario(
        scenario_id=scenario_id,
        framework=framework,
        language=language,
    )
    return test_case


@router.post(
    "/generated-tests/{test_id}/execute",
    response_model=TestExecutionResponse,
    summary="Execute generated test case in an isolated, secret-stripped sandbox",
)
def execute_generated_test(
    test_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Executes the generated test case in an isolated temporary sandbox.
    Does not report as passed unless verified with exit code 0.
    """
    test_case = db.get(GeneratedTestCase, test_id)
    if not test_case:
        raise HTTPException(status_code=404, detail="GeneratedTestCase not found")

    scenario = test_case.scenario
    _get_authorized_repo(db, scenario.repository_id, current_user)

    runner = IsolatedTestRunner(db=db)
    executed = runner.execute_test(test_id)

    res = executed.execution_result or {}
    return TestExecutionResponse(
        test_id=executed.id,
        scenario_id=scenario.id,
        status=executed.execution_status,
        returncode=res.get("returncode"),
        stdout=res.get("stdout"),
        stderr=res.get("stderr"),
        duration_ms=res.get("duration_ms"),
        assertions_passed=res.get("assertions_passed", 0),
        assertions_failed=res.get("assertions_failed", 0),
        failure_details=res.get("failure_details"),
        executed_at=executed.executed_at,
    )


@router.get(
    "/test-intelligence/dashboard/{pull_request_id}",
    response_model=TestIntelligenceDashboardResponse,
    summary="Get complete test intelligence dashboard for a pull request",
)
def get_test_dashboard(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns aggregated dashboard metrics, scenarios, existing test files, and regression suites."""
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="PullRequest not found")

    _get_authorized_repo(db, pr.repository_id, current_user)

    # Scenarios
    scenarios = list(
        db.execute(
            select(TestScenario)
            .where(
                TestScenario.repository_id == pr.repository_id,
                TestScenario.pull_request_id == pull_request_id,
            )
            .order_by(TestScenario.id.asc())
        ).scalars().all()
    )

    # Category counts
    category_counts = {}
    coverage_gaps_count = 0
    all_generated_tests = []
    regression_files = set()

    for sc in scenarios:
        category_counts[sc.category] = category_counts.get(sc.category, 0) + 1
        if sc.coverage_gap:
            coverage_gaps_count += 1
        if sc.existing_test_file:
            regression_files.add(sc.existing_test_file)
        all_generated_tests.extend(sc.generated_tests)

    passed_count = sum(1 for t in all_generated_tests if t.execution_status == "passed")
    failed_count = sum(1 for t in all_generated_tests if t.execution_status == "failed")
    pending_count = sum(1 for t in all_generated_tests if t.execution_status == "pending")

    # Discover existing tests
    analyzer = TestIntelligenceAnalyzer(db=db, repository_id=pr.repository_id)
    raw_existing = analyzer._discover_existing_tests()
    existing_summaries = [
        ExistingTestFileSummary(
            test_file=e["test_file"],
            test_framework=e["framework"],
            test_count=len(e.get("tested_symbols", [])),
            tested_symbols=e.get("tested_symbols", []),
        )
        for e in raw_existing
    ]

    return TestIntelligenceDashboardResponse(
        repository_id=pr.repository_id,
        pull_request_id=pull_request_id,
        review_run_id=None,
        total_scenarios_count=len(scenarios),
        coverage_gaps_count=coverage_gaps_count,
        generated_tests_count=len(all_generated_tests),
        passed_tests_count=passed_count,
        failed_tests_count=failed_count,
        pending_tests_count=pending_count,
        category_counts=category_counts,
        scenarios=scenarios,
        existing_tests=existing_summaries,
        regression_test_files=list(regression_files),
    )

