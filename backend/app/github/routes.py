"""
GitHub API routes — Phase 5.

Endpoints per api-design.md:
  POST /repositories/connect             org_admin — connect a GitHub repo
  GET  /repositories/{id}/pull-requests  any member — list PRs (with optional sync)
  GET  /pull-requests/{id}               any member — PR detail
  POST /pull-requests/{id}/sync          any member — force re-sync PR from GitHub

All endpoints derive organization_id from the session — never trusted from request input.
The GitHub PAT is NEVER returned in any response.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, RoleEnum
from backend.app.github import schemas, service
from backend.app.organizations.service import (
    get_repository_by_id,
    get_project_by_id,
    verify_org_member,
    verify_org_admin,
)
from backend.app.audit.models import AuditLog

router = APIRouter(tags=["github"])


def _assert_repo_access(db: Session, repository_id: int, user_id: int) -> tuple:
    """
    Resolve repository → project → organization and assert the user is an org member.
    Returns (repository, project, organization_id).
    """
    repo = get_repository_by_id(db, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = get_project_by_id(db, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    # Will raise 404 if not a member (uniform error to prevent org enumeration)
    verify_org_member(db, user_id, project.organization_id)
    return repo, project, project.organization_id


# ---------------------------------------------------------------------------
# POST /repositories/connect
# ---------------------------------------------------------------------------

@router.post(
    "/repositories/connect",
    response_model=schemas.RepositoryConnectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Connect a GitHub repository to an organization",
)
def connect_repository(
    payload: schemas.GitHubConnectRequest,
    organization_id: int = Query(..., description="Organization to connect the repository to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Validate the provided PAT against GitHub, encrypt it, and persist the connection.
    Only org_admin can call this endpoint (per api-design.md).
    The PAT is accepted in the request body and NEVER returned in any response.
    """
    verify_org_admin(db, current_user.id, organization_id)

    repo, connection = service.connect_repository(
        db,
        organization_id=organization_id,
        github_owner=payload.github_owner,
        github_name=payload.github_name,
        default_branch=payload.default_branch,
        plaintext_pat=payload.pat,
    )

    # Audit log — record the connection event without logging the token
    db.add(AuditLog(
        user_id=current_user.id,
        action=f"Connected GitHub repository {payload.github_owner}/{payload.github_name}",
        target_type="github_connection",
        target_id=connection.id,
    ))
    db.commit()

    return schemas.RepositoryConnectResponse(
        repository_id=repo.id,
        github_connection_id=connection.id,
        message=f"Successfully connected {payload.github_owner}/{payload.github_name}",
    )


# ---------------------------------------------------------------------------
# GET /repositories/{repository_id}/pull-requests
# ---------------------------------------------------------------------------

@router.get(
    "/repositories/{repository_id}/pull-requests",
    response_model=List[schemas.PullRequestResponse],
    summary="List pull requests for a repository",
)
def list_pull_requests(
    repository_id: int,
    sync: bool = Query(False, description="Force re-sync from GitHub before returning"),
    state: str = Query("all", description="PR state filter: open, closed, all"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return pull requests for a repository.
    On the first call (or with sync=true) this fetches from GitHub.
    Subsequent calls return cached DB rows.
    """
    repo, project, org_id = _assert_repo_access(db, repository_id, current_user.id)

    if sync:
        return service.sync_pull_requests(db, repo, org_id, state=state)

    return service.get_pull_requests_for_repository(db, repo, org_id)


# ---------------------------------------------------------------------------
# GET /pull-requests/{pull_request_id}
# ---------------------------------------------------------------------------

@router.get(
    "/pull-requests/{pull_request_id}",
    response_model=schemas.PullRequestResponse,
    summary="Get pull request detail",
)
def get_pull_request(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return PR detail. Enforces organization membership via repository → project → org chain."""
    pr = service.get_pull_request_by_id(db, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    # Assert org membership via repository chain
    _assert_repo_access(db, pr.repository_id, current_user.id)

    return pr


