import pytest
import os
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import get_db, SessionLocal
from backend.app.auth.models import User, Organization, OrganizationMembership


@pytest.fixture
def client():
    # Ensure a valid bootstrap token is set for tests
    os.environ["BOOTSTRAP_TOKEN"] = "test_bootstrap_token"
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        # Clear users for fresh bootstrap test
        session.query(OrganizationMembership).delete()
        session.query(Organization).delete()
        session.query(User).delete()
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()


def test_bootstrap_flow(client: TestClient, db_session):
    # 1. Valid bootstrap
    response = client.post(
        "/auth/bootstrap",
        json={
            "email": "admin@example.com",
            "password": "SecurePassword123!",
            "organization_name": "Test Engineering",
            "bootstrap_token": "test_bootstrap_token",
        },
    )
    assert response.status_code == 201
    assert "access_token" in response.cookies
    data = response.json()
    assert data["user"]["email"] == "admin@example.com"
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["role"] == "org_admin"

    # 2. Second bootstrap fails
    response2 = client.post(
        "/auth/bootstrap",
        json={
            "email": "admin2@example.com",
            "password": "SecurePassword123!",
            "organization_name": "Test Engineering 2",
            "bootstrap_token": "test_bootstrap_token",
        },
    )
    assert response2.status_code == 400

    # 3. /auth/me
    me_res = client.get("/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["user"]["email"] == "admin@example.com"


def test_onboard_and_change_password_flow(client: TestClient, db_session):
    # 1. Bootstrap
    client.post(
        "/auth/bootstrap",
        json={
            "email": "admin@example.com",
            "password": "AdminPassword123!",
            "organization_name": "Test Org",
            "bootstrap_token": "test_bootstrap_token",
        },
    )
    org_id = client.get("/auth/me").json()["memberships"][0]["organization_id"]

    # 2. Add Member (Onboard)
    invite_res = client.post(
        f"/organizations/{org_id}/members",
        json={"email": "newuser@example.com", "role": "developer"}
    )
    assert invite_res.status_code == 201
    invite_data = invite_res.json()
    token = invite_data["invitation_token"]
    assert token is not None

    # Logout admin
    client.post("/auth/logout")

    # 3. Complete Onboarding
    onboard_res = client.post(
        "/auth/onboard",
        json={
            "invitation_token": token,
            "new_password": "NewUserPassword123!"
        }
    )
    assert onboard_res.status_code == 200
    assert "access_token" in onboard_res.cookies

    # 4. Change Password
    change_res = client.post(
        "/auth/change-password",
        json={
            "current_password": "NewUserPassword123!",
            "new_password": "ChangedPassword123!"
        }
    )
    assert change_res.status_code == 200

    # 5. Old password fails
    client.post("/auth/logout")
    bad_login = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "NewUserPassword123!"}
    )
    assert bad_login.status_code == 401

    # 6. New password works
    good_login = client.post(
        "/auth/login",
        json={"email": "newuser@example.com", "password": "ChangedPassword123!"}
    )
    assert good_login.status_code == 200
