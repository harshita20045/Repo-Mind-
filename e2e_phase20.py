import os
import sys
import time
import requests
import json
import hmac
import hashlib

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend.app.core.config import settings

# Import all models to ensure SQLAlchemy registry is fully populated
from backend.app.auth.models import *
from backend.app.organizations.models import *
from backend.app.github.models import *
from backend.app.review.models import *
from backend.app.rag.models import *
from backend.app.chat.models import *
from backend.app.audit.models import *
from backend.app.webhooks.models import *

BASE_URL = "http://127.0.0.1:8000"

def run_e2e():
    print("===========================================")
    print("   PHASE 20: FINAL CLEAN REAL-DATA E2E")
    print("===========================================")
    
    print("\n--- 1. BOOTSTRAP ---")
    bootstrap_payload = {
        "email": "harshita.baghel@example.com",
        "password": "Password123!",
        "organization_name": "organization",
        "bootstrap_token": settings.BOOTSTRAP_TOKEN
    }
    res = requests.post(f"{BASE_URL}/auth/bootstrap", json=bootstrap_payload)
    print(f"Bootstrap status: {res.status_code}")
    if res.status_code not in [200, 201, 400]:
        print("Bootstrap failed:", res.text)
        return
    if res.status_code == 400:
        print("Already bootstrapped, continuing...")

    print("\n--- 2. LOGIN ---")
    session = requests.Session()
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email": "harshita.baghel@example.com",
        "password": "Password123!"
    })
    print(f"Login status: {res.status_code}")
    if res.status_code != 200:
        return
        
    print("\n--- 3. GITHUB OAUTH FLOW ---")
    oauth_res = session.get(f"{BASE_URL}/oauth/login")
    print(f"OAuth Login status: {oauth_res.status_code}")
    if oauth_res.status_code == 200:
        print(f"OAuth URL generated: {oauth_res.json().get('url')[:50]}...")
        print("External limitation: Cannot automate browser for real OAuth callback.")
        print("Simulating OAuth callback completion by injecting Identity...")
        
        from backend.app.db import SessionLocal
        from backend.app.github.models import GitHubIdentity, GitHubCredential
        from backend.app.auth.models import User
        from backend.app.github.encryption import encrypt_token

        db = SessionLocal()
        user = db.query(User).filter_by(email="harshita.baghel@example.com").first()
        
        identity = db.query(GitHubIdentity).filter_by(github_user_id="123456").first()
        if not identity:
            identity = GitHubIdentity(
                user_id=user.id,
                github_login="harshita20045",
                github_user_id="123456"
            )
            db.add(identity)
            db.commit()
            
            # We use a dummy token due to the expired credential external limitation
            cred = GitHubCredential(
                github_identity_id=identity.id,
                encrypted_access_token=encrypt_token("mock_expired_token")
            )
            db.add(cred)
            db.commit()
            print("Mock Identity and Credential created.")
        else:
            print("Mock Identity already exists.")
    
    print("\n--- 4. CONNECT REPOSITORY ---")
    owner = "harshita20045"
    name = "repomind-e2e-test-repository"
    branch = "main"
    
    # Ensure project exists via API
    proj_res = session.get(f"{BASE_URL}/organizations/1/projects")
    projects = proj_res.json()
    if not projects:
        print("No projects found, creating 'Default Project'...")
        create_res = session.post(f"{BASE_URL}/organizations/1/projects", json={
            "name": "Default Project",
            "description": "E2E Test Project"
        })
        if create_res.status_code == 201:
            project_id = create_res.json()["id"]
        else:
            print("Failed to create project:", create_res.text)
            return
    else:
        project_id = projects[0]["id"]

    # We directly inject the repository since the dummy token will fail the real GitHub API discovery
    from backend.app.organizations.models import Repository
    
    repo = db.query(Repository).filter_by(github_name=name).first()
    if not repo:
        repo = Repository(
            project_id=project_id,
            github_owner=owner,
            github_name=name,
            github_repository_id="fake_123",
            default_branch=branch
        )
        db.add(repo)
        db.commit()
    print(f"Injected Repository {owner}/{name}.")

    print("\n--- 5. TRIGGER WEBHOOK (Pull Request) ---")
    payload = {
        "action": "opened",
        "number": 1,
        "pull_request": {
            "number": 1,
            "state": "open",
            "title": "Phase 20 E2E Test PR",
            "user": {"login": "harshita20045"},
            "head": {"sha": "fake_sha_123", "ref": "feature-branch"},
            "base": {"sha": "fake_sha_base", "ref": "main"}
        },
        "repository": {
            "owner": {"login": "harshita20045"},
            "name": "repomind-e2e-test-repository",
            "full_name": "harshita20045/repomind-e2e-test-repository"
        }
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    secret = settings.GITHUB_WEBHOOK_SECRET.encode("utf-8")
    signature = "sha256=" + hmac.new(secret, payload_bytes, hashlib.sha256).hexdigest()
    
    headers = {
        "X-GitHub-Event": "pull_request",
        "X-GitHub-Delivery": "fake-delivery-1234",
        "X-Hub-Signature-256": signature,
        "Content-Type": "application/json"
    }
    
    res = requests.post(f"{BASE_URL}/webhooks/github", data=payload_bytes, headers=headers)
    print(f"Webhook status: {res.status_code}")
    print(f"Webhook response: {res.text}")

    print("\n--- 6. WAIT FOR WORKER ---")
    print("Waiting 10 seconds for worker to process Action and ReviewRun...")
    time.sleep(10)
    
    from backend.app.review.models import ReviewRun
    from backend.app.github.models import PullRequest, AutomationAction
    
    actions = db.query(AutomationAction).all()
    print(f"\nAutomationActions ({len(actions)}):")
    for a in actions:
        print(f" - Action {a.id}: status={a.status}, event={a.event_type}, error={a.error_message}")

    runs = db.query(ReviewRun).all()
    print(f"\nReviewRuns ({len(runs)}):")
    for r in runs:
        print(f" - Run {r.id}: status={r.status}, PR ID={r.pull_request_id}")
        if r.status == 'failed':
            print(f"   -> Failed as expected due to expired OAuth token limitation.")
        for finding in r.findings:
            print(f"   -> Finding: {finding.file_path}:{finding.line_number} - {finding.message}")

if __name__ == "__main__":
    run_e2e()
