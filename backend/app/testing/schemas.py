"""
Pydantic V2 Schemas for AI Test Intelligence — RepoMind 2.0.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GeneratedTestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_scenario_id: int
    language: str
    framework: str
    test_file_path: str
    test_code: str
    execution_status: str
    execution_result: Optional[Dict[str, Any]] = None
    security_reviewed: bool = False
    executed_at: Optional[datetime] = None
    created_at: datetime


class TestScenarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    pull_request_id: Optional[int] = None
    review_run_id: Optional[int] = None
    target_file: str
    target_symbol: str
    category: str
    title: str
    description: str
    edge_case_notes: Optional[str] = None
    suggested_assertions: Optional[List[str]] = Field(default_factory=list)
    existing_test_file: Optional[str] = None
    coverage_gap: bool = True
    impacted_endpoints: Optional[List[str]] = Field(default_factory=list)
    impacted_services: Optional[List[str]] = Field(default_factory=list)
    priority: str = "medium"
    created_at: datetime
    generated_tests: List[GeneratedTestCaseResponse] = Field(default_factory=list)


class TestIntelligenceTriggerRequest(BaseModel):
    pull_request_id: Optional[int] = None
    review_run_id: Optional[int] = None
    diff: Optional[str] = None


class TestGenerationRequest(BaseModel):
    framework: Optional[str] = None  # pytest, vitest
    language: Optional[str] = None   # python, typescript, javascript


class TestExecutionResponse(BaseModel):
    test_id: int
    scenario_id: int
    status: str
    returncode: Optional[int] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    duration_ms: Optional[float] = None
    assertions_passed: int = 0
    assertions_failed: int = 0
    failure_details: Optional[str] = None
    executed_at: datetime


class ExistingTestFileSummary(BaseModel):
    test_file: str
    test_framework: str
    test_count: int = 0
    tested_symbols: List[str] = Field(default_factory=list)


class TestIntelligenceDashboardResponse(BaseModel):
    repository_id: int
    pull_request_id: Optional[int] = None
    review_run_id: Optional[int] = None
    total_scenarios_count: int = 0
    coverage_gaps_count: int = 0
    generated_tests_count: int = 0
    passed_tests_count: int = 0
    failed_tests_count: int = 0
    pending_tests_count: int = 0
    category_counts: Dict[str, int] = Field(default_factory=dict)
    scenarios: List[TestScenarioResponse] = Field(default_factory=list)
    existing_tests: List[ExistingTestFileSummary] = Field(default_factory=list)
    regression_test_files: List[str] = Field(default_factory=list)

