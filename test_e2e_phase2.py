import requests
import json
import time

BASE_URL = "http://localhost:8000"

def run_test():
    session = requests.Session()
    
    # 1. Login as admin
    print("Logging in as admin...")
    resp = session.post(f"{BASE_URL}/auth/login", json={"email": "harshita.baghel@example.com", "password": "Password123!"})
    resp.raise_for_status()
    admin_data = resp.json()
    org_id = admin_data["memberships"][0]["organization"]["id"]
    print(f"Logged in. Org ID: {org_id}")
    
    # 2. Invite member
    print("Inviting test_invitee@example.com as developer...")
    invite_resp = session.post(
        f"{BASE_URL}/organizations/{org_id}/members",
        json={"email": "test_invitee@example.com", "role": "developer"}
    )
    invite_resp.raise_for_status()
    invite_data = invite_resp.json()
    token = invite_data["invitation_token"]
    print(f"Invitation token: {token}")
    
    # 3. Onboard member (new session to simulate different user/browser)
    new_session = requests.Session()
    print("Onboarding new member...")
    onboard_resp = new_session.post(
        f"{BASE_URL}/auth/onboard",
        json={"invitation_token": token, "new_password": "TestPassword123!"}
    )
    onboard_resp.raise_for_status()
    onboard_data = onboard_resp.json()
    print("Onboarded successfully!")
    
    # 4. Login as new member
    print("Logging in as new member...")
    login_resp = new_session.post(
        f"{BASE_URL}/auth/login",
        json={"email": "test_invitee@example.com", "password": "TestPassword123!"}
    )
    login_resp.raise_for_status()
    new_member_data = login_resp.json()
    
    # 5. Verify /auth/me
    print("Fetching /auth/me for new member...")
    me_resp = new_session.get(f"{BASE_URL}/auth/me")
    me_resp.raise_for_status()
    me_data = me_resp.json()
    
    memberships = me_data["memberships"]
    assert len(memberships) > 0, "No memberships found!"
    assert memberships[0]["organization"]["id"] == org_id, "Wrong organization!"
    assert memberships[0]["role"] == "developer", "Wrong role!"
    print(f"Success! New member {me_data['user']['email']} has role {memberships[0]['role']} in org {org_id}")

if __name__ == "__main__":
    run_test()
