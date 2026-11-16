"""
Architecture Intelligence Pydantic Schemas — RepoMind 2.0.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ArchitectureRuleCreateRequest(BaseModel):
    rule_code: str = Field(..., max_length=64, description="Unique rule code, e.g. ARCH-001 or CUSTOM-001")
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    rule_type: str = Field(..., description="forbidden_dependency | layer_boundary | no_circular_dependencies | api_db_isolation | naming_convention")
    source_layer: Optional[str] = None
    target_layer: Optional[str] = None
    source_pattern: Optional[str] = None
    target_pattern: Optional[str] = None
    severity: str = Field("high", description="critical | high | medium | low")
    suggested_fix: Optional[str] = None
    is_enabled: bool = True


class ArchitectureRuleUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    rule_type: Optional[str] = None
    source_layer: Optional[str] = None
    target_layer: Optional[str] = None
    source_pattern: Optional[str] = None
    target_pattern: Optional[str] = None
    severity: Optional[str] = None
    suggested_fix: Optional[str] = None
    is_enabled: Optional[bool] = None


class ArchitectureRuleResponse(BaseModel):
    id: int
    repository_id: int
    rule_code: str
    name: str
    description: Optional[str] = None
    rule_type: str
    source_layer: Optional[str] = None
    target_layer: Optional[str] = None
    source_pattern: Optional[str] = None
    target_pattern: Optional[str] = None
    severity: str
    suggested_fix: Optional[str] = None
    is_enabled: bool
    is_system_inferred: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArchitectureViolationResponse(BaseModel):
    id: int
    analysis_id: int
    rule_id: Optional[int] = None
    rule_code: str
    violation_type: str
    severity: str
    title: str
    explanation: str
    suggested_correction: str
    source_file: str
    source_line: Optional[int] = None
    target_file: Optional[str] = None
    target_line: Optional[int] = None
    evidence: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArchitectureAnalysisResponse(BaseModel):
    id: int
    repository_id: int
    pull_request_id: Optional[int] = None
    health_score: int
    inferred_pattern: str
    pattern_confidence: float
    total_violations: int
    critical_violations: int
    circular_dependency_count: int
    layer_summary: Optional[Dict[str, Any]] = None
    flow_summary: Optional[Dict[str, Any]] = None
    mermaid_diagram: Optional[str] = None
    created_at: datetime
    violations: List[ArchitectureViolationResponse] = []

    model_config = ConfigDict(from_attributes=True)


class FlowChainResponse(BaseModel):
    endpoint_name: str
    endpoint_path: str
    route_file: str
    service_name: Optional[str] = None
    service_file: Optional[str] = None
    model_name: Optional[str] = None
    model_file: Optional[str] = None
    is_leaky: bool
    evidence: str
    suggested_fix: Optional[str] = None


class CircularDependencyResponse(BaseModel):
    cycle_path: List[str]
    length: int
    participating_files: List[str]
    severity: str
    title: str
    explanation: str
    decoupling_recommendation: str
