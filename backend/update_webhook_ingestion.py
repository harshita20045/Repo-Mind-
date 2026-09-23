import re

file_path = 'backend/app/webhooks/routes.py'
with open(file_path, 'r') as f:
    content = f.read()

upsert_logic = """
def _get_system_user_id_for_repo(db: Session, repository_id: int) -> Optional[int]:
    from backend.app.organizations.models import Repository, Project
    from backend.app.auth.models import OrganizationMembership, User
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    
    res = (
        db.query(User.id)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .join(Project, Project.organization_id == OrganizationMembership.organization_id)
        .join(Repository, Repository.project_id == Project.id)
        .join(GitHubIdentity, GitHubIdentity.user_id == User.id)
        .join(GitHubCredential, GitHubCredential.github_identity_id == GitHubIdentity.id)
        .filter(Repository.id == repository_id, OrganizationMembership.role == 'org_admin')
        .first()
    )
    return res[0] if res else None

def _upsert_pr_from_webhook(db: Session, repository_id: int, pr_payload: dict) -> PullRequest:
    from datetime import datetime
    
    pr_github_number = pr_payload.get("number")
    pr = (
        db.query(PullRequest)
        .filter(
            PullRequest.repository_id == repository_id,
            PullRequest.github_number == pr_github_number,
        )
        .first()
    )
    
    def parse_dt(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

    if not pr:
        pr = PullRequest(
            repository_id=repository_id,
            github_pr_id=str(pr_payload.get("id")),
            github_number=pr_github_number,
        )
        db.add(pr)
        
    pr.title = pr_payload.get("title", "")[:512]
    pr.description = pr_payload.get("body")
    pr.github_url = pr_payload.get("html_url")
    pr.state = pr_payload.get("state", "open")
    pr.github_author_login = pr_payload.get("user", {}).get("login")
    pr.source_branch = pr_payload.get("head", {}).get("ref")
    pr.target_branch = pr_payload.get("base", {}).get("ref")
    pr.head_sha = pr_payload.get("head", {}).get("sha")
    pr.base_sha = pr_payload.get("base", {}).get("sha")
    
    created_at = pr_payload.get("created_at")
    if created_at:
        pr.created_at = parse_dt(created_at)
    else:
        pr.created_at = datetime.utcnow()
        
    pr.updated_at = parse_dt(pr_payload.get("updated_at"))
    pr.merged_at = parse_dt(pr_payload.get("merged_at"))
    pr.closed_at = parse_dt(pr_payload.get("closed_at"))
    
    db.commit()
    db.refresh(pr)
    
    # Try deep sync if a system user exists
    sys_user_id = _get_system_user_id_for_repo(db, repository_id)
    if sys_user_id:
        from backend.app.github.service import sync_pull_request_details
        try:
            pr = sync_pull_request_details(db, pr.id, sys_user_id)
        except Exception as e:
            logger.error(f"Failed to deep sync PR {pr.id} during webhook ingestion: {e}")
            
    return pr

def _enqueue_review(db: Session, repository_id: int, pr_payload: dict) -> Optional[ReviewRun]:
    \"\"\"
    Upsert the PullRequest from payload and create a pending ReviewRun.
    \"\"\"
    pr_github_number = pr_payload.get("number")
    pr = _upsert_pr_from_webhook(db, repository_id, pr_payload)
"""

# Replace _enqueue_review definition and update routes calls
content = re.sub(
    r'def _enqueue_review\(db: Session, repository_id: int, pr_github_number: int\) -> Optional\[ReviewRun\]:.*?existing = \(',
    upsert_logic + '\n    existing = (',
    content,
    flags=re.DOTALL
)

# Replace the call in github_webhook
content = content.replace(
    'review_run = _enqueue_review(db, repository_id, pr_number)',
    'review_run = _enqueue_review(db, repository_id, payload.get("pull_request", {}))'
)

with open(file_path, 'w') as f:
    f.write(content)
