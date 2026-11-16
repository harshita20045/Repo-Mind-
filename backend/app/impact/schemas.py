"""
Pydantic Schemas for Change Impact & Blast Radius Analyzer — RepoMind 2.0.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field


class ImpactAnalysisTriggerRequest(BaseModel):
    diff: str = Field(..., description="Unified git diff to analyze")
    commit_sha: Optional[str] = None
    target_branch: Optional[str] = "main"
    pull_request_id: Optional[int] = None
    max_depth: Optional[int] = 3


class AffectedComponentResponse(BaseModel):
    name: str
    file_path: str
    component_type: str
    impact_tier: str
    relationship: str
    why_affected: str
    severity: str
    distance: int
    supporting_evidence: Optional[str] = None
    suggested_verification: Optional[str] = None


class BreakingChangeResponse(BaseModel):
    change_type: str
    component_name: str
    file_path: str
    severity: str
    title: str
    description: str
    evidence: str
    suggested_fix: str


class TestRecommendationResponse(BaseModel):
    target_component: str
    target_file: str
    recommended_test_file: str
    test_type: str
    priority: str
    reason: str
    command: str


class GraphVisualizationResponse(BaseModel):
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    mermaid: Optional[str] = None


class ChangeImpactAnalysisResponse(BaseModel):
    id: int
    repository_id: int
    pull_request_id: Optional[int] = None
    review_run_id: Optional[int] = None
    commit_sha: Optional[str] = None
    target_branch: Optional[str] = None
    risk_level: str
    directly_affected_count: int
    indirectly_affected_count: int
    breaking_changes_count: int
    affected_components: List[AffectedComponentResponse] = []
    breaking_changes: List[BreakingChangeResponse] = []
    test_recommendations: List[TestRecommendationResponse] = []
    graph_visualization: Optional[GraphVisualizationResponse] = None
    summary: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
