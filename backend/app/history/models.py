"""
SQLAlchemy models for Historical Code Intelligence — RepoMind 2.0.

Tables:
  architecture_decision_record  — Indexed Architecture Decision Records (ADRs) parsed from repository docs
  historical_commit_record      — Mined commit history, touched files, bugfix flags, and decision rationale
  recurring_issue_hotspot       — Aggregated high-churn bug modules and recurring review finding hotspots
"""
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class ArchitectureDecisionRecord(Base):
    """
    Structured Architecture Decision Record (ADR) parsed and indexed from repository documentation.
    Governs architectural constraints, technology choices, and design patterns.
    """
    __tablename__ = "architecture_decision_record"
    __table_args__ = (
        UniqueConstraint("repository_id", "adr_number", name="uq_adr_repo_number"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    adr_number = Column(String(50), nullable=False, index=True)  # e.g., "ADR-001"
    title = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False, default="Confirmed")  # Confirmed, Superseded, Proposed, Accepted
    context = Column(Text, nullable=True)
    decision = Column(Text, nullable=False)
    options_considered = Column(JSONB, nullable=True)  # List[str]
    reason = Column(Text, nullable=True)
    consequences = Column(Text, nullable=True)
    superseded_alternative = Column(Text, nullable=True)
    file_source = Column(String(1024), nullable=True)  # e.g. "docs/02-architecture/architecture-decisions.md"
    affected_modules = Column(JSONB, nullable=True)  # List[str] of file/dir patterns governed
    date = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    repository = relationship("Repository", backref="adrs")


class HistoricalCommitRecord(Base):
    """
    Mined commit history entry with file-level modifications, bugfix categorization,
    and extracted original engineering decision rationale.
    """
    __tablename__ = "historical_commit_record"
    __table_args__ = (
        UniqueConstraint("repository_id", "commit_sha", name="uq_historical_commit_repo_sha"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    commit_sha = Column(String(40), nullable=False, index=True)
    author = Column(String(255), nullable=True)
    committer = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    committed_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_bugfix = Column(Boolean, nullable=False, default=False, index=True)
    files_changed = Column(JSONB, nullable=True)  # List[{"path": str, "status": str, "additions": int, "deletions": int}]
    linked_issues = Column(JSONB, nullable=True)  # List[str] e.g. ["#42", "PROJ-101"]
    original_decision_rationale = Column(Text, nullable=True)  # Extracted explanation of why the change was made

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    repository = relationship("Repository", backref="historical_commits")


class RecurringIssueHotspot(Base):
    """
    Aggregated high-churn bug hotspot identified through historical commit analysis
    and repeated review findings.
    """
    __tablename__ = "recurring_issue_hotspot"
    __table_args__ = (
        UniqueConstraint("repository_id", "file_path", name="uq_hotspot_repo_filepath"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_path = Column(String(1024), nullable=False, index=True)
    total_commits = Column(Integer, nullable=False, default=0)
    bugfix_commits_count = Column(Integer, nullable=False, default=0)
    recurring_findings_count = Column(Integer, nullable=False, default=0)
    hotspot_score = Column(Float, nullable=False, default=0.0)  # 0.0 - 100.0 score
    severity = Column(String(50), nullable=False, default="low")  # critical, high, medium, low
    recurring_finding_categories = Column(JSONB, nullable=True)  # {"security": 3, "correctness": 2}
    historical_references = Column(JSONB, nullable=True)  # List[{"ref": str, "date": str, "reason": str}]
    last_bugfix_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        onupdate=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    repository = relationship("Repository", backref="recurring_hotspots")

