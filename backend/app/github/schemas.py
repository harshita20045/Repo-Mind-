"""
GitHub module schemas — Phase 5.

All schemas follow NFR-001: encrypted_token is NEVER returned in any response schema.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


# ---------------------------------------------------------------------------
# GitHub Connection
# ---------------------------------------------------------------------------

class GitHubConnectRequest(BaseModel):
    """Request body for POST /repositories/connect.
    The PAT is accepted as plaintext and encrypted server-side before storage.
    It is NEVER stored in plaintext and NEVER returned.
    """
    github_owner: str
    github_name: str
    default_branch: str = "main"
    pat: str  # plaintext PAT accepted here, encrypted before DB write


class GitHubConnectionResponse(BaseModel):
    """Safe response that omits the encrypted token."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    scope: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Pull Request
# ---------------------------------------------------------------------------

class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    repository_id: int
    github_number: int
    title: str
    author: Optional[str] = None
    state: str
    created_at: datetime
    merged_at: Optional[datetime] = None
    additions: Optional[int] = None
    deletions: Optional[int] = None
    files_changed: Optional[int] = None
    head_sha: Optional[str] = None


class PullRequestListResponse(BaseModel):
    pull_requests: List[PullRequestResponse]
    total: int


# ---------------------------------------------------------------------------
# Connect result
# ---------------------------------------------------------------------------

class RepositoryConnectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    repository_id: int
    github_connection_id: int
    message: str
