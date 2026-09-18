import os
import requests
import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Setup
DATABASE_URL = os.getenv("POSTGRES_URL", "postgresql://postgres:Sipl%4012345@localhost:5432/repomind_db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
API_URL = "http://localhost:8000"

ts = int(time.time())
org_name = f"TestOrg_{ts}"
admin_email = f"admin_{ts}@example.com"
lead_email = f"lead_{ts}@example.com"
reviewer_email = f"reviewer_{ts}@example.com"
dev_email = f"dev_{ts}@example.com"
password = "Password123!"
bootstrap_token = "fkjerngiorneognrengioirw0rrrrrth348h3fin3gnw3480"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def test_flow():
    print_header("1. SETUP & REGISTRATION")
    # Clean DB state or ensure bootstrap is allowed
    # (If the system is already bootstrapped, we might need to bypass it or use an existing org_admin. Let's try to just use SQL for everything to be safe!)
    
    with SessionLocal() as db:
        # 1. Create org
        org_res = db.execute(text("INSERT INTO organization (name, created_at) VALUES (:n, NOW()) RETURNING id"), {"n": org_name}).fetchone()
        org_id = org_res[0]
        
        # 2. Create users
        users = [
            (admin_email, "org_admin"),
            (lead_email, "team_lead"),
            (reviewer_email, "reviewer"),
            (dev_email, "developer")
        ]
        
        user_ids = {}
        for email, role in users:
            import bcrypt
            hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            res = db.execute(text("INSERT INTO \"user\" (email, password_hash, created_at) VALUES (:e, :h, NOW()) RETURNING id"), {"e": email, "h": hashed}).fetchone()
            uid = res[0]
            user_ids[role] = uid
            db.execute(text("INSERT INTO organization_membership (organization_id, user_id, role) VALUES (:o, :u, :r)"), {"o": org_id, "u": uid, "r": role})
            
        db.commit()
    print("Assigned LEAD, REVIEWER, DEVELOPER roles in DB.")

    # Get cookies for users
    def get_cookies(email):
        res = requests.post(f"{API_URL}/auth/login", json={"email": email, "password": password})
        if res.status_code != 200:
            print(f"Failed to login {email}: {res.text}")
        return res.cookies
        
    admin_cookies = get_cookies(admin_email)
    lead_cookies = get_cookies(lead_email)
    reviewer_cookies = get_cookies(reviewer_email)
    dev_cookies = get_cookies(dev_email)

    print_header("2. PROJECT CREATION & AUTHORIZATION")
    # Admin creates project
    res = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project Alpha"}, cookies=admin_cookies)
    print(f"ORG_ADMIN Create Project: HTTP {res.status_code} - {res.json()}")
    proj_alpha_id = res.json().get("id")

    # Lead attempts
    res = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project Beta"}, cookies=lead_cookies)
    print(f"LEAD Create Project: HTTP {res.status_code} - {res.json()}")
    
    # Reviewer attempts
    res = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project Gamma"}, cookies=reviewer_cookies)
    print(f"REVIEWER Create Project: HTTP {res.status_code} - {res.json()}")
    
    # Developer attempts
    res = requests.post(f"{API_URL}/organizations/{org_id}/projects", json={"name": "Project Delta"}, cookies=dev_cookies)
    print(f"DEVELOPER Create Project: HTTP {res.status_code} - {res.json()}")

    # Verify DB for projects
    with SessionLocal() as db:
        projects = db.execute(text("SELECT id, name, organization_id FROM project WHERE organization_id = :org_id"), {"org_id": org_id}).fetchall()
        print(f"\nDB Projects for Org {org_id}:")
        for p in projects:
            print(f" - ID: {p.id}, Name: {p.name}, OrgID: {p.organization_id}")

    print_header("3. CONNECT REPOSITORY AUTHORIZATION (WITHOUT VALID PAT)")
    payload = {
        "project_id": proj_alpha_id,
        "github_owner": "test",
        "github_name": "test-repo",
        "default_branch": "main",
        "pat": "ghp_fake123"
    }
    
    # Lead attempts
    res = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json=payload, cookies=lead_cookies)
    print(f"LEAD Connect Repo: HTTP {res.status_code} - {res.json()}")
    
    # Reviewer attempts
    res = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json=payload, cookies=reviewer_cookies)
    print(f"REVIEWER Connect Repo: HTTP {res.status_code} - {res.json()}")
    
    # Developer attempts
    res = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json=payload, cookies=dev_cookies)
    print(f"DEVELOPER Connect Repo: HTTP {res.status_code} - {res.json()}")

    # Admin attempts (Will hit GitHub validation and fail 400/401/404)
    res = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json=payload, cookies=admin_cookies)
    print(f"ORG_ADMIN Connect Repo: HTTP {res.status_code} - {res.json()}")

    print_header("4. CROSS-TENANT ISOLATION")
    hacker_email = f"hacker_{ts}@example.com"
    with SessionLocal() as db:
        org_res = db.execute(text("INSERT INTO organization (name, created_at) VALUES ('HackerOrg', NOW()) RETURNING id")).fetchone()
        hacker_org_id = org_res[0]
        import bcrypt
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        res = db.execute(text("INSERT INTO \"user\" (email, password_hash, created_at) VALUES (:e, :h, NOW()) RETURNING id"), {"e": hacker_email, "h": hashed}).fetchone()
        db.execute(text("INSERT INTO organization_membership (organization_id, user_id, role) VALUES (:o, :u, 'org_admin')"), {"o": hacker_org_id, "u": res[0]})
        db.commit()
        
    hacker_cookies = get_cookies(hacker_email)
    
    # Hacker attempts to connect repo to Org 1's project
    res = requests.post(f"{API_URL}/repositories/connect?organization_id={org_id}", json=payload, cookies=hacker_cookies)
    print(f"CROSS-TENANT Connect Repo: HTTP {res.status_code} - {res.json()}")

    # List repositories for Org 1's project using Hacker
    res = requests.get(f"{API_URL}/projects/{proj_alpha_id}/repositories", cookies=hacker_cookies)
    print(f"CROSS-TENANT List Repos: HTTP {res.status_code} - {res.json()}")
    
    print_header("5. PROJECT LISTING ISOLATION")
    res = requests.get(f"{API_URL}/organizations/{org_id}/projects", cookies=admin_cookies)
    print(f"ORG_ADMIN Get Projects: HTTP {res.status_code} - {res.json()}")

if __name__ == "__main__":
    try:
        test_flow()
    except Exception as e:
        print(f"Error: {e}")
