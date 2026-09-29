import requests
import sys

BASE_URL = "http://127.0.0.1:8000"
session = requests.Session()

def create_user_and_get_token(email, password, role):
    from backend.app.db import SessionLocal
    from backend.app.auth.models import User, OrganizationMembership, RoleEnum
    from backend.app.auth.service import hash_password, create_access_token
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(email=email, password_hash=hash_password(password))
            db.add(user)
            db.flush()
            
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=1,
                role=RoleEnum(role)
            )
            db.add(membership)
            db.commit()
        return create_access_token(user.id, user.email)
    finally:
        db.close()

def get_or_create_target_user():
    from backend.app.db import SessionLocal
    from backend.app.auth.models import User, OrganizationMembership, RoleEnum
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "target_test_user@example.com").first()
        if not user:
            from backend.app.auth.service import hash_password
            user = User(email="target_test_user@example.com", password_hash=hash_password("pass"))
            db.add(user)
            db.flush()
            membership = OrganizationMembership(
                user_id=user.id,
                organization_id=1,
                role=RoleEnum.DEVELOPER
            )
            db.add(membership)
            db.commit()
        return user.id
    finally:
        db.close()

def run_checks():
    target_id = get_or_create_target_user()
    if target_id == 1:
        raise ValueError("CRITICAL: Safety violation. Target user ID is 1.")
        
    roles = ["org_admin", "team_lead", "reviewer", "developer"]
    tokens = {}
    
    for role in roles:
        email = f"{role}@example.com"
        token = create_user_and_get_token(email, "Password123!", role)
        tokens[role] = token
        
    for role in roles:
        print(f"\n--- Testing Role: {role} ---")
        headers = {"Authorization": f"Bearer {tokens[role]}"}
        cookies = {"access_token": tokens[role]}
        
        # Test members list (org level)
        res = requests.get(f"{BASE_URL}/organizations/1/members", cookies=cookies)
        print(f"GET /organizations/1/members -> {res.status_code}")
        
        # Test update member role (org admin only)
        res = requests.put(f"{BASE_URL}/organizations/1/members/{target_id}/role", json={"role": "developer"}, cookies=cookies)
        print(f"PUT /organizations/1/members/{target_id}/role -> {res.status_code}")
        
        # Test create project
        res = requests.post(f"{BASE_URL}/organizations/1/projects", json={"name": f"Project {role}"}, cookies=cookies)
        print(f"POST /organizations/1/projects -> {res.status_code}")

if __name__ == "__main__":
    run_checks()
