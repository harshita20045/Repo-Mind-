"""
GitHub service — Phase 5.

Business logic for GitHub connection management, PAT validation,
and pull-request data synchronization.

Security invariants (per security.md, NFR-001):
- The PAT is encrypted before any DB write.
- The PAT is decrypted only when needed to call the GitHub API.
- The PAT is NEVER logged, NEVER included in exceptions surfaced to clients.
- decrypt_token raises ValueError on corruption — callers must catch and report job failure.
"""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.github.client import GitHubClient, GitHubAPIError, GitHubTransientError
from backend.app.github.encryption import encrypt_token, decrypt_token
from backend.app.github.models import PullRequest, Commit
from backend.app.organizations.models import GithubConnection, Repository
from backend.app.organizations.service import get_repository_by_id, get_project_by_id


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def connect_repository(
    db: Session,
    organization_id: int,
    github_owner: str,
    github_name: str,
    default_branch: str,
    plaintext_pat: str,
) -> tuple[Repository, GithubConnection]:
    """
    Validate the PAT against GitHub, encrypt it, persist GithubConnection
    and ensure the Repository row exists.

    Returns (repository, github_connection).
    Raises HTTPException on invalid PAT or inaccessible repository.
    """
    # 1. Validate PAT against GitHub before storing anything
    client = GitHubClient(plaintext_pat)
    try:
        repo_meta = client.validate_repository_access(github_owner, github_name)
    except GitHubAPIError as e:
        if e.status_code in (401, 403):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="GitHub token is invalid or lacks access to the specified repository.",
            )
        if e.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {github_owner}/{github_name} not found on GitHub.",
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error: {e.status_code}",
        )
    except GitHubTransientError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub API is temporarily unavailable. Please retry.",
        )

    # 2. Encrypt the PAT before touching the database
    encrypted = encrypt_token(plaintext_pat)

    # 3. Upsert GithubConnection (one per org is the MVP design)
    connection = (
        db.query(GithubConnection)
        .filter(GithubConnection.organization_id == organization_id)
        .first()
    )
    if connection:
        connection.encrypted_token = encrypted
        connection.scope = "repo"
    else:
        connection = GithubConnection(
            organization_id=organization_id,
            encrypted_token=encrypted,
            scope="repo",
        )
        db.add(connection)
    db.flush()

    # 4. Find the repository row linked to this org (via project)
    # For MVP: we create/update the repository record using GitHub metadata
    default_branch_actual = repo_meta.get("default_branch", default_branch)

    # We need a project to hang the repository under — use the first project for the org
    # (caller is org_admin so they must have a project, or we raise 400)
    from backend.app.organizations.models import Project
    project = db.query(Project).filter(Project.organization_id == organization_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Create a project first before connecting a repository.",
        )

    # Check for existing repository
    repo = (
        db.query(Repository)
        .filter(
            Repository.project_id == project.id,
            Repository.github_owner == github_owner,
            Repository.github_name == github_name,
        )
        .first()
    )
    if not repo:
        repo = Repository(
            project_id=project.id,
            github_owner=github_owner,
            github_name=github_name,
            default_branch=default_branch_actual,
            index_status="unindexed",
        )
        db.add(repo)
    else:
        repo.default_branch = default_branch_actual
        repo.index_status = "unindexed"  # Reset so re-indexing can be triggered

    db.commit()
    db.refresh(repo)
    db.refresh(connection)
    return repo, connection


def get_github_connection_for_org(db: Session, organization_id: int) -> Optional[GithubConnection]:
    """Return the GithubConnection for an org, or None if not configured."""
    return (
        db.query(GithubConnection)
        .filter(GithubConnection.organization_id == organization_id)
        .first()
    )


def get_decrypted_pat_for_org(db: Session, organization_id: int) -> str:
    """
    Return the decrypted PAT for an org.
    Raises HTTPException if no connection is configured or decryption fails.
    NEVER log or re-raise the token value.
    """
    conn = get_github_connection_for_org(db, organization_id)
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GitHub connection configured for this organization.",
        )
    try:
        return decrypt_token(conn.encrypted_token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt GitHub credentials. Contact your org admin.",
        )


# ---------------------------------------------------------------------------
# Pull request synchronization
# ---------------------------------------------------------------------------

def _get_org_id_for_repository(db: Session, repository_id: int) -> int:
    """Walk repository → project → organization_id."""
    repo = get_repository_by_id(db, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = get_project_by_id(db, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.organization_id


def sync_pull_requests(
    db: Session,
    repository: Repository,
    organization_id: int,
    state: str = "all",
) -> List[PullRequest]:
    """
    Fetch PRs from GitHub for the given repository and upsert into DB.
    Returns the list of PullRequest ORM objects after sync.

    Retry policy: on GitHubTransientError, raise HTTPException 502 (caller
    can retry). Non-retryable errors become 422/404/502 per the error matrix.
    """
    pat = get_decrypted_pat_for_org(db, organization_id)
    client = GitHubClient(pat)

    try:
        raw_prs = client.list_pull_requests(
            repository.github_owner,
            repository.github_name,
            state=state,
        )
    except GitHubAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API error fetching pull requests: {e.status_code}",
        )
    except GitHubTransientError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GitHub API is temporarily unavailable. Please retry.",
        )

    result: List[PullRequest] = []
    for raw in raw_prs:
        pr_number = raw["number"]
        # Upsert by (repository_id, github_number)
        pr = (
            db.query(PullRequest)
            .filter(
                PullRequest.repository_id == repository.id,
                PullRequest.github_number == pr_number,
            )
            .first()
        )
        created_at_str = raw.get("created_at") or ""
        created_at = (
            datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            if created_at_str
            else datetime.now(timezone.utc)
        )
        merged_at = None
        if raw.get("merged_at"):
            merged_at = datetime.fromisoformat(raw["merged_at"].replace("Z", "+00:00"))

        if not pr:
            pr = PullRequest(
                repository_id=repository.id,
                github_number=pr_number,
                title=raw.get("title", ""),
                author=raw.get("user", {}).get("login"),
                state=raw.get("state", "open"),
                created_at=created_at,
                merged_at=merged_at,
                additions=raw.get("additions"),
                deletions=raw.get("deletions"),
                files_changed=raw.get("changed_files"),
                head_sha=raw.get("head", {}).get("sha"),
            )
            db.add(pr)
        else:
            pr.title = raw.get("title", pr.title)
            pr.state = raw.get("state", pr.state)
            pr.merged_at = merged_at
            pr.head_sha = raw.get("head", {}).get("sha", pr.head_sha)
        result.append(pr)

    db.commit()
    for pr in result:
        db.refresh(pr)
    return result


def get_pull_requests_for_repository(
    db: Session,
    repository: Repository,
    organization_id: int,
) -> List[PullRequest]:
    """
    Return cached PRs from DB, triggering a sync if no PRs exist yet.
    """
    existing = (
        db.query(PullRequest)
        .filter(PullRequest.repository_id == repository.id)
        .all()
    )
    if not existing:
        # Lazy first-time sync
        return sync_pull_requests(db, repository, organization_id)
    return existing


def get_pull_request_by_id(db: Session, pr_id: int) -> Optional[PullRequest]:
    return db.query(PullRequest).filter(PullRequest.id == pr_id).first()


def get_pull_request_diff(
    db: Session,
    pr: PullRequest,
    organization_id: int,
) -> str:
    """
    Fetch the unified diff for a PR from GitHub.
    The PAT is decrypted from DB, used for the API call, and not retained.
    """
    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    pat = get_decrypted_pat_for_org(db, organization_id)
    client = GitHubClient(pat)
    try:
        return client.get_pull_request_diff(
            repo.github_owner,
            repo.github_name,
            pr.github_number,
        )
    except GitHubAPIError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch PR diff: {e.status_code}",
        )
