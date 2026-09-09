from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.auth.models import User
from backend.app.auth.dependencies import get_current_user
from backend.app.github.models import PullRequest

db = SessionLocal()
user = db.query(User).get(95)

def override_get_current_user():
    return user

app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)
response = client.get('/repositories/14/pull-requests?sync=true')
print('API Status:', response.status_code)
if response.status_code == 200:
    data = response.json()
    print('API Response Length:', len(data))
    if data:
        print('First PR API Data:', data[0])
else:
    print('API Error:', response.text)

prs = db.query(PullRequest).all()
print('\n--- PRs from DB ---')
for p in prs:
    pr_num = getattr(p, "github_pr_id", getattr(p, "pr_number", getattr(p, "number", "unknown")))
    print(f'PR ID: {p.id}, GitHub PR ID/Number: {pr_num}, Title: {p.title}, State: {p.state}, URL: {getattr(p, "html_url", getattr(p, "url", "none"))}')
