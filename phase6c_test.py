# -*- coding: utf-8 -*-
import io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
"""
Phase 6C — Real PR webhook end-to-end test.

Steps:
1. Create a test branch from main
2. Add one minimal test file
3. Open a real PR
4. Wait for GitHub webhook delivery
5. Verify the full chain: WebhookEvent → PR → ReviewRun
"""
import os
import sys
import time
import json
import requests
import psycopg2

sys.path.append(os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()
from cryptography.fernet import Fernet

BASE_URL = "http://127.0.0.1:8000"
OWNER = "harshita20045"
REPO = "repomind-e2e-test-repository"
REPO_ID = 2

# Get GitHub token (without exposing it)
fernet_key = os.environ.get("FERNET_KEY")
conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur = conn.cursor()
cur.execute("""
    SELECT gc.encrypted_access_token
    FROM github_credential gc
    JOIN github_identity gi ON gi.id = gc.github_identity_id
    WHERE gi.user_id = 1
""")
token = Fernet(fernet_key.encode()).decrypt(cur.fetchone()[0].encode()).decode()
conn.close()

gh_headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}
GH = "https://api.github.com"

# Step 1: Create test branch from main
print("=" * 60)
print("PHASE 6C — Real PR Webhook End-to-End Test")
print("=" * 60)

print("\n[1] Getting main branch SHA...")
ref = requests.get(f"{GH}/repos/{OWNER}/{REPO}/git/ref/heads/main", headers=gh_headers).json()
base_sha = ref["object"]["sha"]
print(f"    main SHA: {base_sha[:12]}...")

branch_name = f"phase6c-webhook-test-{int(time.time())}"
print(f"\n[2] Creating branch: {branch_name}")
br_res = requests.post(f"{GH}/repos/{OWNER}/{REPO}/git/refs", json={
    "ref": f"refs/heads/{branch_name}",
    "sha": base_sha
}, headers=gh_headers)
print(f"    Branch creation: {br_res.status_code}")

# Step 2: Make one minimal test change
import base64
file_content = f"# Phase 6C Webhook Test\nCreated at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
print(f"\n[3] Committing test file to {branch_name}...")
file_res = requests.put(
    f"{GH}/repos/{OWNER}/{REPO}/contents/phase6c_test_{int(time.time())}.md",
    json={
        "message": "Phase 6C: webhook integration test file",
        "content": base64.b64encode(file_content.encode()).decode(),
        "branch": branch_name
    },
    headers=gh_headers
)
print(f"    File commit: {file_res.status_code}")

# Step 3: Open a real PR
print(f"\n[4] Opening pull request: {branch_name} -> main")
pr_res = requests.post(f"{GH}/repos/{OWNER}/{REPO}/pulls", json={
    "title": f"Phase 6C: Webhook Integration Test",
    "body": "Automated test PR for Phase 6C webhook verification. DO NOT MERGE.",
    "head": branch_name,
    "base": "main"
}, headers=gh_headers)
pr_data = pr_res.json()
pr_number = pr_data.get("number")
pr_id_github = pr_data.get("id")
pr_url = pr_data.get("html_url")
pr_head_sha = pr_data.get("head", {}).get("sha")
pr_author = pr_data.get("user", {}).get("login")
print(f"    PR created: #{pr_number}")
print(f"    GitHub PR URL: {pr_url}")
print(f"    Head SHA: {pr_head_sha[:12]}...")
print(f"    Author: {pr_author}")

# Step 4: Wait for webhook delivery
print(f"\n[5] Waiting 8 seconds for GitHub webhook delivery...")
time.sleep(8)

# Step 5: Verify everything in the database
print(f"\n[6] Verifying database state...")
conn2 = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur2 = conn2.cursor()

# 6a: Check WebhookEvent
cur2.execute("""
    SELECT we.id, we.github_delivery_id, we.event_type, we.action, we.status,
           we.repository_id, we.received_at, we.processed_at
    FROM webhook_event we
    WHERE we.event_type = 'pull_request'
      AND we.repository_id = %s
    ORDER BY we.id DESC
    LIMIT 5
""", (REPO_ID,))
events = cur2.fetchall()
print(f"\n  [6a] WebhookEvents (pull_request, repo_id={REPO_ID}):")
if not events:
    print("    *** NO pull_request events found! Webhook may not have arrived. ***")
else:
    for e in events:
        print(f"    ID={e[0]} delivery={e[1]} event={e[2]} action={e[3]} status={e[4]} repo_id={e[5]} received={e[6]}")

# Find the event for this specific PR (action=opened)
target_event = None
for e in events:
    if e[3] == "opened" and e[4] == "processed":
        target_event = e
        break

if target_event:
    print(f"    [OK] Found 'opened' + 'processed' event: ID={target_event[0]}")
else:
    print(f"    [!!] No 'opened' + 'processed' event found yet")

# 6b: Check PullRequest record
cur2.execute("""
    SELECT pr.id, pr.repository_id, pr.github_number, pr.title,
           pr.source_branch, pr.target_branch, pr.github_author_login,
           pr.head_sha, pr.state
    FROM pull_request pr
    WHERE pr.repository_id = %s AND pr.github_number = %s
""", (REPO_ID, pr_number))
pr_rows = cur2.fetchall()
print(f"\n  [6b] PullRequest record for PR #{pr_number}:")
if not pr_rows:
    print(f"    *** PR #{pr_number} NOT found in DB ***")
else:
    pr_row = pr_rows[0]
    print(f"    DB ID:           {pr_row[0]}")
    print(f"    Repository ID:   {pr_row[1]} (expected {REPO_ID})")
    print(f"    GitHub Number:   {pr_row[2]} (expected {pr_number})")
    print(f"    Title:           {pr_row[3]}")
    print(f"    Source Branch:   {pr_row[4]} (expected {branch_name})")
    print(f"    Target Branch:   {pr_row[5]} (expected main)")
    print(f"    Author:          {pr_row[6]} (expected {pr_author})")
    print(f"    Head SHA:        {pr_row[7][:12] if pr_row[7] else 'None'}...")
    print(f"    State:           {pr_row[8]}")
    print(f"    Duplicate check: {len(pr_rows)} row(s) (expected 1)")
    pr_db_id = pr_row[0]

# 6c: Check ReviewRun
if pr_rows:
    cur2.execute("""
        SELECT rr.id, rr.pull_request_id, rr.commit_sha, rr.status,
               rr.progress_message, rr.started_at, rr.completed_at
        FROM review_run rr
        WHERE rr.pull_request_id = %s
        ORDER BY rr.id DESC
    """, (pr_db_id,))
    runs = cur2.fetchall()
    print(f"\n  [6c] ReviewRun(s) for PR DB ID {pr_db_id}:")
    if not runs:
        print(f"    *** No ReviewRun found ***")
    else:
        for run in runs:
            print(f"    Run ID:        {run[0]}")
            print(f"    PR ID:         {run[1]}")
            print(f"    Commit SHA:    {run[2][:12] if run[2] else 'None'}...")
            print(f"    Status:        {run[3]}")
            print(f"    Progress:      {run[4]}")
            print(f"    Started At:    {run[5]}")
            print(f"    Completed At:  {run[6]}")
            print()
        print(f"    Total ReviewRuns: {len(runs)}")
        
        # Check for duplicate pending/running
        pending_running = [r for r in runs if r[3] in ("pending", "running")]
        print(f"    Pending/Running: {len(pending_running)}")

# Save key IDs for Phase 6D reference
print(f"\n{'=' * 60}")
print(f"PHASE 6C KEY DATA")
print(f"  PR GitHub Number:  #{pr_number}")
print(f"  PR GitHub URL:     {pr_url}")
print(f"  Branch:            {branch_name} → main")
print(f"  GitHub PR Author:  {pr_author}")
print(f"{'=' * 60}")

conn2.close()
