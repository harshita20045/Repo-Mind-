import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()

def check():
    print("Testing /auth/login...")
    res = session.post(f"{BASE_URL}/auth/login", json={
        "email": "harshita.baghel@example.com",
        "password": "Password123!"
    })
    print("Login Status:", res.status_code)
    if res.status_code != 200:
        print("Login Failed:", res.text)
        return
    print("Login Response:", res.json())
    
    print("\nTesting /auth/me...")
    res = session.get(f"{BASE_URL}/auth/me")
    print("Me Status:", res.status_code)
    print("Me Response:", res.json())
    
    print("\nTesting Organization endpoints...")
    # Assuming there are org endpoints, e.g. /organizations/
    res = session.get(f"{BASE_URL}/organizations/")
    print("Organizations Status:", res.status_code)
    if res.status_code == 200:
        orgs = res.json()
        print("Organizations:", orgs)
        if len(orgs) > 0:
            org_id = orgs[0]['id']
            print(f"\nTesting organization members for org {org_id}...")
            res = session.get(f"{BASE_URL}/organizations/{org_id}/members")
            print("Members Status:", res.status_code)
            if res.status_code == 200:
                print("Members:", res.json())

if __name__ == "__main__":
    check()
