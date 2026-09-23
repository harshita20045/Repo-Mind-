from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db import Base
from datetime import datetime, timezone
from backend.app.auth.models import RoleEnum
from sqlalchemy import Enum as SQLEnum

class Project(Base):
    __tablename__ = "project"
    __table_args__ = {"extend_existing": True}
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    organization = relationship("Organization", backref="projects")
    repositories = relationship("Repository", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class ProjectMember(Base):
    __tablename__ = "project_member"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        SQLEnum(RoleEnum, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=RoleEnum.DEVELOPER,
        nullable=False,
    )

    user = relationship("User", backref="project_memberships")
    project = relationship("Project", back_populates="members")


class Repository(Base):
    __tablename__ = "repository"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), default="github")
    github_repository_id = Column(String(255), unique=True, index=True, nullable=False)
    github_owner = Column(String(255), nullable=False)
    github_name = Column(String(255), nullable=False)
    github_url = Column(String(1024), nullable=True)
    default_branch = Column(String(255), default="main")
    index_status = Column(String(50), default="unindexed")
    last_indexed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", back_populates="repositories")


