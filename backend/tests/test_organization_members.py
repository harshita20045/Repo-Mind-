import pytest
import os
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.auth.models import User, Organization, OrganizationMembership



def test_organization_membership_roles(client: TestClient, db_session):
    # 1. Bootstrap to get an Admin and Org 1
    res_admin = client.post("/auth/bootstrap", json={
        "email": "admin@example.com", "password": "password", 
        "organization_name": "Org 1", "bootstrap_token": "test_bootstrap_token"
    })
    org_id = res_admin.json()["memberships"][0]["organization_id"]
    token_admin = client.post("/auth/login", json={"email": "admin@example.com", "password": "password"}).cookies.get("access_token")

    # Admin adds user to Org 1
    res_add = client.post(
        f"/organizations/{org_id}/members", 
        json={"email": "user@example.com", "role": "developer"}, 
        cookies={"access_token": token_admin}
    )
    assert res_add.status_code == 201
    invitation_token = res_add.json()["invitation_token"]

    # List members
    res_list = client.get(f"/organizations/{org_id}/members", cookies={"access_token": token_admin})
    assert len(res_list.json()) == 2

    # User completes onboarding
    res_user = client.post("/auth/onboard", json={"invitation_token": invitation_token, "new_password": "user_password"})
    user_id = res_user.json()["user"]["id"]
    token_user = res_user.cookies.get("access_token")

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
