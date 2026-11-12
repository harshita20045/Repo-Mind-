"""
Pydantic Schemas for Developer Onboarding & Codebase Blueprint — RepoMind 2.0.

Provides strict, typed contracts for:
  - Subsystems and directory mapping
  - Request-to-database runtime flow tracing
  - Role-based learning tracks (Backend, Frontend, Fullstack)
  - Actionable milestone items and verification hints
  - Caution zones (blast radius) and safe starter areas
  - User progress tracking and private scratchpad
"""
import re
from typing import List, Optional, Dict, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# ---------------------------------------------------------------------------
# Atomic Blueprint Entities
# ---------------------------------------------------------------------------

class SubsystemItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=100, description="Name of the subsystem or architectural layer")
    path: str = Field(..., min_length=1, max_length=500, description="Root directory or file path for this subsystem")
    purpose: str = Field(..., min_length=5, max_length=1000, description="Summary of responsibilities")
    key_files: List[str] = Field(..., min_length=1, description="Primary files belonging to this subsystem")


class RequestFlowStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    step_number: int = Field(..., ge=1, le=20, description="Sequential order in the request execution lifecycle")
    layer: str = Field(..., min_length=2, max_length=100, description="Architectural tier (e.g. API Routing, Auth, Service, DB)")
    file: str = Field(..., min_length=1, max_length=500, description="Source file where execution occurs")
    symbol: Optional[str] = Field(None, max_length=150, description="Function, router, or class handling this step")
    description: str = Field(..., min_length=5, max_length=1000, description="What occurs at this execution stage")


class ReadingOrderItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(..., min_length=1, max_length=500, description="Relative path in the repository")
    role: str = Field(..., min_length=2, max_length=100, description="Role in system (e.g. Entry Point, Domain Model, Handler)")
    why_read: str = Field(..., min_length=10, max_length=1000, description="Specific learning objective for reading this file")
    focus_symbols: List[str] = Field(default_factory=list, description="Key functions/classes to inspect")
    key_lines: Optional[str] = Field(None, max_length=50, description="Optional suggested line range (e.g. L1-L45)")


class MilestoneItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_\-]+$", description="Unique milestone identifier")
    title: str = Field(..., min_length=5, max_length=150, description="Action-oriented milestone title")
    description: str = Field(..., min_length=10, max_length=1000, description="Detailed explanation of the exercise")
    action_type: Literal["run_command", "code_inspection", "first_task", "architecture_trace"] = Field(
        ...,
        description="Type of hands-on verification"
    )
    action_hint: str = Field(..., min_length=5, max_length=500, description="Exact command or search string to verify completion")


class TrackPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    track_name: Literal["backend", "frontend", "fullstack"] = Field(..., description="Role track name")
    reading_order: List[ReadingOrderItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Prioritized files to read (5-7 recommended where evidence exists)"
    )
    milestones: List[MilestoneItem] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Actionable onboarding milestones for this track"
    )

    @field_validator("milestones")
    @classmethod
    def validate_unique_milestone_ids(cls, v: List[MilestoneItem]) -> List[MilestoneItem]:
        ids = [m.id for m in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Milestone IDs within a track must be unique")
        return v


class CautionZone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., min_length=1, max_length=500, description="Path to sensitive directory or file")
    risk_level: Literal["critical", "high", "medium"] = Field(..., description="Blast radius severity")
    reason: str = Field(..., min_length=10, max_length=1000, description="Why this area requires senior review or caution")


class SafeStarterArea(BaseModel):
    model_config = ConfigDict(extra="forbid")

    area: str = Field(..., min_length=2, max_length=100, description="Subsystem or module safe for new developers")
    description: str = Field(..., min_length=10, max_length=1000, description="Why this area has low blast radius")
    starter_ideas: List[str] = Field(..., min_length=1, description="Concrete suggestions for first contribution tasks")


# ---------------------------------------------------------------------------
# Complete LLM Blueprint Payload (Parsed from Gemini JSON)
# ---------------------------------------------------------------------------

class LLMBlueprintPayload(BaseModel):
    """
    Strict payload schema expected from Gemini.
    Rejects fabricated or incomplete structures.
    """
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., min_length=20, max_length=5000, description="Comprehensive architectural summary")
    architecture_pattern: str = Field(..., min_length=3, max_length=100, description="Architecture pattern (e.g. Modular Monolith)")
    subsystems: List[SubsystemItem] = Field(..., min_length=1, description="Primary subsystems")
    request_flow: List[RequestFlowStep] = Field(..., min_length=2, description="Request-to-database execution steps")
    tracks: Dict[str, TrackPlan] = Field(..., description="Role plans keyed by 'backend', 'frontend', 'fullstack'")
    caution_zones: List[CautionZone] = Field(default_factory=list, description="High-risk caution zones")
    safe_starter_areas: List[SafeStarterArea] = Field(default_factory=list, description="Beginner-friendly contribution areas")
    mermaid_diagram: str = Field(..., min_length=10, description="Mermaid flowchart definition")

    @field_validator("tracks")
    @classmethod
    def validate_required_tracks(cls, v: Dict[str, TrackPlan]) -> Dict[str, TrackPlan]:
        required = {"backend", "frontend", "fullstack"}
        missing = required - set(v.keys())
        if missing:
            raise ValueError(f"Blueprint missing required tracks: {missing}")
        return v

    @field_validator("mermaid_diagram")
    @classmethod
    def validate_mermaid_syntax(cls, v: str) -> str:
        clean = v.strip().replace("```mermaid", "").replace("```", "").strip()
        valid_starters = ("graph ", "flowchart ", "sequenceDiagram", "classDiagram", "stateDiagram")
        if not any(clean.startswith(starter) for starter in valid_starters):
            raise ValueError("Mermaid diagram must begin with a recognized diagram type (e.g. 'flowchart TD' or 'graph TD')")
        return clean


# ---------------------------------------------------------------------------
# API Responses and Requests
# ---------------------------------------------------------------------------

class RepositoryBlueprintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    repository_id: int
    analyzed_commit_sha: str
    status: str
    is_outdated: bool = False
    current_indexed_sha: Optional[str] = None
    remote_github_sha: Optional[str] = None
    summary: Optional[str] = None
    architecture_pattern: Optional[str] = None
    subsystems: List[SubsystemItem] = []
    request_flow: List[RequestFlowStep] = []
    tracks: Dict[str, TrackPlan] = {}
    caution_zones: List[CautionZone] = []
    safe_starter_areas: List[SafeStarterArea] = []
    mermaid_diagram: Optional[str] = None
    retry_count: int = 0
    generation_error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    repository_id: int
    active_track: str
    completed_milestones: List[str]
    notes: Optional[str] = None
    updated_at: Optional[datetime] = None


class UpdateProgressRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    active_track: Optional[Literal["backend", "frontend", "fullstack"]] = None
    completed_milestones: Optional[List[str]] = None
    notes: Optional[str] = None

