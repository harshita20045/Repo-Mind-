import re

new_func = """def connect_repository(
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
"""

file_path = 'backend/app/github/service.py'
with open(file_path, 'r') as f:
    content = f.read()

# Using regex to find the old connect_repository and replace it.
pattern = re.compile(r"def connect_repository\(.*?\n    return repo, connection\n", re.DOTALL)
content = re.sub(pattern, new_func, content)

with open(file_path, 'w') as f:
    f.write(content)
