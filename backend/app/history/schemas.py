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
    file_path: str
    diff_snippet: Optional[str] = None
    pull_request_id: Optional[int] = None


class ChangeComparisonResponse(BaseModel):
    file_path: str
    total_historical_changes: int
    is_hotspot: bool
    hotspot_score: float
    governing_adrs: List[ADRResponse] = Field(default_factory=list)
    historical_changes: List[ChangeComparisonItem] = Field(default_factory=list)
    summary_guidance: str


class HistoricalIndexRequest(BaseModel):
    parse_adrs: bool = True
    mine_commits: bool = True
    compute_hotspots: bool = True


class HistoricalIndexResponse(BaseModel):
    status: str
    indexed_adrs_count: int
    indexed_commits_count: int
    hotspots_detected_count: int

