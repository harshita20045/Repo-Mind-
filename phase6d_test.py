# -*- coding: utf-8 -*-
import io, sys, os, time, json, requests, psycopg2
from dotenv import load_dotenv
from cryptography.fernet import Fernet

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.append(os.path.abspath('.'))
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"
OWNER = "harshita20045"
REPO = "repomind-e2e-test-repository"
REPO_ID = 2
PR_NUMBER = 11

# Get GitHub token
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

gh_headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}
GH = "https://api.github.com"

print(f"============================================================")
print(f"PHASE 6D — Real PR Webhook Comment Test")
print(f"============================================================")

print(f"\n[1] Getting PR #{PR_NUMBER} details...")
pr_res = requests.get(f"{GH}/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}", headers=gh_headers).json()
head_sha = pr_res["head"]["sha"]
print(f"    Head SHA: {head_sha[:12]}...")

print(f"\n[2] Getting PR files...")
files_res = requests.get(f"{GH}/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/files", headers=gh_headers).json()
target_file = files_res[0]["filename"]
print(f"    Target file: {target_file}")

print(f"\n[3] Adding review comment...")
comment_payload = {
    "body": "Phase 6D: Testing pull_request_review_comment webhook lifecycle.",
    "commit_id": head_sha,
    "path": target_file,
    "side": "RIGHT",
    "line": 1
}
comment_res = requests.post(
    f"{GH}/repos/{OWNER}/{REPO}/pulls/{PR_NUMBER}/comments",
    json=comment_payload,
    headers=gh_headers
)
print(f"    Comment creation: {comment_res.status_code}")
if comment_res.status_code not in (201, 200):
    print("Failed!", comment_res.text)
    sys.exit(1)

print(f"\n[4] Waiting 10 seconds for webhook & processing...")
for i in range(10):
    time.sleep(1)
    print(".", end="", flush=True)
print("\n")

print(f"\n[5] Verifying database state...")
cur.execute("""
    SELECT we.id, we.github_delivery_id, we.event_type, we.action, we.status, we.received_at
    FROM webhook_event we
    WHERE we.repository_id = 2 AND we.event_type = 'pull_request_review_comment'
    ORDER BY we.id DESC LIMIT 1
""")
target_event = cur.fetchone()

if target_event:
    print(f"    [OK] Found 'pull_request_review_comment' event: ID={target_event[0]} (action={target_event[3]}, status={target_event[4]})")
else:
    print(f"    [!!] No 'pull_request_review_comment' event found")

cur.execute("""
    SELECT rr.id, rr.pull_request_id, rr.status, rr.progress_message
    FROM review_run rr
    JOIN pull_request pr ON pr.id = rr.pull_request_id
    WHERE pr.github_number = %s AND pr.repository_id = 2
    ORDER BY rr.id ASC
""", (PR_NUMBER,))
runs = cur.fetchall()

print(f"\n    ReviewRuns for PR #{PR_NUMBER}:")
for r in runs:
    print(f"      Run ID={r[0]} | Status: {r[2]:10} | Msg: {r[3]}")

# Verify exact count is 1 for the relevant run if we reused it?
# In Phase 6C, we already had Run 4 and 5. Run 4 was stuck 'running' and Run 5 was 'completed'.
# The fix in 6D reuses the LAST run for the PR. So Run 5 should have been set to 'pending' then picked up and completed,
# or Run 4 might have been reused if it was last. Let's see what we get.
conn.close()
