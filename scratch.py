from pydantic import BaseModel, Field
from typing import Optional, List

class FindingSchema(BaseModel):
    severity: str
    confidence: float = Field(..., description='0.0-1.0')
    category: str
    review_dimension: str
    title: str
    problem: str
    affected_file: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    changed_code_evidence: Optional[str] = None
    repository_evidence: Optional[str] = None
    reasoning: str
    impact: str
    recommendation: Optional[str] = None
    evidence_sources: List[str] = []

print("Success")
