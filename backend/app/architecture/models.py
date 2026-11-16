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


class ArchitectureRule(Base):
    """
    Architecture rule governing module and layer boundaries, imports, and API flows.
    Can be system-inferred or user-configured.
    """
    __tablename__ = "architecture_rule"
    __table_args__ = (
        UniqueConstraint("repository_id", "rule_code", name="uq_architecture_rule_repo_code"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_code = Column(String(64), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    rule_type = Column(String(50), nullable=False)  # forbidden_dependency, layer_boundary, no_circular_dependencies, api_db_isolation, naming_convention
    source_layer = Column(String(100), nullable=True)  # presentation, frontend, etc.
    target_layer = Column(String(100), nullable=True)  # data_access, backend, etc.
    source_pattern = Column(String(255), nullable=True)  # glob e.g. backend/app/api/**
    target_pattern = Column(String(255), nullable=True)  # glob e.g. backend/app/*/models.py
    severity = Column(String(50), nullable=False, default="high")  # critical, high, medium, low
    suggested_fix = Column(Text, nullable=True)
    is_enabled = Column(Boolean, nullable=False, default=True, index=True)
    is_system_inferred = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    repository = relationship("Repository", backref="architecture_rules")


class ArchitectureAnalysis(Base):
    """
    Snapshot of an architectural audit on a repository or PR run,
    containing the overall health score, inferred pattern, flow analysis, and diagram.
    """
    __tablename__ = "architecture_analysis"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pull_request_id = Column(
        Integer,
        ForeignKey("pull_request.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    health_score = Column(Integer, nullable=False, default=100)
    inferred_pattern = Column(String(100), nullable=False, default="layered_mvc")
    pattern_confidence = Column(Float, nullable=False, default=1.0)
    total_violations = Column(Integer, nullable=False, default=0)
    critical_violations = Column(Integer, nullable=False, default=0)
    circular_dependency_count = Column(Integer, nullable=False, default=0)
    layer_summary = Column(JSONB, nullable=True)
    flow_summary = Column(JSONB, nullable=True)
    mermaid_diagram = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    repository = relationship("Repository", backref="architecture_analyses")
    pull_request = relationship("PullRequest", backref="architecture_analyses")
    violations = relationship("ArchitectureViolation", back_populates="analysis", cascade="all, delete-orphan")


class ArchitectureViolation(Base):
    """
    An individual grounded violation of an architecture rule, cycle, or flow.
    """
    __tablename__ = "architecture_violation"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_id = Column(
        Integer,
        ForeignKey("architecture_analysis.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_id = Column(
        Integer,
        ForeignKey("architecture_rule.id", ondelete="SET NULL"),
        nullable=True,
    )
    rule_code = Column(String(64), nullable=False, index=True)
    violation_type = Column(String(50), nullable=False)  # forbidden_dependency, circular_dependency, leaky_flow, layer_violation
    severity = Column(String(50), nullable=False)  # critical, high, medium, low
    title = Column(String(255), nullable=False)
    explanation = Column(Text, nullable=False)
    suggested_correction = Column(Text, nullable=False)
    source_file = Column(String(1024), nullable=False)
    source_line = Column(Integer, nullable=True)
    target_file = Column(String(1024), nullable=True)
    target_line = Column(Integer, nullable=True)
    evidence = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    analysis = relationship("ArchitectureAnalysis", back_populates="violations")
    rule = relationship("ArchitectureRule")
