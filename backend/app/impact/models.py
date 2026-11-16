"""
Change Impact & Blast Radius SQLAlchemy models — RepoMind 2.0.

Tables:
  change_impact_analysis — persists change impact, blast radius, breaking changes,
                           subgraph visualizations, and test recommendations.
"""
import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class ChangeImpactAnalysis(Base):
    """
    Persistent record of a change impact and blast radius analysis run.
    Associated with a repository and optionally a pull request and review run.
    """
    __tablename__ = "change_impact_analysis"
    __table_args__ = (
        Index("ix_impact_repo_pr", "repository_id", "pull_request_id"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pull_request_id = Column(
        Integer,
        ForeignKey("pull_request.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    review_run_id = Column(
        Integer,
        ForeignKey("review_run.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    commit_sha = Column(String(255), nullable=True)
    target_branch = Column(String(255), nullable=True, default="main")

    # Overall risk level: low | medium | high | critical
    risk_level = Column(String(50), nullable=False, default="low")

    # Counts
    directly_affected_count = Column(Integer, nullable=False, default=0)
    indirectly_affected_count = Column(Integer, nullable=False, default=0)
    breaking_changes_count = Column(Integer, nullable=False, default=0)

    # Detailed structured outputs
    # List of affected components with tier, relationship, reason, evidence, verification
    affected_components = Column(JSONB, nullable=True)
    # List of breaking change alerts (signature mutations, removed exports, contract breaks)
    breaking_changes = Column(JSONB, nullable=True)
    # Recommended test suites and files with priority
    test_recommendations = Column(JSONB, nullable=True)
    # Interactive graph payload (nodes and edges with styling & Mermaid representation)
    graph_visualization = Column(JSONB, nullable=True)

    summary = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    # Relationships
    repository = relationship("Repository", backref="impact_analyses")
    pull_request = relationship("PullRequest", backref="impact_analyses")
    review_run = relationship("ReviewRun", backref="impact_analyses")
