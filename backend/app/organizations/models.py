from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db import Base
from datetime import datetime, timezone

class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    organization = relationship("Organization", backref="projects")
    repositories = relationship("Repository", back_populates="project", cascade="all, delete-orphan")

class Repository(Base):
    __tablename__ = "repository"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    github_owner = Column(String(255), nullable=False)
    github_name = Column(String(255), nullable=False)
    default_branch = Column(String(255), default="main")
    index_status = Column(String(50), default="unindexed")
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="repositories")

class GithubConnection(Base):
    __tablename__ = "github_connection"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    encrypted_token = Column(String(1024), nullable=False)
    scope = Column(String(255), default="repo")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", backref="github_connections")
