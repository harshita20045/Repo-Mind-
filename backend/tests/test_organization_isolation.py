from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.auth.models import RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.auth.service import register_user

client = TestClient(app)

def test_organization_isolation():
    # Setup Org A and User A
    import uuid
    email_a = f"usera_{uuid.uuid4().hex[:8]}@example.com"
    email_b = f"userb_{uuid.uuid4().hex[:8]}@example.com"
    
    res_a_reg = client.post("/auth/register", json={"email": email_a, "password": "password", "organization_name": "Org A"})
    org_a_id = res_a_reg.json()["memberships"][0]["organization_id"]
    
    # Setup Org B and User B
    res_b_reg = client.post("/auth/register", json={"email": email_b, "password": "password", "organization_name": "Org B"})
    org_b_id = res_b_reg.json()["memberships"][0]["organization_id"]
    
    # User B creates a project in Org B
    res_b = client.post("/auth/login", json={"email": email_b, "password": "password"})
    token_b = res_b.cookies.get("access_token")
    
    res_project_b = client.post(
        f"/organizations/{org_b_id}/projects",
        json={"name": "Project B"},
        cookies={"access_token": token_b}
    )
    assert res_project_b.status_code == 201
    project_b_id = res_project_b.json()["id"]
    
    res_repo_b = client.post(
        f"/projects/{project_b_id}/repositories",
        json={"github_owner": "owner", "github_name": "repo"},
        cookies={"access_token": token_b}
    )
    assert res_repo_b.status_code == 201
    repo_b_id = res_repo_b.json()["id"]
    
    # User A logs in
    res_a = client.post("/auth/login", json={"email": email_a, "password": "password"})
    token_a = res_a.cookies.get("access_token")
    
    # User A tries to list Org B projects -> 404
    r1 = client.get(f"/organizations/{org_b_id}/projects", cookies={"access_token": token_a})
    assert r1.status_code == 404
    
    # User A tries to list Project B repos -> 404
    r2 = client.get(f"/projects/{project_b_id}/repositories", cookies={"access_token": token_a})
    assert r2.status_code == 404
    
    # User A tries to get Repo B details -> 404
    r3 = client.get(f"/repositories/{repo_b_id}", cookies={"access_token": token_a})
    assert r3.status_code == 404
