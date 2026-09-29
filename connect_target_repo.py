import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()

def check():
    # Login as harshita
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email": "harshita.baghel@example.com",
        "password": "Password123!"
    })
    
    if res.status_code != 200:
        print("Login Failed")
        return
        
    owner = "harshita20045"
    name = "repomind-e2e-test-repository"
    branch = "main"
        
    # List available GitHub repos
    print(f"Discovering repositories for OAuth user...")
    res = session.get(f"{BASE_URL}/organizations/1/github/repos")
    if res.status_code == 200:
        repos = res.json()
        target_repo = next((r for r in repos if r["github_owner"] == owner and r["github_name"] == name), None)
        if target_repo:
            print(f"DISCOVERY SUCCESS: Found {owner}/{name}. Default branch: {target_repo.get('default_branch')}")
        else:
            print(f"DISCOVERY FAILED: {owner}/{name} not found in user's repository list.")
            print("Available repos:")
            for r in repos[:5]:
                print(" -", r["full_name"])
            return
            
        print(f"\nConnecting {owner}/{name}...")
        # Get project ID
        proj_res = session.get(f"{BASE_URL}/organizations/1/projects")
        projects = proj_res.json()
        project_id = projects[0]["id"]
            
        conn_res = session.post(f"{BASE_URL}/repositories/connect?organization_id=1", json={
            "project_id": project_id,
            "github_owner": owner,
            "github_name": name,
            "default_branch": branch
        })
        print("Connect Status:", conn_res.status_code)
        if conn_res.status_code in [200, 201]:
            print(f"Connected successfully. Repository ID: {conn_res.json().get('repository_id')}")
        else:
            print("Connect Error:", conn_res.text)

        # Test duplicate connect
        dup_res = session.post(f"{BASE_URL}/repositories/connect?organization_id=1", json={
            "project_id": project_id,
            "github_owner": owner,
            "github_name": name,
            "default_branch": branch
        })
        print("Duplicate Connect Status:", dup_res.status_code)
        
    else:
        print("Discovery failed:", res.status_code)

if __name__ == "__main__":
    check()
