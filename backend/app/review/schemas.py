"""
Pydantic schemas for LLM output validation — Phase 8.

The LLM must return a JSON array of findings conforming to FindingSchema.
Per ADR-011: invalid JSON triggers one retry; second failure → ReviewRun FAILED.
Confidence values outside [0.0, 1.0] are rejected (not silently clamped).
"""
import json
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


VALID_SEVERITIES = frozenset(["critical", "high", "medium", "low", "info"])
VALID_CATEGORIES = frozenset([
    "standards_violation", "style", "security", "performance", "general"
])


class FindingSchema(BaseModel):
    """
    Schema that the LLM must return for each finding.
    Field names match the LLM prompt contract; they are mapped to DB columns
    in the persistence layer.
    """
    severity: str
    category: str          # maps to finding.type in the DB
    file: Optional[str] = None
    line: Optional[int] = None
    title: str
    problem: str           # maps to finding.explanation in the DB
    evidence: Optional[str] = None   # maps to finding.rule_source
    repository_rule: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float = Field(..., description="0.0–1.0 confidence score")

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        if v not in VALID_SEVERITIES:
            raise ValueError(
                f"severity must be one of {sorted(VALID_SEVERITIES)}, got '{v}'"
            )
        return v

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(VALID_CATEGORIES)}, got '{v}'"
            )
        return v

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        # Per spec: reject invalid values rather than silently clamping
        if not (0.0 <= v <= 1.0):
            raise ValueError(
                f"confidence must be between 0.0 and 1.0, got {v}"
            )
        return v

    @field_validator("title")
    @classmethod
    def validate_title_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v

    @field_validator("problem")
    @classmethod
    def validate_problem_nonempty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("problem must not be empty")
        return v


class ReviewOutput(BaseModel):
    """Wraps the top-level list returned by the LLM."""
    findings: List[FindingSchema]


class LLMOutputParseError(Exception):
    """Raised when LLM raw output cannot be parsed or validated."""
    def __init__(self, message: str, raw_output: str) -> None:
        super().__init__(message)
        self.raw_output = raw_output


def parse_llm_output(raw: str) -> List[FindingSchema]:
    """
    Parse and validate the raw LLM response string into a list of FindingSchema.

    Expects a JSON array at the top level.
    Raises LLMOutputParseError on any failure so the caller can retry.
    Raw output is attached to the exception — never logged with diff/PAT content.
    """
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LLMOutputParseError(
            f"LLM response is not valid JSON: {exc}",
            raw_output=raw,
        ) from exc

    if not isinstance(parsed, list):
        raise LLMOutputParseError(
            f"LLM response is not a JSON array (got {type(parsed).__name__})",
            raw_output=raw,
        )

    try:
        output = ReviewOutput(findings=parsed)
    except Exception as exc:
        raise LLMOutputParseError(
            f"LLM response failed schema validation: {exc}",
            raw_output=raw,
        ) from exc

    return output.findings


# --- Phase 10 API Schemas ---

from datetime import datetime

class ReviewTriggerResponse(BaseModel):
    """Returned by POST /pull-requests/{id}/review to provide the job reference."""
    job_id: int = Field(..., description="The ID of the ReviewRun, acting as the job_id.")
    status: str

class FindingResponse(BaseModel):
    """API view of a Finding."""
    id: int
    severity: str
    type: str
    file: Optional[str] = None
    line: Optional[int] = None
    title: str
    explanation: str
    rule_source: Optional[str] = None
    recommendation: Optional[str] = None
    confidence: float
    status: str

    class Config:
        from_attributes = True

class ReviewRunResponse(BaseModel):
    """Returned by GET /review-runs/{id} to provide run details and findings."""
    id: int
    pull_request_id: int
    commit_sha: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    findings: List[FindingResponse] = []

    class Config:
        from_attributes = True
