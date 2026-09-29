import requests

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()

def check():
    # Login as harshita
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email": "harshita.baghel@example.com",
        "password": "Password123!"
    })
    
    print("Login Status:", res.status_code)
    
    # List available GitHub repos
    res = session.get(f"{BASE_URL}/organizations/1/github/repos")
    print("Repos Status:", res.status_code)
    if res.status_code == 200:
        repos = res.json()
        print(f"Found {len(repos)} repositories.")
        if repos:
            print("First repo:", repos[0])
            # Connect the first repo
            owner = repos[0]["github_owner"]
            name = repos[0]["github_name"]
            branch = repos[0].get("default_branch", "main")
            
            print(f"\nConnecting {owner}/{name}...")
            # We need a project first
            proj_res = session.get(f"{BASE_URL}/organizations/1/projects")
            projects = proj_res.json()
            if not projects:
                p_res = session.post(f"{BASE_URL}/organizations/1/projects", json={"name": "Default Project"})
                project_id = p_res.json()["id"]
            else:
                project_id = projects[0]["id"]
                
            conn_res = session.post(f"{BASE_URL}/repositories/connect?organization_id=1", json={
                "project_id": project_id,
                "github_owner": owner,
                "github_name": name,
                "default_branch": branch
            })
            print("Connect Status:", conn_res.status_code)
            print("Connect Response:", conn_res.json())

            # Test duplicate
            conn2_res = session.post(f"{BASE_URL}/repositories/connect?organization_id=1", json={
                "project_id": project_id,
                "github_owner": owner,
                "github_name": name,
                "default_branch": branch
            })
            print("Duplicate Connect Status:", conn2_res.status_code)
            print("Duplicate Connect Response:", conn2_res.json())

if __name__ == "__main__":
    check()
