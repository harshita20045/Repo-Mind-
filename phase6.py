import sys
import os
import time
import requests

sys.path.append(os.path.abspath('.'))

from backend.app.db import SessionLocal
from backend.app.organizations.models import Repository
from backend.app.github.service import get_decrypted_github_token_for_user
from backend.app.github.client import GitHubClient
from backend.app.core.config import settings

def main():
    db = SessionLocal()
    # Get user 1
    user_id = 1
    repo = db.query(Repository).filter(Repository.id == 2).first()
    
    if not repo:
        print("Repo ID 2 not found!")
        return

    token = get_decrypted_github_token_for_user(db, user_id)
    client = GitHubClient(token)
    
    owner = repo.github_owner
    name = repo.github_name
    webhook_url = settings.GITHUB_WEBHOOK_URL
    webhook_secret = settings.GITHUB_WEBHOOK_SECRET
    
    if not webhook_url or not webhook_secret:
        print("Missing webhook url or secret in settings.")
        return

    # PHASE 6B: Register Webhook
    print(f"Registering webhook for {owner}/{name} to {webhook_url}...")
    try:
        client.register_webhook(owner, name, webhook_url, webhook_secret)
        print("Webhook registered successfully!")
    except Exception as e:
        print(f"Failed to register webhook (or already exists): {e}")

    # GitHub API base and headers
    gh_headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    gh_base = "https://api.github.com"
    
    # Check webhook status via GitHub API
    webhooks_resp = requests.get(f"{gh_base}/repos/{owner}/{name}/hooks", headers=gh_headers)
    webhooks = webhooks_resp.json()
    active = any(h.get("active") and h.get("config", {}).get("url") == webhook_url for h in webhooks)
    print(f"Webhook active status: {active}")

    # PHASE 6C: Create controlled real PR
    # 1. Get default branch SHA
    print("Creating a new branch and PR...")
    ref_data = requests.get(f"{gh_base}/repos/{owner}/{name}/git/ref/heads/{repo.default_branch}", headers=gh_headers).json()
    base_sha = ref_data["object"]["sha"]
    
    branch_name = f"e2e-test-webhook-{int(time.time())}"
    # Create branch
    requests.post(f"{gh_base}/repos/{owner}/{name}/git/refs", json={
        "ref": f"refs/heads/{branch_name}",
        "sha": base_sha
    }, headers=gh_headers)
    
    # Create a dummy commit (create a file)
    requests.put(f"{gh_base}/repos/{owner}/{name}/contents/test_webhook_{int(time.time())}.txt", json={
        "message": "Add test webhook file",
        "content": "SGVsbG8gd29ybGQ=", # "Hello world" base64
        "branch": branch_name
    }, headers=gh_headers)
    
    # Open PR
    pr_res = requests.post(f"{gh_base}/repos/{owner}/{name}/pulls", json={
        "title": "E2E Webhook Test PR",
        "body": "This PR is created automatically to test the RepoMind webhook.",
        "head": branch_name,
        "base": repo.default_branch
    }, headers=gh_headers).json()
    pr_number = pr_res["number"]
    print(f"Created PR #{pr_number}")
    
    # Wait a few seconds for webhook to arrive
    print("Waiting 5 seconds for webhook delivery...")
    time.sleep(5)
    
    # Check RepoMind DB for PR and ReviewRun
    from backend.app.github.models import PullRequest
    from backend.app.review.models import ReviewRun
    from backend.app.webhooks.models import WebhookEvent
    
    pr = db.query(PullRequest).filter(PullRequest.repository_id == 2, PullRequest.github_number == pr_number).first()
    if pr:
        print(f"PR correctly synced in DB. PR ID: {pr.id}")
        run = db.query(ReviewRun).filter(ReviewRun.pull_request_id == pr.id).order_by(ReviewRun.id.desc()).first()
        if run:
            print(f"ReviewRun correctly created. Status: {run.status}")
        else:
            print("ReviewRun NOT created.")
    else:
        print("PR NOT found in DB. Webhook might have failed or not arrived yet.")
        
    # Check WebhookEvents
    events = db.query(WebhookEvent).filter(WebhookEvent.repository_id == 2).order_by(WebhookEvent.id.desc()).limit(5).all()
    print("Recent Webhook Events:")
    for e in events:
        print(f"  - Action: {e.action}, Status: {e.status}, Event: {e.event_type}")
        
    print("DONE.")

if __name__ == "__main__":
    main()
