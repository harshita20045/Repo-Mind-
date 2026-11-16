"""
Database Models for AI Test Intelligence — RepoMind 2.0.
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class TestScenario(Base):
    """
    Stores structured test scenario recommendations categorized by test type:
    positive, negative, boundary, validation, authentication, authorization,
    integration, and regression.
    """
    __test__ = False
    __tablename__ = "test_scenario"

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

    target_file = Column(String(1024), nullable=False, index=True)
    target_symbol = Column(String(255), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # positive, negative, boundary, validation, authentication, authorization, integration, regression
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    edge_case_notes = Column(Text, nullable=True)
    suggested_assertions = Column(JSONB, nullable=True)  # List[str]
    existing_test_file = Column(String(1024), nullable=True)
    coverage_gap = Column(Boolean, default=True, nullable=False)
    impacted_endpoints = Column(JSONB, nullable=True)  # List[str]
    impacted_services = Column(JSONB, nullable=True)  # List[str]
    priority = Column(String(20), default="medium", nullable=False)  # critical, high, medium, low
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    generated_tests = relationship(
        "GeneratedTestCase",
        back_populates="scenario",
        cascade="all, delete-orphan",
        order_by="GeneratedTestCase.id.asc()",
    )


class GeneratedTestCase(Base):
    """
    Stores concrete test code generated for a scenario and its isolated
    sandbox execution results.
    """
    __tablename__ = "generated_test_case"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_scenario_id = Column(
        Integer,
        ForeignKey("test_scenario.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    language = Column(String(50), nullable=False)  # python, typescript, javascript
    framework = Column(String(50), nullable=False)  # pytest, vitest, jest
    test_file_path = Column(String(1024), nullable=False)
    test_code = Column(Text, nullable=False)
    execution_status = Column(
        String(50),
        default="pending",
        nullable=False,
        index=True,
    )  # pending, running, passed, failed, error
    execution_result = Column(JSONB, nullable=True)
    security_reviewed = Column(Boolean, default=False, nullable=False)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    scenario = relationship("TestScenario", back_populates="generated_tests")
