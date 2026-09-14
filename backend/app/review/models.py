"""
Review SQLAlchemy models — Phase 8.

Tables: review_run, finding, linter_result.
See Docs/03-design/database-design.md for the authoritative schema.

review_run.status lifecycle:
    pending → running → completed
                     → failed
    (cancelled reserved for Phase 13 async-job orchestration)
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
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

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
    # type/category: standards_violation | style | security | performance | general
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
    # status: open | accepted | rejected | resolved
    status = Column(String(50), nullable=False, default="open")

    review_run = relationship("ReviewRun", back_populates="findings")


class LinterResult(Base):
    """
    Raw linter output for a ReviewRun.
    Table created in Phase 8 migration; linter execution logic is Phase 9.
    """
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
