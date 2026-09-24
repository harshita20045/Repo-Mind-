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
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from backend.app.github.client import GitHubClient, GitHubAPIError, GitHubTransientError
from backend.app.github.encryption import encrypt_token, decrypt_token
from backend.app.github.models import PullRequest, PullRequestCommit
from backend.app.organizations.models import GithubConnection, Repository
from backend.app.organizations.service import get_repository_by_id, get_project_by_id


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def connect_repository(
    db: Session,
    user_id: int,
    organization_id: int,
    project_id: int,
    github_owner: str,
    github_name: str,
    default_branch: str,
) -> Repository:
    from backend.app.organizations.models import Project, Repository
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    from backend.app.github.encryption import decrypt_token
    from fastapi import HTTPException, status

    identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == user_id).first()
    if not identity:
        raise HTTPException(status_code=400, detail="Please connect your GitHub account first.")
    
    credential = db.query(GitHubCredential).filter(GitHubCredential.github_identity_id == identity.id).first()
    if not credential:
        raise HTTPException(status_code=400, detail="GitHub credentials not found.")

    try:
        pat = decrypt_token(credential.encrypted_access_token)
    except ValueError:
        raise HTTPException(status_code=500, detail="Failed to decrypt GitHub credentials.")

    client = GitHubClient(pat)
    try:
        repo_meta = client.validate_repository_access(github_owner, github_name)
    except GitHubAPIError as e:
        if e.status_code in (401, 403):
            raise HTTPException(status_code=422, detail="GitHub token lacks access to repository.")
        if e.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found on GitHub.")
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e.status_code}")
    except GitHubTransientError:
        raise HTTPException(status_code=502, detail="GitHub API is temporarily unavailable.")

    project = db.query(Project).filter(Project.id == project_id, Project.organization_id == organization_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found or does not belong to organization.")

    repo = (
        db.query(Repository)
        .join(Project, Project.id == Repository.project_id)
        .filter(
            Project.organization_id == organization_id,
            Repository.github_owner == github_owner,
            Repository.github_name == github_name,
        )
        .first()
    )


    github_repository_id = str(repo_meta.get("id"))
    default_branch_actual = repo_meta.get("default_branch", default_branch)

    # Register webhook
    from backend.app.core.config import settings
    webhook_url = getattr(settings, "GITHUB_WEBHOOK_URL", None)
    webhook_secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
    
    if webhook_url and webhook_secret:
        try:
            client.register_webhook(github_owner, github_name, webhook_url, webhook_secret)
        except GitHubAPIError as e:
            # We don't fail the entire repository connection if webhook fails,
            # but we could log it or set a status
            pass


    if not repo:
        repo = Repository(
            project_id=project.id,
            github_owner=github_owner,
            github_name=github_name,
            github_repository_id=github_repository_id,
            github_url=repo_meta.get("html_url"),
            default_branch=default_branch_actual,
            index_status="unindexed",
            provider="github",
        )
        db.add(repo)
    else:
        repo.default_branch = default_branch_actual
        repo.github_repository_id = github_repository_id
        repo.github_url = repo_meta.get("html_url")
        repo.index_status = "unindexed"

    db.commit()
    db.refresh(repo)
    return repo


def get_github_repositories(db: Session, organization_id: int, user_id: int) -> List[Dict[str, Any]]:
    from backend.app.organizations.service import verify_org_admin
    verify_org_admin(db, user_id, organization_id)
    pat = get_decrypted_pat_for_user(db, user_id)
    client = GitHubClient(pat)
    try:
        raw_repos = client.list_user_repositories(per_page=100)
    except GitHubAPIError as e:
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e.status_code}")
    except GitHubTransientError:
        raise HTTPException(status_code=502, detail="GitHub API is temporarily unavailable.")
    
    # Filter for repos where the user has admin access
    return [r for r in raw_repos if r.get("permissions", {}).get("admin")]


def get_github_connection_for_org(db: Session, organization_id: int) :
    """Return the GithubConnection for an org, or None if not configured."""
    return (
        db.query(GithubConnection)
        .filter(GithubConnection.organization_id == organization_id)
        .first()
    )


def get_decrypted_pat_for_org(db: Session, organization_id: int) -> str:
    """
    Return the decrypted PAT for an org by finding an org_admin with a linked GitHub Identity.
    Raises HTTPException if no connection is configured or decryption fails.
    NEVER log or re-raise the token value.
    """
    from backend.app.auth.models import OrganizationMembership, User
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    
    credential = (
        db.query(GitHubCredential)
        .join(GitHubIdentity, GitHubIdentity.id == GitHubCredential.github_identity_id)
        .join(User, User.id == GitHubIdentity.user_id)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .filter(
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.role == "org_admin"
        )
        .first()
    )
    
    if not credential:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No GitHub connection configured for this organization.",
        )
    try:
        from backend.app.github.encryption import decrypt_token
        return decrypt_token(credential.encrypted_access_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt GitHub credentials. Contact your org admin.",
        )


# ---------------------------------------------------------------------------
# Pull request synchronization
# ---------------------------------------------------------------------------


def get_decrypted_pat_for_user(db: Session, user_id: int) -> str:
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    from backend.app.github.encryption import decrypt_token
    from fastapi import HTTPException, status
    
    identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == user_id).first()
    if not identity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub account not connected.")
        
    credential = db.query(GitHubCredential).filter(GitHubCredential.github_identity_id == identity.id).first()
    if not credential:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="GitHub credentials not found.")
        
    try:
        return decrypt_token(credential.encrypted_access_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt token.")

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
    user_id: int,
    state: str = "all",
) -> List[PullRequest]:
    """
    Fetch PRs from GitHub for the given repository and upsert into DB.
    Returns the list of PullRequest ORM objects after sync.

    Retry policy: on GitHubTransientError, raise HTTPException 502 (caller
    can retry). Non-retryable errors become 422/404/502 per the error matrix.
    """
    pat = get_decrypted_pat_for_user(db, user_id)
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
                github_pr_id=str(raw.get("id")),
                github_number=pr_number,
                github_url=raw.get("html_url"),
                title=raw.get("title", ""),
                description=raw.get("body", ""),
                github_author_login=raw.get("user", {}).get("login"),
                source_branch=raw.get("head", {}).get("ref"),
                target_branch=raw.get("base", {}).get("ref"),
                base_sha=raw.get("base", {}).get("sha"),
                head_sha=raw.get("head", {}).get("sha"),
                draft_status=1 if raw.get("draft") else 0,
                state=raw.get("state", "open"),
                created_at=created_at,
                updated_at=datetime.fromisoformat(raw["updated_at"].replace("Z", "+00:00")) if raw.get("updated_at") else None,
                closed_at=datetime.fromisoformat(raw["closed_at"].replace("Z", "+00:00")) if raw.get("closed_at") else None,
                merged_at=merged_at,
            )
            db.add(pr)
        else:
            pr.title = raw.get("title", pr.title)
            pr.description = raw.get("body", pr.description)
            pr.state = raw.get("state", pr.state)
            pr.draft_status = 1 if raw.get("draft") else 0
            pr.updated_at = datetime.fromisoformat(raw["updated_at"].replace("Z", "+00:00")) if raw.get("updated_at") else pr.updated_at
            pr.closed_at = datetime.fromisoformat(raw["closed_at"].replace("Z", "+00:00")) if raw.get("closed_at") else pr.closed_at
            pr.merged_at = merged_at
            pr.head_sha = raw.get("head", {}).get("sha", pr.head_sha)
            pr.base_sha = raw.get("base", {}).get("sha", pr.base_sha)
            pr.last_synced_at = datetime.now(timezone.utc)
        result.append(pr)

    db.commit()
    for pr in result:
        db.refresh(pr)
    return result


def get_pull_requests_for_repository(
    db: Session,
    repository: Repository,
    user_id: int,
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
        return sync_pull_requests(db, repository, user_id)
    return existing


def get_pull_request_by_id(db: Session, pr_id: int) -> Optional[PullRequest]:
    return db.query(PullRequest).filter(PullRequest.id == pr_id).first()


def get_pull_request_diff(
    db: Session,
    pr: PullRequest,
    user_id: int,
) -> str:
    """
    Fetch the unified diff for a PR from GitHub.
    The PAT is decrypted from DB, used for the API call, and not retained.
    """
    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    pat = get_decrypted_pat_for_user(db, user_id)
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

def upsert_github_identity(
    db: Session,
    user_id: int,
    github_user_id: str,
    github_login: str,
    access_token: str,
    refresh_token: Optional[str],
):
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    from backend.app.github.encryption import encrypt_token

    identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == user_id).first()
    
    if not identity:
        identity = GitHubIdentity(
            user_id=user_id,
            github_user_id=github_user_id,
            github_login=github_login,
            connection_status="CONNECTED",
            verified_at=datetime.now(timezone.utc)
        )
        db.add(identity)
        db.flush()
    else:
        identity.github_user_id = github_user_id
        identity.github_login = github_login
        identity.connection_status = "CONNECTED"
        identity.verified_at = datetime.now(timezone.utc)

    credential = db.query(GitHubCredential).filter(GitHubCredential.github_identity_id == identity.id).first()
    encrypted_access = encrypt_token(access_token)
    encrypted_refresh = encrypt_token(refresh_token) if refresh_token else None

    if not credential:
        credential = GitHubCredential(
            github_identity_id=identity.id,
            encrypted_access_token=encrypted_access,
            encrypted_refresh_token=encrypted_refresh
        )
        db.add(credential)
    else:
        credential.encrypted_access_token = encrypted_access
        credential.encrypted_refresh_token = encrypted_refresh
        
    db.commit()
    db.refresh(identity)
    return identity

def sync_pull_request_details(db: Session, pr_id: int, user_id: int) -> PullRequest:
    from backend.app.github.models import (
        PullRequestCommit, PullRequestFile, GitHubReview, GitHubComment, PullRequestCheck
    )
    
    pr = get_pull_request_by_id(db, pr_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")
        
    repo = pr.repository
    pat = get_decrypted_pat_for_user(db, user_id)
    client = GitHubClient(pat)
    owner = repo.github_owner
    name = repo.github_name
    number = pr.github_number

    # 1. Sync Commits
    raw_commits = client.list_pull_request_commits(owner, name, number)
    existing_commits = {c.sha: c for c in pr.commits}
    for idx, rc in enumerate(raw_commits):
        sha = rc.get("sha")
        c = existing_commits.get(sha)
        if not c:
            c = PullRequestCommit(
                pull_request_id=pr.id,
                sha=sha,
            )
            db.add(c)
        c.author = rc.get("commit", {}).get("author", {}).get("name")
        c.committer = rc.get("commit", {}).get("committer", {}).get("name")
        c.message = rc.get("commit", {}).get("message")
        parents = rc.get("parents", [])
        c.parent_shas = ",".join([p.get("sha") for p in parents]) if parents else None
        c.github_url = rc.get("html_url")
        c.sequence = idx
        
    # 2. Sync Files
    raw_files = client.get_pull_request_files(owner, name, number)
    existing_files = {f.file_path: f for f in pr.files}
    for rf in raw_files:
        f_path = rf.get("filename")
        f = existing_files.get(f_path)
        if not f:
            f = PullRequestFile(
                pull_request_id=pr.id,
                file_path=f_path,
            )
            db.add(f)
        f.status = rf.get("status")
        f.additions = rf.get("additions")
        f.deletions = rf.get("deletions")
        f.changes = rf.get("changes")
        f.previous_filename = rf.get("previous_filename")
        f.blob_url = rf.get("blob_url")
        f.raw_url = rf.get("raw_url")
        f.patch_data = rf.get("patch")
        
    # 3. Sync Reviews
    raw_reviews = client.list_pull_request_reviews(owner, name, number)
    existing_reviews = {str(r.github_review_id): r for r in pr.github_reviews}
    for rr in raw_reviews:
        r_id = str(rr.get("id"))
        rv = existing_reviews.get(r_id)
        if not rv:
            rv = GitHubReview(
                pull_request_id=pr.id,
                github_review_id=r_id,
            )
            db.add(rv)
        rv.github_reviewer_login = rr.get("user", {}).get("login")
        rv.commit_sha = rr.get("commit_id")
        rv.state = rr.get("state")
        rv.body = rr.get("body")
        if rr.get("submitted_at"):
            rv.submitted_at = datetime.fromisoformat(rr.get("submitted_at").replace("Z", "+00:00"))

    # 4. Sync Comments
    raw_comments = client.list_pull_request_comments(owner, name, number)
    existing_comments = {str(c.github_comment_id): c for c in pr.github_comments}
    for rc in raw_comments:
        c_id = str(rc.get("id"))
        cm = existing_comments.get(c_id)
        if not cm:
            cm = GitHubComment(
                pull_request_id=pr.id,
                github_comment_id=c_id,
            )
            db.add(cm)
        cm.github_author_login = rc.get("user", {}).get("login")
        cm.commit_sha = rc.get("commit_id")
        cm.body = rc.get("body")
        cm.file_path = rc.get("path")
        cm.line_number = rc.get("line")
        
    # 5. Sync Checks (if head_sha is available)
    if pr.head_sha:
        raw_checks = client.get_pull_request_checks(owner, name, pr.head_sha)
        check_runs = raw_checks.get("check_runs", [])
        existing_checks = {str(cr.github_check_run_id): cr for cr in pr.checks}
        for run in check_runs:
            run_id = str(run.get("id"))
            chk = existing_checks.get(run_id)
            if not chk:
                chk = PullRequestCheck(
                    pull_request_id=pr.id,
                    github_check_run_id=run_id,
                )
                db.add(chk)
            chk.name = run.get("name")
            chk.status = run.get("status")
            chk.conclusion = run.get("conclusion")
            chk.head_sha = run.get("head_sha")
            chk.url = run.get("html_url")


    # 6. Sync Events (Phase 11)
    from backend.app.github.models import PullRequestEvent
    raw_events = client.list_pull_request_events(owner, name, number)
    
    # Simple strategy: clear and recreate (or we could deduplicate by a composite of actor/type/timestamp)
    # But GitHub Issue Events don't have stable global IDs in the same way, though they do have 'id'.
    # Actually, GitHub Issue Events *do* have 'id'. Let's check if the payload has an 'id'.
    # We will just parse them. To prevent duplicates, we can look up existing by event type and timestamp,
    # or just wipe and recreate for simplicity during sync.
    # We will use wipe and recreate for events since they are just a log and we don't hold foreign keys to them.
    db.query(PullRequestEvent).filter(PullRequestEvent.pull_request_id == pr.id).delete()
    
    import json
    for revent in raw_events:
        evt = PullRequestEvent(
            pull_request_id=pr.id,
            event_type=revent.get("event"),
            actor_login=revent.get("actor", {}).get("login") if revent.get("actor") else None,
            commit_sha=revent.get("commit_id"),
        )
        created_at_str = revent.get("created_at")
        if created_at_str:
            evt.timestamp = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
            
        # Store a minimal payload if needed
        payload_dict = {
            k: v for k, v in revent.items() 
            if k not in ("actor", "event", "commit_id", "created_at", "url", "issue")
        }
        evt.payload = json.dumps(payload_dict) if payload_dict else None
        
        db.add(evt)
        
    db.commit()

    db.refresh(pr)
    return pr
