import pytest
import os
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import SessionLocal
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository

@pytest.fixture
def client():
    os.environ["BOOTSTRAP_TOKEN"] = "test_bootstrap_token"
    return TestClient(app)

@pytest.fixture
def db_session():
    session = SessionLocal()
    try:
        session.query(Repository).delete()
        session.query(Project).delete()
        session.query(OrganizationMembership).delete()
        session.query(Organization).delete()
        session.query(User).delete()
        session.commit()
        yield session
    finally:
        session.rollback()
        session.close()

def test_organization_isolation(client: TestClient, db_session):
    # 1. Bootstrap Org A
    res_a_reg = client.post("/auth/bootstrap", json={
        "email": "usera@example.com", "password": "password", 
        "organization_name": "Org A", "bootstrap_token": "test_bootstrap_token"
    })
    org_a_id = res_a_reg.json()["memberships"][0]["organization_id"]
    token_a = client.post("/auth/login", json={"email": "usera@example.com", "password": "password"}).cookies.get("access_token")

    # 2. Directly create Org B and User B since registration/org creation is restricted
    from backend.app.auth.service import hash_password
    org_b = Organization(name="Org B")
    db_session.add(org_b)
    db_session.flush()

    user_b = User(email="userb@example.com", password_hash=hash_password("password"))
    db_session.add(user_b)
    db_session.flush()

    membership_b = OrganizationMembership(user_id=user_b.id, organization_id=org_b.id, role=RoleEnum.ORG_ADMIN)
    db_session.add(membership_b)
    db_session.commit()

    org_b_id = org_b.id

    # User B logs in
    res_b = client.post("/auth/login", json={"email": "userb@example.com", "password": "password"})
    token_b = res_b.cookies.get("access_token")

    # User B creates a project in Org B
    res_project_b = client.post(
        f"/organizations/{org_b_id}/projects",
        json={"name": "Project B"},
        cookies={"access_token": token_b}
    )
    assert res_project_b.status_code == 201
    project_b_id = res_project_b.json()["id"]

    # User B creates a repository
    res_repo_b = client.post(
        f"/projects/{project_b_id}/repositories",
        json={"github_owner": "owner", "github_name": "repo"},
        cookies={"access_token": token_b}
    )
    assert res_repo_b.status_code == 201
    repo_b_id = res_repo_b.json()["id"]

    # User A tries to list Org B projects -> 404
    r1 = client.get(f"/organizations/{org_b_id}/projects", cookies={"access_token": token_a})
    assert r1.status_code == 404

    # User A tries to list Project B repos -> 404
    r2 = client.get(f"/projects/{project_b_id}/repositories", cookies={"access_token": token_a})
    assert r2.status_code == 404

    # User A tries to get Repo B details -> 404
    r3 = client.get(f"/repositories/{repo_b_id}", cookies={"access_token": token_a})
    assert r3.status_code == 404
