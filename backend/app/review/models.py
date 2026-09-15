"""
Review SQLAlchemy models — Phase 8 + RepoMind 2.0 extension.

Tables:
  review_run       — one per PR analysis attempt
  finding          — structured LLM findings
  linter_result    — raw static analysis output
  risk_assessment  — PR-level risk score and factors [NEW]
  conflict         — semantic and mechanical conflicts [NEW]
  finding_evidence — grounded evidence per finding [NEW]
  human_decision   — human approval/rejection audit trail [NEW]

review_run.status lifecycle:
    pending → running → completed
                     → failed
    (cancelled reserved for async-job orchestration)
"""
import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, Text,
    DateTime, ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class ReviewRun(Base):
    """
    One ReviewRun per PR analysis attempt.
    Tracks lifecycle from creation through completion/failure.
    """
    __tablename__ = "review_run"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(
        Integer,
        ForeignKey("pull_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha = Column(String(255), nullable=True)
    # Lifecycle: pending | running | completed | failed | cancelled
    status = Column(String(50), nullable=False, default="pending")
    repomind_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    llm_model = Column(String(255), nullable=True)
    rag_enabled = Column(Boolean, nullable=False, default=True)
    # Repository intelligence mode used for this run
    intelligence_mode = Column(String(20), nullable=True, default="v1")  # v1 | v2 | auto
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    # Worker progress message shown in UI
    progress_message = Column(String(255), nullable=True)
    # Raw LLM output (for debugging — never exposed to UI)
    error_message = Column(Text, nullable=True)

    findings = relationship(
        "Finding",
        back_populates="review_run",
        cascade="all, delete-orphan",
    )
    linter_results = relationship(
        "LinterResult",
        back_populates="review_run",
        cascade="all, delete-orphan",
    )
    risk_assessment = relationship(
        "RiskAssessment",
        back_populates="review_run",
        uselist=False,
        cascade="all, delete-orphan",
    )
    conflicts = relationship(
        "Conflict",
        back_populates="review_run",
        cascade="all, delete-orphan",
    )
    human_decisions = relationship(
        "HumanDecision",
        back_populates="review_run",
        cascade="all, delete-orphan",
    )


class Finding(Base):
    """
    A single structured finding produced by the LLM review.
    Linked to a ReviewRun; never produced without one.
    """
    __tablename__ = "finding"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # type/category: correctness | security | performance | maintainability |
    #                architecture | testing | compatibility | documentation |
    #                standards_violation | style | general
    type = Column(String(100), nullable=False)
    # severity: critical | high | medium | low | info
    severity = Column(String(50), nullable=False)
    file = Column(String(1024), nullable=True)
    line = Column(Integer, nullable=True)
    title = Column(String(512), nullable=False)
    explanation = Column(Text, nullable=False)
    rule_source = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False)
    # status: open | accepted | rejected | resolved | dismissed
    status = Column(String(50), nullable=False, default="open")
    # Evidence grounding status (RepoMind 2.0)
    # supported | unverified | contradicted
    evidence_status = Column(String(50), nullable=True, default="unverified")
    # Tracks across review runs: new | persistent | resolved
    lifecycle_status = Column(String(50), nullable=True, default="new")

    review_run = relationship("ReviewRun", back_populates="findings")
    evidence = relationship(
        "FindingEvidence",
        back_populates="finding",
        cascade="all, delete-orphan",
    )


class LinterResult(Base):
    """Raw linter output for a ReviewRun."""
    __tablename__ = "linter_result"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tool = Column(String(255), nullable=False)
    raw_output = Column(JSONB, nullable=True)

    review_run = relationship("ReviewRun", back_populates="linter_results")


# ---------------------------------------------------------------------------
# RepoMind 2.0 new models
# ---------------------------------------------------------------------------

class RiskAssessment(Base):
    """
    PR-level risk score with explainable factors.

    Every risk score has an explanation — no opaque scores.
    Does NOT include developer performance metrics (per fairness rule).
    """
    __tablename__ = "risk_assessment"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One risk assessment per review run
        index=True,
    )
    # 0-100 risk score
    score = Column(Integer, nullable=False, default=0)
    # critical | high | medium | low
    level = Column(String(20), nullable=False, default="low")
    # Structured risk factor breakdown
    # Example: {"code_complexity": 20, "security_exposure": 30, "test_risk": 15, ...}
    factors = Column(JSONB, nullable=True)
    # Blast radius: {"directly_affected": 2, "potentially_affected": 7, "test_files": 12}
    blast_radius = Column(JSONB, nullable=True)
    # Test impact: {"affected_tests": [...], "missing_tests": [...]}
    test_impact = Column(JSONB, nullable=True)
    # Human-readable summary of why the score is what it is
    summary = Column(Text, nullable=True)
    calculated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    review_run = relationship("ReviewRun", back_populates="risk_assessment")


class Conflict(Base):
    """
    A semantic or mechanical conflict detected during PR review.
    Distinct from ordinary findings — displayed separately in the UI.
    """
    __tablename__ = "conflict"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # mechanical | semantic
    conflict_type = Column(String(50), nullable=False)
    # architecture | api_contract | data_model | security_policy |
    # dependency | test_contract | configuration | git_merge | recent_change
    category = Column(String(100), nullable=False)
    # critical | high | medium | low
    severity = Column(String(50), nullable=False, default="medium")
    title = Column(String(512), nullable=False)
    description = Column(Text, nullable=False)
    # Structured evidence: {"expected": "...", "actual": "...", "sources": [...]}
    evidence = Column(JSONB, nullable=True)
    # open | dismissed | resolved
    status = Column(String(50), nullable=False, default="open")

    review_run = relationship("ReviewRun", back_populates="conflicts")


class FindingEvidence(Base):
    """
    Grounded evidence backing a specific Finding.
    Each finding can have multiple evidence items.
    Evidence status indicates LLM claim reliability.
    """
    __tablename__ = "finding_evidence"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    finding_id = Column(
        Integer,
        ForeignKey("finding.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # supported | unverified | contradicted
    evidence_status = Column(String(50), nullable=False, default="unverified")
    # documentation | source_code | linter | diff | test
    source_type = Column(String(50), nullable=False)
    # File path for the evidence source
    source_path = Column(String(1024), nullable=True)
    # Relevant text excerpt from the evidence source
    source_text = Column(Text, nullable=True)
    # Additional metadata (line numbers, chunk IDs, similarity distance, etc.)
    citation_metadata = Column(JSONB, nullable=True)

    finding = relationship("Finding", back_populates="evidence")


class HumanDecision(Base):
    """
    Records human review decisions on a ReviewRun.
    This is the human approval gate — RepoMind never auto-merges.
    """
    __tablename__ = "human_decision"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # approve | request_changes | dismiss | resolve_finding
    action = Column(String(50), nullable=False)
    # Optional: which finding/conflict this decision applies to
    target_type = Column(String(50), nullable=True)  # finding | conflict | review
    target_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    review_run = relationship("ReviewRun", back_populates="human_decisions")
