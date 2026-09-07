import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import get_db, SessionLocal
from backend.app.auth.models import User, Organization, OrganizationMembership


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def test_auth_flow(client: TestClient):
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"

    # 1. Register a new user
    reg_response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "organization_name": "Test Engineering",
        },
    )
    assert reg_response.status_code == 201, reg_response.text
    data = reg_response.json()
    assert data["user"]["email"] == unique_email
    assert len(data["memberships"]) == 1
    assert data["memberships"][0]["organization"]["name"] == "Test Engineering"
    assert data["memberships"][0]["role"] == "org_admin"
    assert "access_token" in reg_response.cookies

    # 2. Get /auth/me with the session cookie
    me_response = client.get("/auth/me")
    assert me_response.status_code == 200
    me_data = me_response.json()
    assert me_data["user"]["email"] == unique_email

    # 3. Duplicate registration rejected
    dup_response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": password,
        },
    )
    assert dup_response.status_code == 400

    # 4. Logout clears cookie
    logout_response = client.post("/auth/logout")
    assert logout_response.status_code == 200

    # 5. /auth/me after logout returns 401
    # Create fresh client without cookies to verify unauthenticated rejection
    fresh_client = TestClient(app)
    unauth_response = fresh_client.get("/auth/me")
    assert unauth_response.status_code == 401

    # 6. Login with invalid password returns 401
    bad_login = fresh_client.post(
        "/auth/login",
        json={"email": unique_email, "password": "WrongPassword!"},
    )
    assert bad_login.status_code == 401

    # 7. Login with valid credentials succeeds
    good_login = fresh_client.post(
        "/auth/login",
        json={"email": unique_email, "password": password},
    )
    assert good_login.status_code == 200
    assert "access_token" in good_login.cookies
    assert good_login.json()["user"]["email"] == unique_email

    # 8. /auth/me with Bearer token header works
    token = good_login.cookies.get("access_token")
    bearer_client = TestClient(app)
    bearer_response = bearer_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert bearer_response.status_code == 200
    assert bearer_response.json()["user"]["email"] == unique_email


def test_require_role():
    from fastapi import Depends
    from backend.app.auth.dependencies import require_role
    from backend.app.auth.models import RoleEnum

    # Add a temporary test route to the app
    @app.get("/test-admin-only")
    def admin_only_route(user=Depends(require_role(RoleEnum.ORG_ADMIN))):
        return {"access": "granted"}

    import uuid
    client = TestClient(app)
    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    reg = client.post("/auth/register", json={"email": email, "password": "password123"})
    assert reg.status_code == 201

    # As creator, user is org_admin -> can access admin_only_route
    admin_access = client.get("/test-admin-only")
    assert admin_access.status_code == 200
    assert admin_access.json() == {"access": "granted"}

    # Unauthenticated request receives 401
    anon_client = TestClient(app)
    anon_access = anon_client.get("/test-admin-only")
    assert anon_access.status_code == 401
