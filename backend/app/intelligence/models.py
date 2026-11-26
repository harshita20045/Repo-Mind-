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


class CodeGraphNode(Base):
    """
    Persistent node representing an architectural entity in the repository:
    file, module, class, function, method, API endpoint, service, or database model.
    """
    __tablename__ = "code_graph_node"
    __table_args__ = (
        UniqueConstraint("repository_id", "node_key", name="uq_code_graph_node_repo_key"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_key = Column(String(512), nullable=False, index=True)
    node_type = Column(String(50), nullable=False, index=True)  # file, module, class, function, method, api_endpoint, service, db_model
    name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(1024), nullable=False, index=True)
    start_line = Column(Integer, nullable=True)
    end_line = Column(Integer, nullable=True)
    metadata_json = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    repository = relationship("Repository", backref="code_nodes")


class CodeGraphEdge(Base):
    """
    Directed relationship between architectural entities:
    contains, imports, calls, inherits, exposes, interacts_with, depends_on.
    """
    __tablename__ = "code_graph_edge"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id = Column(
        Integer,
        ForeignKey("code_graph_node.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_node_id = Column(
        Integer,
        ForeignKey("code_graph_node.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    relation_type = Column(String(50), nullable=False, index=True)  # contains, imports, calls, inherits, exposes, interacts_with, depends_on
    weight = Column(Float, nullable=False, default=1.0)
    metadata_json = Column(JSONB, nullable=True)

    source_node = relationship("CodeGraphNode", foreign_keys=[source_node_id], backref="outgoing_edges")
    target_node = relationship("CodeGraphNode", foreign_keys=[target_node_id], backref="incoming_edges")


class PackageDependency(Base):
    """
    Extracted external package dependency (from requirements.txt, pyproject.toml, package.json, etc.).
    """
    __tablename__ = "package_dependency"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ecosystem = Column(String(50), nullable=False, index=True)  # pypi, npm, cargo, go
    package_name = Column(String(255), nullable=False, index=True)
    version_spec = Column(String(100), nullable=True)
    is_dev = Column(Boolean, nullable=False, default=False)
    file_path = Column(String(1024), nullable=True)


class RepositoryScanSummary(Base):
    """
    Aggregated high-level repository scan summary, language stats, framework detections,
    and generated architecture diagram.
    """
    __tablename__ = "repository_scan_summary"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    primary_language = Column(String(50), nullable=True)
    languages = Column(JSONB, nullable=True)
    frameworks = Column(JSONB, nullable=True)
    entry_points = Column(JSONB, nullable=True)
    stats = Column(JSONB, nullable=True)
    architecture_summary = Column(Text, nullable=True)
    mermaid_diagram = Column(Text, nullable=True)
    scanned_commit_sha = Column(String(40), nullable=True)
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )

    repository = relationship("Repository", backref="scan_summary", uselist=False)
