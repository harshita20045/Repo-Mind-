"""
GitHub integration SQLAlchemy models — Phase 5.

Provides PullRequest and Commit models per database-design.md.
GithubConnection already lives in organizations/models.py (Phase 4).
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from backend.app.db import Base


class GitHubIdentity(Base):
    __tablename__ = "github_identity"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    github_user_id = Column(String(255), unique=True, index=True, nullable=False)
    github_login = Column(String(255), nullable=False)
    connection_status = Column(String(50), default="CONNECTED")
    verified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", backref="github_identity")
    credential = relationship("GitHubCredential", back_populates="identity", uselist=False, cascade="all, delete-orphan")
    repository_accesses = relationship("GitHubRepositoryAccess", back_populates="identity", cascade="all, delete-orphan")


class GitHubCredential(Base):
    __tablename__ = "github_credential"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    github_identity_id = Column(Integer, ForeignKey("github_identity.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    encrypted_access_token = Column(String(1024), nullable=False)
    encrypted_refresh_token = Column(String(1024), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    identity = relationship("GitHubIdentity", back_populates="credential")


class GitHubRepositoryAccess(Base):
    __tablename__ = "github_repository_access"
    __table_args__ = (
        UniqueConstraint("github_identity_id", "repository_id", name="uq_github_repo_access"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    github_identity_id = Column(Integer, ForeignKey("github_identity.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    permission = Column(String(50), nullable=False)
    role_name = Column(String(50), nullable=True)
    verification_status = Column(String(50), default="VERIFIED")
    last_checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    identity = relationship("GitHubIdentity", back_populates="repository_accesses")
    repository = relationship("Repository", backref="github_accesses")



class PullRequest(Base):
    """PR metadata fetched from GitHub, scoped to a repository."""
    __tablename__ = "pull_request"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_number", name="uq_pull_request_repo_number"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    github_pr_id = Column(String(255), unique=True, index=True, nullable=False)
    github_number = Column(Integer, nullable=False)
    github_url = Column(String(1024), nullable=True)
    title = Column(String(512), nullable=False)
    description = Column(String, nullable=True)
    author_user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    github_author_login = Column(String(255), nullable=True)
    
    source_branch = Column(String(255), nullable=True)
    target_branch = Column(String(255), nullable=True)
    base_sha = Column(String(255), nullable=True)
    head_sha = Column(String(255), nullable=True)
    
    draft_status = Column(Integer, default=0) # 0=False, 1=True
    state = Column(String(50), nullable=False, default="open") # open, closed, merged
    mergeable_state = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    
    merged_by = Column(String(255), nullable=True)
    merge_commit_sha = Column(String(255), nullable=True)
    
    synchronization_status = Column(String(50), default="SYNCED")
    last_synced_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    repository = relationship("Repository", backref="pull_requests")
    commits = relationship("PullRequestCommit", back_populates="pull_request", cascade="all, delete-orphan")
    files = relationship("PullRequestFile", back_populates="pull_request", cascade="all, delete-orphan")
    checks = relationship("PullRequestCheck", back_populates="pull_request", cascade="all, delete-orphan")
    github_reviews = relationship("GitHubReview", back_populates="pull_request", cascade="all, delete-orphan")
    github_comments = relationship("GitHubComment", back_populates="pull_request", cascade="all, delete-orphan")
    events = relationship("PullRequestEvent", back_populates="pull_request", cascade="all, delete-orphan")
    ai_analyses = relationship("AIAnalysis", back_populates="pull_request", cascade="all, delete-orphan")
    human_reviews = relationship("HumanReview", back_populates="pull_request", cascade="all, delete-orphan")
    automation_actions = relationship("AutomationAction", back_populates="pull_request", cascade="all, delete-orphan")


class PullRequestCommit(Base):
    """Individual commits associated with a PR — used for re-analysis diffing."""
    __tablename__ = "pull_request_commit"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    sha = Column(String(255), nullable=False)
    author = Column(String(255), nullable=True)
    committer = Column(String(255), nullable=True)
    message = Column(String, nullable=True)
    parent_shas = Column(String, nullable=True)
    github_url = Column(String(1024), nullable=True)
    sequence = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    pull_request = relationship("PullRequest", back_populates="commits")

class PullRequestFile(Base):
    __tablename__ = "pull_request_file"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(255), nullable=True)
    file_path = Column(String(1024), nullable=False)
    status = Column(String(50), nullable=True)
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    changes = Column(Integer, nullable=True)
    previous_filename = Column(String(1024), nullable=True)
    blob_url = Column(String(1024), nullable=True)
    raw_url = Column(String(1024), nullable=True)
    patch_data = Column(String, nullable=True)

    pull_request = relationship("PullRequest", back_populates="files")

class GitHubReview(Base):
    __tablename__ = "github_review"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    github_review_id = Column(String(255), unique=True, index=True, nullable=False)
    github_reviewer_login = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    state = Column(String(50), nullable=False)
    body = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)
    synchronization_status = Column(String(50), default="SYNCED")

    pull_request = relationship("PullRequest", back_populates="github_reviews")

class GitHubComment(Base):
    __tablename__ = "github_comment"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    github_comment_id = Column(String(255), unique=True, index=True, nullable=False)
    github_author_login = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    body = Column(String, nullable=True)
    file_path = Column(String(1024), nullable=True)
    line_number = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)

    pull_request = relationship("PullRequest", back_populates="github_comments")

class PullRequestCheck(Base):
    __tablename__ = "pull_request_check"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    github_check_run_id = Column(String(255), unique=True, index=True, nullable=False)
    check_suite_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    conclusion = Column(String(50), nullable=True)
    head_sha = Column(String(255), nullable=True)
    url = Column(String(1024), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    pull_request = relationship("PullRequest", back_populates="checks")

class PullRequestEvent(Base):
    __tablename__ = "pull_request_event"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(255), nullable=False)
    actor_login = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    payload = Column(String, nullable=True)

    pull_request = relationship("PullRequest", back_populates="events")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(255), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    findings = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    pull_request = relationship("PullRequest", back_populates="ai_analyses")

class HumanReview(Base):
    __tablename__ = "human_review"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(255), nullable=False, index=True)
    reviewer_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)
    comment = Column(String, nullable=True)
    status = Column(String(50), default="PENDING_SYNC")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    pull_request = relationship("PullRequest", back_populates="human_reviews")
    reviewer = relationship("User", backref="human_reviews")

class AutomationAction(Base):
    __tablename__ = "automation_action"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    organization_id = Column(Integer, ForeignKey("organization.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    
    action_type = Column(String(100), nullable=False)
    requested_by_user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    github_identity_id = Column(Integer, ForeignKey("github_identity.id", ondelete="SET NULL"), nullable=True)
    
    status = Column(String(50), nullable=False, default="PENDING")
    attempt_count = Column(Integer, default=0)
    idempotency_key = Column(String(255), unique=True, nullable=True)
    
    github_resource_id = Column(String(255), nullable=True)
    commit_sha = Column(String(255), nullable=True)
    expected_head_sha = Column(String(255), nullable=True)
    
    error_code = Column(String(100), nullable=True)
    error_message = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    pull_request = relationship("PullRequest", back_populates="automation_actions")
    requested_by = relationship("User", backref="requested_actions")
    github_identity = relationship("GitHubIdentity", backref="executed_actions")

class WebhookEvent(Base):
    __tablename__ = "webhook_event"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=True, index=True)
    github_delivery_id = Column(String(255), unique=True, index=True, nullable=False)
    event_type = Column(String(100), nullable=False)
    payload = Column(String, nullable=False)
    processed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

class ProjectMergePolicy(Base):
    __tablename__ = "project_merge_policy"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    require_human_approval = Column(Integer, default=1)
    required_approvals = Column(Integer, default=1)
    require_ai_analysis = Column(Integer, default=1)
    require_ci_success = Column(Integer, default=1)
    auto_merge_enabled = Column(Integer, default=0)
    approval_validity = Column(String(100), default="LATEST_COMMIT_ONLY")
    require_latest_commit_review = Column(Integer, default=1)

    project = relationship("Project", backref="merge_policy")
