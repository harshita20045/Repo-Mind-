"""
SQLAlchemy models for Developer Onboarding & Codebase Blueprint — RepoMind 2.0.

Tables:
  repository_blueprint      — Cached architectural mental model and role-based learning tracks,
                              tied to the analyzed commit SHA of the indexed repository snapshot.
  user_onboarding_progress  — Private, per-user checklist and developer scratchpad.
                              STRICT PRIVACY: Never exposed for developer scoring or monitoring.
"""
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class RepositoryBlueprint(Base):
    """
    Cached architecture map, reading order, and milestones for a repository snapshot.
    Associated with the indexed repository's commit SHA.
    """
    __tablename__ = "repository_blueprint"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    # The commit SHA of the repository snapshot that was analyzed
    analyzed_commit_sha = Column(String(40), nullable=False, index=True)

    # Concurrency and generation lifecycle status: 'pending' | 'ready' | 'failed'
    status = Column(String(20), nullable=False, default="pending", index=True)
    retry_count = Column(Integer, nullable=False, default=0)
    generation_started_at = Column(DateTime(timezone=True), nullable=True)
    generation_completed_at = Column(DateTime(timezone=True), nullable=True)
    generation_error = Column(Text, nullable=True)

    # Core architectural overview
    summary = Column(Text, nullable=True)
    architecture_pattern = Column(String(100), nullable=True)  # e.g., "Modular Monolith", "Clean Architecture"
    subsystems = Column(JSONB, nullable=True)                 # [{ name, path, purpose, key_files }]
    request_flow = Column(JSONB, nullable=True)               # [{ step_number, layer, file, symbol, description }]
    
    # Role-based tracks: { backend: { reading_order: [...], milestones: [...] }, frontend: {...}, fullstack: {...} }
    tracks = Column(JSONB, nullable=True)

    # Blast radius & safe entry points
    caution_zones = Column(JSONB, nullable=True)              # [{ path, risk_level, reason }]
    safe_starter_areas = Column(JSONB, nullable=True)         # [{ area, description, starter_ideas }]
    mermaid_diagram = Column(Text, nullable=True)             # Valid Mermaid flowchart

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    repository = relationship("Repository", backref="blueprint")


class UserOnboardingProgress(Base):
    """
    Private developer progress on onboarding milestones for a given repository.
    Anti-surveillance invariant:
    - Belongs strictly to (user_id, repository_id).
    - Readable and writable ONLY by the owning user.
    - Zero manager aggregation or performance scoring permitted.
    """
    __tablename__ = "user_onboarding_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "repository_id", name="uq_user_repo_onboarding"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    active_track = Column(String(50), nullable=False, default="backend")  # backend | frontend | fullstack
    completed_milestones = Column(JSONB, nullable=False, default=list)    # list of completed milestone IDs
    notes = Column(Text, nullable=True)                                   # Private developer scratchpad

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    user = relationship("User", backref="onboarding_progresses")
    repository = relationship("Repository", backref="user_onboarding_progresses")

