"""
Pydantic Schemas for Change Impact & Blast Radius Analyzer — RepoMind 2.0.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator


class ImpactAnalysisTriggerRequest(BaseModel):
    diff: str = Field(..., description="Unified git diff to analyze")
    commit_sha: Optional[str] = None
    target_branch: Optional[str] = "main"
    pull_request_id: Optional[int] = None
    max_depth: Optional[int] = 3


class AffectedComponentResponse(BaseModel):
    name: str = ""
    file_path: str = ""
    component_type: str = "file"
    impact_tier: str = "directly_affected"
    relationship: str = "modified"
    why_affected: str = ""
    severity: str = "medium"
    distance: int = 0
    supporting_evidence: Optional[str] = None
    suggested_verification: Optional[str] = None

    # Complementary aliases for UI compatibility
    component_name: Optional[str] = None
    node_type: Optional[str] = None
    reason: Optional[str] = None
    evidence: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, str):
            f_name = data.split("/")[-1] if "/" in data else data
            return {
                "name": f_name,
                "component_name": f_name,
                "file_path": data,
                "component_type": "file",
                "node_type": "file",
                "impact_tier": "directly_affected",
                "relationship": "modified",
                "why_affected": f"Component at {data} directly modified",
                "reason": f"Component at {data} directly modified",
                "severity": "medium",
                "distance": 0,
                "supporting_evidence": f"File path: {data}",
                "evidence": f"File path: {data}",
                "suggested_verification": f"Run tests covering {f_name}",
            }
        elif isinstance(data, dict):
            d = dict(data)
            f_path = d.get("file_path") or ""
            f_name = d.get("name") or d.get("component_name") or (f_path.split("/")[-1] if f_path else "component")
            c_type = d.get("component_type") or d.get("node_type") or "file"
            reason = d.get("why_affected") or d.get("reason") or "Directly modified in changes"
            evidence = d.get("supporting_evidence") or d.get("evidence")
            d["name"] = f_name
            d["component_name"] = f_name
            d["component_type"] = c_type
            d["node_type"] = c_type
            d["why_affected"] = reason
            d["reason"] = reason
            d["supporting_evidence"] = evidence
            d["evidence"] = evidence
            d["impact_tier"] = d.get("impact_tier") or "directly_affected"
            d["relationship"] = d.get("relationship") or "modified"
            d["severity"] = d.get("severity") or "medium"
            d["distance"] = d.get("distance", 0)
            return d
        return data


class BreakingChangeResponse(BaseModel):
    change_type: str = "contract_mutation"
    component_name: str = "API Contract"
    file_path: str = ""
    severity: str = "high"
    title: str = ""
    description: str = ""
    evidence: str = ""
    suggested_fix: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {
                "change_type": "contract_mutation",
                "component_name": "API Contract",
                "file_path": "",
                "severity": "high",
                "title": data,
                "description": data,
                "evidence": data,
                "suggested_fix": "Verify backward compatibility with consumer services.",
            }
        elif isinstance(data, dict):
            d = dict(data)
            desc = d.get("description") or d.get("title") or "Potential breaking change detected"
            title = d.get("title") or desc[:60]
            d["title"] = title
            d["description"] = desc
            d["evidence"] = d.get("evidence") or desc
            d["change_type"] = d.get("change_type") or "contract_mutation"
            d["component_name"] = d.get("component_name") or "API Contract"
            d["file_path"] = d.get("file_path") or ""
            d["severity"] = d.get("severity") or "high"
            d["suggested_fix"] = d.get("suggested_fix") or "Review backward-compatibility and update clients."
            return d
        return data


class TestRecommendationResponse(BaseModel):
    target_component: str = "Modified Code"
    target_file: str = ""
    recommended_test_file: str = "tests/"
    test_type: str = "unit_test"
    priority: str = "P1_HIGH"
    reason: str = ""
    command: str = ""

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, str):
            cmd = data if ("pytest" in data or "npm" in data) else f"pytest {data}"
            return {
                "target_component": "Modified Code",
                "target_file": "",
                "recommended_test_file": "tests/",
                "test_type": "unit_test",
                "priority": "P1_HIGH",
                "reason": data,
                "command": cmd,
            }
        elif isinstance(data, dict):
            d = dict(data)
            t_comp = d.get("target_component") or "Modified Code"
            d["target_component"] = t_comp
            d["target_file"] = d.get("target_file") or ""
            d["recommended_test_file"] = d.get("recommended_test_file") or "tests/"
            d["test_type"] = d.get("test_type") or "unit_test"
            d["priority"] = d.get("priority") or "P1_HIGH"
            d["reason"] = d.get("reason") or f"Recommended tests for {t_comp}"
            cmd = d.get("command") or f"pytest backend/tests/"
            d["command"] = cmd
            return d
        return data


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
    affected_components: List[AffectedComponentResponse] = Field(default_factory=list)
    breaking_changes: List[BreakingChangeResponse] = Field(default_factory=list)
    test_recommendations: List[TestRecommendationResponse] = Field(default_factory=list)
    graph_visualization: Optional[GraphVisualizationResponse] = None
    summary: Optional[str] = None
    created_at: datetime

    @field_validator("affected_components", "breaking_changes", "test_recommendations", mode="before")
    @classmethod
    def ensure_list(cls, v: Any) -> List[Any]:
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return [v]

    model_config = ConfigDict(from_attributes=True)
