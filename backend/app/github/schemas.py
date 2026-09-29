"""
GitHub module schemas — Phase 5.

All schemas follow NFR-001: encrypted_token is NEVER returned in any response schema.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# GitHub Connection
# ---------------------------------------------------------------------------

class GitHubConnectRequest(BaseModel):
    """Request body for POST /repositories/connect.
    The PAT is no longer accepted here. The user's OAuth token is used.
    """
    project_id: int
    github_owner: str
    github_name: str
    default_branch: str = "main"





# ---------------------------------------------------------------------------
# Pull Request
# ---------------------------------------------------------------------------

class PullRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    repository_id: int
    github_number: int
    title: str
    description: Optional[str] = None
    author: Optional[str] = Field(default=None, validation_alias="github_author_login")
    state: str
    source_branch: Optional[str] = None
    target_branch: Optional[str] = None
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
    message: str
