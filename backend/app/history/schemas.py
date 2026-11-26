"""
Pydantic schemas for Historical Code Intelligence — RepoMind 2.0.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class HistoricalPRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    github_number: int
    title: str
    state: str
    github_author_login: Optional[str] = None
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
    head_sha: Optional[str] = None
    files_changed_count: int = 0
    additions: Optional[int] = 0
    deletions: Optional[int] = 0
    merged_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    linked_issues: List[str] = Field(default_factory=list)
    summary: Optional[str] = None


class HistoricalCommitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commit_sha: str
    author: Optional[str] = None
    committer: Optional[str] = None
    message: str
    committed_at: datetime
    is_bugfix: bool = False
    files_changed: Optional[List[Dict[str, Any]]] = None
    linked_issues: Optional[List[str]] = None
    original_decision_rationale: Optional[str] = None


class RecurringHotspotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_path: str
    total_commits: int
    bugfix_commits_count: int
    recurring_findings_count: int
    hotspot_score: float
    severity: str
    recurring_finding_categories: Optional[Dict[str, int]] = None
    historical_references: Optional[List[Dict[str, Any]]] = None
    last_bugfix_at: Optional[datetime] = None


class ADRResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    adr_number: str
    title: str
    status: str
    context: Optional[str] = None
    decision: str
    options_considered: Optional[List[str]] = None
    reason: Optional[str] = None
    consequences: Optional[str] = None
    superseded_alternative: Optional[str] = None
    file_source: Optional[str] = None
    affected_modules: Optional[List[str]] = None
    date: Optional[datetime] = None

    # 15-attribute structured decision framework
    decision_category: Optional[str] = "architecture"
    decision_type: Optional[str] = "synthetic_demo"  # documented | inferred | synthetic_demo
    original_problem: Optional[str] = None
    business_context: Optional[str] = None
    technical_context: Optional[str] = None
    advantages: Optional[List[str]] = None
    trade_offs: Optional[List[str]] = None
    related_prs: Optional[List[str]] = None
    current_relevance: Optional[str] = "active"


class EvolutionMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    milestone_date: datetime
    title: str
    category: str  # architecture | api | database | dependency | security | performance
    module_name: str
    pr_id: Optional[int] = None
    commit_sha: Optional[str] = None
    previous_approach: Optional[str] = None
    current_approach: Optional[str] = None
    problem_solved: str
    reason_for_change: str
    business_context: Optional[str] = None
    technical_explanation: Optional[str] = None
    affected_files: Optional[List[str]] = None
    affected_modules: Optional[List[str]] = None
    dependencies_impacted: Optional[List[str]] = None
    consequences: Optional[str] = None
    lessons_learned: Optional[str] = None
    is_synthetic_demo: bool = True


class BugLessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    issue_title: str
    issue_category: str
    module_name: str
    description: str
    root_cause: Optional[str] = None
    related_pr_number: Optional[int] = None
    related_commit_sha: Optional[str] = None
    files_involved: Optional[List[str]] = None
    resolution_details: str
    tests_added: Optional[List[str]] = None
    prevention_recommendations: str
    warning_triggers: Optional[List[str]] = None
    occurred_at: datetime


class ModuleEvolutionResponse(BaseModel):
    module_name: str
    display_name: str
    original_architecture: str
    current_architecture: str
    total_modifications: int = 0
    evolution_milestones: List[EvolutionMilestoneResponse] = Field(default_factory=list)
    governing_decisions: List[ADRResponse] = Field(default_factory=list)
    historical_bugs: List[BugLessonResponse] = Field(default_factory=list)
    critical_cautions: List[str] = Field(default_factory=list)


class EvolutionOverviewResponse(BaseModel):
    total_milestones: int = 0
    architecture_changes_count: int = 0
    api_changes_count: int = 0
    database_changes_count: int = 0
    dependency_changes_count: int = 0
    security_changes_count: int = 0
    performance_changes_count: int = 0
    top_hotspots: List[RecurringHotspotResponse] = Field(default_factory=list)
    recent_milestones: List[EvolutionMilestoneResponse] = Field(default_factory=list)


class HistoricalImpactAnalysisRequest(BaseModel):
    module_name: Optional[str] = None
    file_path: Optional[str] = None
    proposed_change_summary: Optional[str] = None


class HistoricalImpactAnalysisResponse(BaseModel):
    target_module: str
    target_file: Optional[str] = None
    is_hotspot: bool = False
    hotspot_score: float = 0.0
    previous_major_modifications: List[EvolutionMilestoneResponse] = Field(default_factory=list)
    governing_decisions: List[ADRResponse] = Field(default_factory=list)
    verified_dependencies: List[str] = Field(default_factory=list)
    inferred_potential_impacts: List[str] = Field(default_factory=list)
    connected_apis: List[str] = Field(default_factory=list)
    database_dependencies: List[str] = Field(default_factory=list)
    historical_bugs_and_warnings: List[BugLessonResponse] = Field(default_factory=list)
    relevant_regression_tests: List[str] = Field(default_factory=list)
    structured_report: str


class SimilarPRSearchRequest(BaseModel):
    query: Optional[str] = None
    file_path: Optional[str] = None
    module_name: Optional[str] = None
    change_category: Optional[str] = None
    limit: int = 10


class SimilarPRMatchResponse(BaseModel):
    pr_id: int
    github_number: int
    title: str
    change_category: str
    relevance_reason: str
    what_changed: str
    problem_addressed: str
    review_feedback_summary: str
    outcome: str
    lessons_relevant_to_current_work: str
    evidence_snippets: List[str] = Field(default_factory=list)


class SimilarBugResponse(BaseModel):
    reference: str  # PR # or Commit SHA
    file_path: str
    date: Optional[str] = None
    title: str
    description: str
    category: str
    resolution_details: str
    supporting_evidence: str


class ChangeComparisonItem(BaseModel):
    reference: str  # PR # or Commit SHA
    file: str
    date: Optional[str] = None
    author: Optional[str] = None
    original_decision: str
    supporting_evidence: str
    is_bugfix: bool = False
    risk_warning: Optional[str] = None


class ChangeComparisonRequest(BaseModel):
    file_path: Optional[str] = None
    diff_snippet: Optional[str] = None
    pull_request_id: Optional[int] = None


class ChangeComparisonResponse(BaseModel):
    file_path: Optional[str] = None
    total_historical_changes: int = 0
    is_hotspot: bool = False
    is_problematic_hotspot: Optional[bool] = False
    hotspot_score: float = 0.0
    hotspot_details: Optional[Dict[str, Any]] = None
    governing_adrs: List[ADRResponse] = Field(default_factory=list)
    relevant_adrs: List[ADRResponse] = Field(default_factory=list)
    historical_changes: List[ChangeComparisonItem] = Field(default_factory=list)
    historical_commits: List[HistoricalCommitResponse] = Field(default_factory=list)
    similar_resolved_bugs: List[SimilarBugResponse] = Field(default_factory=list)
    summary_guidance: Optional[str] = None
    change_evolution_summary: Optional[str] = None


class HistoricalIndexRequest(BaseModel):
    parse_adrs: bool = True
    mine_commits: bool = True
    compute_hotspots: bool = True


class HistoricalIndexResponse(BaseModel):
    status: str
    indexed_adrs_count: int
    indexed_commits_count: int
    hotspots_detected_count: int

