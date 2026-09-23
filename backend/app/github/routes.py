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
    Validate access using the current user's OAuth token and persist the connection.
    Only org_admin can call this endpoint.
    """
    verify_org_admin(db, current_user.id, organization_id)

    repo = service.connect_repository(
        db,
        user_id=current_user.id,
        organization_id=organization_id,
        project_id=payload.project_id,
        github_owner=payload.github_owner,
        github_name=payload.github_name,
        default_branch=payload.default_branch,
    )

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action=f"Connected GitHub repository {payload.github_owner}/{payload.github_name}",
        target_type="repository",
        target_id=repo.id,
    ))
    db.commit()

    return schemas.RepositoryConnectResponse(
        repository_id=repo.id,
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
        return service.sync_pull_requests(db, repo, current_user.id, state=state)

    return service.get_pull_requests_for_repository(db, repo, current_user.id)


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

@router.post(
    "/repositories/{repository_id}/index",
    response_model=schemas.RepositoryConnectResponse, # Re-using response model for simplicity, or we can just return a dict
    summary="Trigger indexing for a repository",
)
def trigger_index(
    repository_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Reset a repository's index_status to 'unindexed' so the worker picks it up.
    Only allows transitioning if currently 'indexed' or 'failed'.
    """
    repo, project, org_id = _assert_repo_access(db, repository_id, current_user.id)
    verify_org_admin(db, current_user.id, org_id)

    if repo.index_status in ("unindexed", "indexing"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Repository is currently {repo.index_status}. Cannot trigger re-index.",
        )

    repo.index_status = "unindexed"
    db.commit()

    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action=f"Triggered re-indexing for repository {repo.github_owner}/{repo.github_name}",
        target_type="repository",
        target_id=repo.id,
    ))
    db.commit()

    return schemas.RepositoryConnectResponse(
        repository_id=repo.id,
        github_connection_id=0, # N/A here
        message=f"Indexing queued for {repo.github_owner}/{repo.github_name}",
    )

from fastapi import Request
from fastapi.responses import RedirectResponse
import httpx
from urllib.parse import urlencode

# ---------------------------------------------------------------------------
# GET /oauth/login
# ---------------------------------------------------------------------------
@router.get("/oauth/login", summary="Initiate GitHub OAuth flow")
def github_oauth_login(
    current_user: User = Depends(get_current_user),
):
    """
    Redirects the user to GitHub's OAuth authorization page.
    Requires an authenticated user session.
    """
    from backend.app.core.config import settings
    client_id = getattr(settings, "GITHUB_CLIENT_ID", None)
    if not client_id:
        raise HTTPException(status_code=500, detail="GITHUB_CLIENT_ID is not configured")

    state = str(current_user.id) 

    params = {
        "client_id": client_id,
        "scope": "repo read:user", # repo for access, read:user for identity
        "state": state,
    }
    
    url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    return {"url": url}


# ---------------------------------------------------------------------------
# GET /oauth/callback
# ---------------------------------------------------------------------------
@router.get("/oauth/callback", summary="GitHub OAuth callback")
async def github_oauth_callback(
    request: Request,
    code: str,
    state: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), 
):
    """
    Handles the callback from GitHub, exchanges code for token, and upserts GitHubIdentity.
    """
    from backend.app.core.config import settings
    client_id = getattr(settings, "GITHUB_CLIENT_ID", None)
    client_secret = getattr(settings, "GITHUB_CLIENT_SECRET", None)
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="GitHub OAuth credentials are not configured")

    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, headers=headers, data=data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="GitHub did not return an access token")

        user_url = "https://api.github.com/user"
        auth_headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        user_response = await client.get(user_url, headers=auth_headers)
        if user_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user data")
            
        github_user = user_response.json()
        github_user_id = str(github_user["id"])
        github_login = github_user["login"]

        identity = service.upsert_github_identity(
            db, 
            user_id=current_user.id, 
            github_user_id=github_user_id, 
            github_login=github_login,
            access_token=access_token,
            refresh_token=refresh_token
        )
        
        frontend_url = getattr(settings, "FRONTEND_URL", "http://localhost:5173")
        return RedirectResponse(url=f"{frontend_url}/settings/integrations?status=success")

# ---------------------------------------------------------------------------
# POST /pull-requests/{pull_request_id}/sync
# ---------------------------------------------------------------------------

@router.post(
    "/pull-requests/{pull_request_id}/sync",
    response_model=schemas.PullRequestResponse,
    summary="Force a full synchronization of a pull request",
)
def sync_pull_request_details(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Force sync of a pull request's commits, files, reviews, comments, and checks.
    """
    pr = service.get_pull_request_by_id(db, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    _assert_repo_access(db, pr.repository_id, current_user.id)

    # Calling the deep sync logic
    synced_pr = service.sync_pull_request_details(db, pull_request_id, current_user.id)
    return synced_pr


@router.get("/pull-requests/{pull_request_id}/events")
def get_pull_request_events(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the activity history of a pull request."""
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    _assert_repo_access(db, current_user.id, pr.repository_id)

    from backend.app.github.models import PullRequestEvent
    events = (
        db.query(PullRequestEvent)
        .filter(PullRequestEvent.pull_request_id == pull_request_id)
        .order_by(PullRequestEvent.timestamp.desc())
        .all()
    )
    
    # Let's map it into a dict
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "actor_login": e.actor_login,
            "commit_sha": e.commit_sha,
            "timestamp": e.timestamp.isoformat() if e.timestamp else None,
            "payload": e.payload
        } for e in events
    ]

