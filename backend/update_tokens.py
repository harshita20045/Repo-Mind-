import re

# Update service.py
file_path = 'backend/app/github/service.py'
with open(file_path, 'r') as f:
    content = f.read()

helper = """
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

"""

# Prepend the helper before sync_pull_requests
content = content.replace("def _get_org_id_for_repository", helper + "def _get_org_id_for_repository")

# Change signatures
content = content.replace("sync_pull_requests(\n    db: Session,\n    repository: Repository,\n    organization_id: int,\n    state: str = \"all\",\n)", "sync_pull_requests(\n    db: Session,\n    repository: Repository,\n    user_id: int,\n    state: str = \"all\",\n)")
content = content.replace("pat = get_decrypted_pat_for_org(db, organization_id)", "pat = get_decrypted_pat_for_user(db, user_id)")

content = content.replace("get_pull_requests_for_repository(\n    db: Session,\n    repository: Repository,\n    organization_id: int,\n)", "get_pull_requests_for_repository(\n    db: Session,\n    repository: Repository,\n    user_id: int,\n)")
content = content.replace("return sync_pull_requests(db, repository, organization_id)", "return sync_pull_requests(db, repository, user_id)")

content = content.replace("get_pull_request_diff(\n    db: Session,\n    pr: PullRequest,\n    organization_id: int,\n)", "get_pull_request_diff(\n    db: Session,\n    pr: PullRequest,\n    user_id: int,\n)")

with open(file_path, 'w') as f:
    f.write(content)


# Update routes.py
routes_path = 'backend/app/github/routes.py'
with open(routes_path, 'r') as f:
    routes = f.read()

routes = routes.replace("return service.sync_pull_requests(db, repo, org_id, state=state)", "return service.sync_pull_requests(db, repo, current_user.id, state=state)")
routes = routes.replace("return service.get_pull_requests_for_repository(db, repo, org_id)", "return service.get_pull_requests_for_repository(db, repo, current_user.id)")

with open(routes_path, 'w') as f:
    f.write(routes)
