import requests
import json
import urllib.parse
from bs4 import BeautifulSoup
import httpx

BASE_URL = "http://127.0.0.1:8000"

def get_auth_token():
    # Helper to login as org_admin
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "harshita.baghel@example.com", "password": "Password123!"})
    if res.status_code == 200:
        return res.cookies.get("access_token")
    return None

def test_oauth_routes():
    token = get_auth_token()
    if not token:
        print("Failed to login")
        return
        
    cookies = {"access_token": token}
    
    # 1. Hit /oauth/login
    res = requests.get(f"{BASE_URL}/oauth/login", cookies=cookies)
    print(f"Login route returned: {res.status_code}")
    
    # Capture the secure state cookie
    oauth_state = res.cookies.get("oauth_state")
    print(f"Captured oauth_state cookie: {oauth_state}")
    
    data = res.json()
    url = data.get("url")
    print(f"Redirect URL: {url}")
    
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    state_param = qs.get("state", [None])[0]
    print(f"State in URL: {state_param}")
    
    if oauth_state and oauth_state == state_param:
        print("✓ State parameter matches cookie.")
    else:
        print("✗ State parameter mismatch!")
        
    # 2. Test missing state
    cb_missing = requests.get(f"{BASE_URL}/oauth/callback?code=fakecode", cookies=cookies)
    print(f"Missing state check (should be 400): {cb_missing.status_code} - {cb_missing.text}")
    
    # 3. Test mismatched state
    cookies_mismatch = cookies.copy()
    cookies_mismatch["oauth_state"] = "wrongcookie"
    cb_mismatch = requests.get(f"{BASE_URL}/oauth/callback?code=fakecode&state={state_param}", cookies=cookies_mismatch)
    print(f"Mismatched state check (should be 400): {cb_mismatch.status_code} - {cb_mismatch.text}")
    
    # We cannot test a successful OAuth code exchange without real GitHub user action, 
    # but we can return the URL so the user can click it.

if __name__ == "__main__":
    test_oauth_routes()
