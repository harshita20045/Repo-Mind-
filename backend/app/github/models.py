"""
GitHub integration SQLAlchemy models — Phase 5.

Provides PullRequest and Commit models per database-design.md.
GithubConnection already lives in organizations/models.py (Phase 4).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.db import Base


class PullRequest(Base):
    """PR metadata fetched from GitHub, scoped to a repository."""
    __tablename__ = "pull_request"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_number", name="uq_pull_request_repo_number"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    github_number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    author = Column(String(255), nullable=True)
    state = Column(String(50), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    files_changed = Column(Integer, nullable=True)
    # Latest head SHA — used to detect new commits for re-analysis
    head_sha = Column(String(255), nullable=True)

    repository = relationship("Repository", backref="pull_requests")
    commits = relationship(
        "Commit",
        back_populates="pull_request",
        cascade="all, delete-orphan",
    )


class Commit(Base):
    """Individual commits associated with a PR — used for re-analysis diffing."""
    __tablename__ = "commit"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(
        Integer,
        ForeignKey("pull_request.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sha = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    pull_request = relationship("PullRequest", back_populates="commits")
