import os
import requests
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Database setup
# from backend/app/core/config.py
DATABASE_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:postgres@localhost:5432/repomind")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

API_URL = "http://localhost:8000"
test_email = f"admin_{int(time.time())}@repomind.local"
password = "admin123_test"
org_name = f"Test Org {int(time.time())}"

def run_tests():
    print("--- STARTING ACCEPTANCE TESTS ---")
    
    # 1. Register User (becomes ORG_ADMIN of the new org)
    res = requests.post(f"{API_URL}/auth/register", json={
        "email": test_email,
        "password": password,
        "organization_name": org_name
    })
    
    if res.status_code != 200:
        print(f"Failed to register: {res.text}")
        return
        
    # Login to get token
    res = requests.post(f"{API_URL}/auth/login", json={
        "email": test_email,
        "password": password
    })
    
    cookies = res.cookies
    me_res = requests.get(f"{API_URL}/auth/me", cookies=cookies).json()
    org_id = me_res["memberships"][0]["organization_id"]
    print(f"Registered Admin: {test_email}, Org ID: {org_id}")

    # 2. Test Project Creation
    res_proj_a = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project A"}, cookies=cookies)
    proj_a = res_proj_a.json()
    print(f"Project A created: {proj_a['id']}")
    
    res_proj_b = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project B"}, cookies=cookies)
    proj_b = res_proj_b.json()
    print(f"Project B created: {proj_b['id']}")
    
    # 3. Test Repo Connection
    res_repo_a = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json={
        "project_id": proj_a["id"],
        "github_owner": "torvalds", # just an example public repo
        "github_name": "linux",
        "default_branch": "master",
        "pat": "ghp_fake123_invalid_but_testing" # might fail validation, let's see
    }, cookies=cookies)
    
    # Wait, the connect_repository endpoint validates PAT against GitHub API!
    # So "ghp_fake123" WILL fail.
    # We must mock or bypass it if we don't have a real PAT, OR we just let it fail and record the failure.
    print(f"Repo A connect result: {res_repo_a.status_code} - {res_repo_a.text}")

if __name__ == "__main__":
    run_tests()
