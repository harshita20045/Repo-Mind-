import requests, json
from backend.app.db import SessionLocal
from backend.app.organizations.models import Repository
from backend.app.github.models import PullRequest
from backend.app.github.service import get_decrypted_github_token_for_org

db = SessionLocal()
repo = db.query(Repository).filter_by(github_name='repomind-e2e-test-repository').first()
org_id = repo.project.organization_id
token = get_decrypted_github_token_for_org(db, org_id)

headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

base_url = f'https://api.github.com/repos/{repo.github_owner}/{repo.github_name}'
branch = 'phase6c-webhook-test-1790676932'

# 1. Get ref
ref_resp = requests.get(f'{base_url}/git/ref/heads/{branch}', headers=headers).json()
last_commit_sha = ref_resp['object']['sha']

# 2. Get commit
commit_resp = requests.get(f'{base_url}/git/commits/{last_commit_sha}', headers=headers).json()
tree_sha = commit_resp['tree']['sha']

# 3. Create blob
blob_resp = requests.post(f'{base_url}/git/blobs', headers=headers, json={'content': 'Testing sync event 2.', 'encoding': 'utf-8'}).json()
blob_sha = blob_resp['sha']

# 4. Create tree
tree_resp = requests.post(f'{base_url}/git/trees', headers=headers, json={
    'base_tree': tree_sha,
    'tree': [{'path': 'update2.txt', 'mode': '100644', 'type': 'blob', 'sha': blob_sha}]
}).json()
new_tree_sha = tree_resp['sha']

# 5. Create commit
new_commit_resp = requests.post(f'{base_url}/git/commits', headers=headers, json={
    'message': 'Add update2.txt to test synchronize',
    'tree': new_tree_sha,
    'parents': [last_commit_sha]
}).json()
new_commit_sha = new_commit_resp['sha']

# 6. Update ref
update_resp = requests.patch(f'{base_url}/git/refs/heads/{branch}', headers=headers, json={'sha': new_commit_sha})
print('Updated ref:', update_resp.status_code)
print('New commit:', new_commit_sha)
