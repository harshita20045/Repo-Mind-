import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from backend.app.db import Base


class RoleEnum(str, enum.Enum):
    """
    Enterprise RBAC roles — ordered by privilege level (ascending).

    Existing values (developer, reviewer, team_lead, org_admin) are preserved
    exactly so that existing DB rows and tokens remain valid.

    New roles added for RepoMind 2.0:
      - org_owner:          Highest privilege; can transfer ownership and manage billing.
      - eng_manager:        Engineering health dashboard; no dev performance scores.
      - tech_lead:          PR review, finding management; synonym for team_lead.
      - security_reviewer:  Security finding access; scoped security ops.
      - read_only:          View-only access across permitted resources.
    """
    # --- Existing roles (keep values identical for DB compatibility) ---
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    TEAM_LEAD = "team_lead"         # Legacy alias; tech_lead is preferred for new assignments
    ORG_ADMIN = "org_admin"

    # --- New roles (RepoMind 2.0) ---
    ORG_OWNER = "org_owner"
    ENG_MANAGER = "eng_manager"
    TECH_LEAD = "tech_lead"         # NOTE: same value as TEAM_LEAD — they are aliases
    SECURITY_REVIEWER = "security_reviewer"
    READ_ONLY = "read_only"


class User(Base):
    __tablename__ = "user"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for pending accounts
    invitation_token_hash = Column(String(255), nullable=True, unique=True, index=True)
    invitation_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan")


class Organization(Base):
    __tablename__ = "organization"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan")


class OrganizationMembership(Base):
    __tablename__ = "organization_membership"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(
        SQLEnum(RoleEnum, native_enum=False, values_callable=lambda x: [e.value for e in x]),
        default=RoleEnum.DEVELOPER,
        nullable=False,
    )

    user = relationship("User", back_populates="memberships")
    organization = relationship("Organization", back_populates="memberships")
