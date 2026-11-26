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
from backend.app.organizations.models import Repository


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

    # 15-attribute structured decision framework (RepoMind 2.0)
    decision_category = Column(String(100), nullable=False, default="architecture", index=True)
    decision_type = Column(String(50), nullable=False, default="synthetic_demo")  # documented | inferred | synthetic_demo
    original_problem = Column(Text, nullable=True)
    business_context = Column(Text, nullable=True)
    technical_context = Column(Text, nullable=True)
    advantages = Column(JSONB, nullable=True)  # List[str]
    trade_offs = Column(JSONB, nullable=True)  # List[str]
    related_prs = Column(JSONB, nullable=True)  # List[str] e.g. ["#1", "#2"]
    current_relevance = Column(String(100), nullable=False, default="active")  # active | superseded | critical

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


class HistoricalEvolutionMilestone(Base):
    """
    Chronological engineering evolution milestone spanning:
    Architecture, API, Database, Dependency, Security, and Performance evolutions.
    """
    __tablename__ = "historical_evolution_milestone"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    milestone_date = Column(DateTime(timezone=True), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # architecture | api | database | dependency | security | performance
    module_name = Column(String(100), nullable=False, index=True)  # auth | orders | users | core | etc.
    pr_id = Column(Integer, ForeignKey("pull_request.id", ondelete="SET NULL"), nullable=True)
    commit_sha = Column(String(40), nullable=True)
    previous_approach = Column(Text, nullable=True)
    current_approach = Column(Text, nullable=True)
    problem_solved = Column(Text, nullable=False)
    reason_for_change = Column(Text, nullable=False)
    business_context = Column(Text, nullable=True)
    technical_explanation = Column(Text, nullable=True)
    affected_files = Column(JSONB, nullable=True)  # List[str]
    affected_modules = Column(JSONB, nullable=True)  # List[str]
    dependencies_impacted = Column(JSONB, nullable=True)  # List[str]
    consequences = Column(Text, nullable=True)
    lessons_learned = Column(Text, nullable=True)
    is_synthetic_demo = Column(Boolean, nullable=False, default=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    repository = relationship("Repository", backref="evolution_milestones")


class HistoricalBugLesson(Base):
    """
    Structured historical bug, incident, root cause, resolution, and preventative guidance.
    Surfaced when developers modify related code modules or touch similar patterns.
    """
    __tablename__ = "historical_bug_lesson"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_title = Column(String(255), nullable=False)
    issue_category = Column(String(100), nullable=False, index=True)  # concurrency | validation | security | database | api_contract
    module_name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    root_cause = Column(Text, nullable=True)
    related_pr_number = Column(Integer, nullable=True)
    related_commit_sha = Column(String(40), nullable=True)
    files_involved = Column(JSONB, nullable=True)  # List[str]
    resolution_details = Column(Text, nullable=False)
    tests_added = Column(JSONB, nullable=True)  # List[str]
    prevention_recommendations = Column(Text, nullable=False)
    warning_triggers = Column(JSONB, nullable=True)  # List[str]
    occurred_at = Column(DateTime(timezone=True), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    repository = relationship("Repository", backref="bug_lessons")


