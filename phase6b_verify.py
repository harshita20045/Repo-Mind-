"""
Phase 6B verification script.
Checks:
1. Backend endpoint
2. Env config (WEBHOOK_URL, WEBHOOK_SECRET - CONFIGURED/MISSING only)
3. Webhook registration status on GitHub
4. Sends GitHub ping test delivery via GitHub API
5. Checks WebhookEvent DB result
6. Tests duplicate delivery idempotency
"""
import os
import sys
import time
import hmac
import hashlib
import json
import requests

sys.path.append(os.path.abspath('.'))
from dotenv import load_dotenv
load_dotenv()

BASE_URL = "http://127.0.0.1:8000"

# 1. Backend health
health = requests.get(f"{BASE_URL}/health")
print(f"[1] Backend endpoint: {BASE_URL}")
print(f"    Health: {health.status_code} {health.json()}")

# 2. Env config (CONFIGURED/MISSING only)
webhook_url = os.environ.get("GITHUB_WEBHOOK_URL", "")
webhook_secret = os.environ.get("GITHUB_WEBHOOK_SECRET", "")
print(f"\n[2] GITHUB_WEBHOOK_URL:    {'CONFIGURED' if webhook_url else 'MISSING'}")
print(f"    GITHUB_WEBHOOK_SECRET: {'CONFIGURED' if webhook_secret else 'MISSING'}")

if not webhook_url or not webhook_secret:
    print("BLOCKED: Cannot proceed without webhook URL and secret.")
    sys.exit(1)

# 3. Login and check webhook registration on GitHub
session = requests.Session()
login = session.post(f"{BASE_URL}/auth/login", json={
    "email": "harshita.baghel@example.com",
    "password": "Password123!"
})
print(f"\n[3] Login: {login.status_code}")

# Get decrypted token via backend (we won't expose it)
import psycopg2
from cryptography.fernet import Fernet

fernet_key = os.environ.get("FERNET_KEY")
conn = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur = conn.cursor()
cur.execute("SELECT gc.encrypted_access_token FROM github_credential gc JOIN github_identity gi ON gi.id=gc.github_identity_id JOIN \"user\" u ON u.id=gi.user_id WHERE u.id=1")
row = cur.fetchone()
conn.close()

f = Fernet(fernet_key.encode())
token = f.decrypt(row[0].encode()).decode()

owner = "harshita20045"
name = "repomind-e2e-test-repository"
gh_headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json"
}
gh_base = "https://api.github.com"

# List webhooks
hooks = requests.get(f"{gh_base}/repos/{owner}/{name}/hooks", headers=gh_headers).json()
matching = [h for h in hooks if isinstance(h, dict) and webhook_url in h.get("config", {}).get("url", "")]

if matching:
    hook = matching[0]
    hook_id = hook["id"]
    print(f"\n[3] Webhook exists: ID {hook_id}")
    print(f"    Active: {hook.get('active')}")
    print(f"    URL: {hook['config']['url']}")
    print(f"    Content-Type: {hook['config'].get('content_type')}")
    print(f"    Events: {hook.get('events')}")
else:
    print("\n[3] No matching webhook found. Registering...")
    # Register with only needed events
    reg = requests.post(f"{gh_base}/repos/{owner}/{name}/hooks", json={
        "name": "web",
        "active": True,
        "events": ["pull_request", "ping"],
        "config": {
            "url": webhook_url,
            "content_type": "json",
            "secret": webhook_secret,
            "insecure_ssl": "0"
        }
    }, headers=gh_headers)
    hook = reg.json()
    hook_id = hook.get("id")
    print(f"    Registered: {reg.status_code}, ID: {hook_id}")

# 4. Test ping delivery
print(f"\n[4] Sending test ping via GitHub webhook re-delivery...")
test_del = requests.post(f"{gh_base}/repos/{owner}/{name}/hooks/{hook_id}/tests", headers=gh_headers)
print(f"    Ping test status: {test_del.status_code}")
if test_del.status_code not in (200, 204):
    print(f"    Response: {test_del.text[:200]}")

# Wait for delivery
time.sleep(4)

# 5. Check WebhookEvent DB
conn2 = psycopg2.connect("postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
cur2 = conn2.cursor()
cur2.execute("""
    SELECT id, github_delivery_id, event_type, action, status, received_at, repository_id
    FROM webhook_event
    ORDER BY id DESC
    LIMIT 5
""")
rows = cur2.fetchall()
print(f"\n[5] Recent WebhookEvents in DB:")
if not rows:
    print("    (none)")
for r in rows:
    print(f"    ID={r[0]} delivery={r[1]} type={r[2]} action={r[3]} status={r[4]} repo_id={r[6]}")

# 6. Test idempotency: send same delivery again via HMAC simulation
# We use the most recent delivery_id found in DB
if rows:
    last_delivery_id = rows[0][1]
    print(f"\n[6] Testing duplicate delivery idempotency with delivery_id: {last_delivery_id}")
    
    # Build a fake ping payload
    test_payload = json.dumps({"zen": "test", "hook_id": hook_id}).encode()
    expected_sig = "sha256=" + hmac.new(
        webhook_secret.encode(),
        test_payload,
        hashlib.sha256
    ).hexdigest()
    
    dup_res = requests.post(
        f"{BASE_URL}/webhooks/github",
        data=test_payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": expected_sig,
            "X-GitHub-Delivery": last_delivery_id
        }
    )
    print(f"    Duplicate delivery response: {dup_res.status_code} {dup_res.json()}")
    if dup_res.json().get("status") == "duplicate":
        print("    IDEMPOTENCY: PASSED — duplicate was rejected correctly.")
    else:
        print("    IDEMPOTENCY: UNEXPECTED response")

    # Also test invalid signature
    print(f"\n[6b] Testing INVALID signature rejection...")
    bad_sig = "sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    bad_res = requests.post(
        f"{BASE_URL}/webhooks/github",
        data=test_payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": bad_sig,
            "X-GitHub-Delivery": "fake-bad-sig-delivery"
        }
    )
    print(f"    Bad signature response: {bad_res.status_code} (expected 401)")

    # Test missing signature
    print(f"\n[6c] Testing MISSING signature rejection...")
    no_sig_res = requests.post(
        f"{BASE_URL}/webhooks/github",
        data=test_payload,
        headers={
            "Content-Type": "application/json",
            "X-GitHub-Event": "ping",
            "X-GitHub-Delivery": "fake-no-sig-delivery"
        }
    )
    print(f"    No signature response: {no_sig_res.status_code} (expected 401)")

print("\n=== Phase 6B verification complete ===")
conn2.close()
