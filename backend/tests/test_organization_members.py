from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_organization_membership_roles():
    import uuid
    # Create Org Admin
    email_admin = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    res_admin = client.post("/auth/register", json={"email": email_admin, "password": "password", "organization_name": "Org 1"})
    org_id = res_admin.json()["memberships"][0]["organization_id"]
    token_admin = client.post("/auth/login", json={"email": email_admin, "password": "password"}).cookies.get("access_token")

    # Create target user separately
    email_user = f"user_{uuid.uuid4().hex[:8]}@example.com"
    res_user = client.post("/auth/register", json={"email": email_user, "password": "password", "organization_name": "Org 2"})
    user_id = res_user.json()["user"]["id"]
    token_user = client.post("/auth/login", json={"email": email_user, "password": "password"}).cookies.get("access_token")

    # Admin adds user to Org 1
    res_add = client.post(f"/organizations/{org_id}/members", json={"email": email_user, "role": "developer"}, cookies={"access_token": token_admin})
    assert res_add.status_code == 201
    
    # List members
    res_list = client.get(f"/organizations/{org_id}/members", cookies={"access_token": token_admin})
    assert len(res_list.json()) == 2
    
    # User tries to change own role (fail)
    res_escalate = client.put(f"/organizations/{org_id}/members/{user_id}/role", json={"role": "org_admin"}, cookies={"access_token": token_user})
    assert res_escalate.status_code == 403

    # Admin changes user role to reviewer
    res_update = client.put(f"/organizations/{org_id}/members/{user_id}/role", json={"role": "reviewer"}, cookies={"access_token": token_admin})
    assert res_update.status_code == 200
    assert res_update.json()["role"] == "reviewer"

    # Admin removes user
    res_remove = client.delete(f"/organizations/{org_id}/members/{user_id}", cookies={"access_token": token_admin})
    assert res_remove.status_code == 204

    # User no longer has access to Org 1
    res_fail = client.get(f"/organizations/{org_id}/members", cookies={"access_token": token_user})
    assert res_fail.status_code == 404
