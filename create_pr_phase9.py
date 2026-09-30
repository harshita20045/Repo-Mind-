import requests, json, time
from backend.app.db import SessionLocal
from backend.app.organizations.models import Repository
from backend.app.github.service import get_decrypted_github_token_for_org

db = SessionLocal()
repo = db.query(Repository).filter_by(github_name='repomind-e2e-test-repository').first()
org_id = repo.project.organization_id
token = get_decrypted_github_token_for_org(db, org_id)
headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
base_url = f'https://api.github.com/repos/{repo.github_owner}/{repo.github_name}'

branch_name = f'phase9-test-{int(time.time())}'
main_ref = requests.get(f'{base_url}/git/ref/heads/main', headers=headers).json()
requests.post(f'{base_url}/git/refs', headers=headers, json={'ref': f'refs/heads/{branch_name}', 'sha': main_ref['object']['sha']})

# Create a realistic vulnerable code file to trigger RAG/LLM findings
bad_code = """
import sqlite3
def get_user(user_id):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    # SQL Injection vulnerability
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    return cursor.fetchone()
"""
blob_resp = requests.post(f'{base_url}/git/blobs', headers=headers, json={'content': bad_code, 'encoding': 'utf-8'}).json()
tree_resp = requests.post(f'{base_url}/git/trees', headers=headers, json={
    'base_tree': main_ref['object']['sha'],
    'tree': [{'path': f'db_utils_{branch_name}.py', 'mode': '100644', 'type': 'blob', 'sha': blob_resp['sha']}]
}).json()
commit_resp = requests.post(f'{base_url}/git/commits', headers=headers, json={
    'message': 'Add vulnerable code for Phase 9',
    'tree': tree_resp['sha'],
    'parents': [main_ref['object']['sha']]
}).json()
requests.patch(f'{base_url}/git/refs/heads/{branch_name}', headers=headers, json={'sha': commit_resp['sha']})

pr_resp = requests.post(f'{base_url}/pulls', headers=headers, json={
    'title': 'Phase 9 Full Review Test',
    'head': branch_name,
    'base': 'main',
    'body': 'Testing full RAG + LLM review flow.'
}).json()
print('Created PR', pr_resp.get('number'))
