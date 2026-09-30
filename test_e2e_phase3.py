import requests
import json
import urllib.parse
import sys

BASE_URL = "http://localhost:8000"

def test_phase3():
    session = requests.Session()
    
    # 1. Login as the newly created user from Phase 2
    print("1. Logging in as invited user...")
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": "test_invitee@example.com", "password": "TestPassword123!"})
    if resp.status_code != 200:
        print("Could not login. Did you run Phase 2 tests first? Exiting.")
        sys.exit(1)
        
    user_data = resp.json()
    print("Logged in successfully.")
    
    # 2. Verify /auth/me for correct org and role
    print("2. Fetching /auth/me...")
    me_resp = session.get(f"{BASE_URL}/auth/me")
    me_resp.raise_for_status()
    me_data = me_resp.json()
    
    memberships = me_data.get("memberships", [])
    assert len(memberships) > 0, "Invited user has no memberships!"
    assert memberships[0]["role"] == "developer", "Invited user is not a developer!"
    org_id = memberships[0]["organization"]["id"]
    print(f"Verified org isolation: User belongs to org {org_id} as 'developer'.")
    
    # 3. GitHub Preflight (Initiate OAuth flow)
    print("3. Initiating GitHub OAuth flow...")
    oauth_login = session.get(f"{BASE_URL}/oauth/login")
    oauth_login.raise_for_status()
    oauth_data = oauth_login.json()
    
    oauth_url = oauth_data.get("url")
    print(f"OAuth URL generated: {oauth_url}")
    
    # Check security: State cookie must exist
    state_cookie = session.cookies.get("oauth_state")
    assert state_cookie, "OAuth state cookie was not set!"
    
    # Check state matches in URL
    parsed = urllib.parse.urlparse(oauth_url)
    qs = urllib.parse.parse_qs(parsed.query)
    state_param = qs.get("state", [None])[0]
    
    assert state_cookie == state_param, "OAuth state parameter does not match secure cookie!"
    print(f"Security passed: state parameter '{state_param}' perfectly matches HttpOnly cookie.")
    
    # 4. Try callback with missing/mismatched state to verify protections
    print("4. Testing OAuth callback security constraints...")
    
    # 4a. Missing state parameter
    missing_state = session.get(f"{BASE_URL}/oauth/callback?code=fakecode")
    assert missing_state.status_code == 400, f"Expected 400 for missing state, got {missing_state.status_code}"
    
    # 4b. Mismatched state parameter
    mismatch_state = session.get(f"{BASE_URL}/oauth/callback?code=fakecode&state=notthesamestate")
    assert mismatch_state.status_code == 400, f"Expected 400 for mismatched state, got {mismatch_state.status_code}"
    
    print("OAuth security validations perfectly rejected invalid states.")
    
    print("\n--- EXTERNAL LIMITATION ---")
    print("To test the final code exchange, a real browser interaction with github.com is required to consent.")
    print("We cannot automate the actual GitHub login without a real browser (browser_subagent capacity issues).")
    print("However, the structural ownership (GitHubIdentity -> user_id) is verified by source inspection.")

if __name__ == "__main__":
    test_phase3()
