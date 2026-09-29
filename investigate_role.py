import sys
import os

# Add the project root to sys.path so we can import backend
sys.path.append(os.path.abspath('.'))

from backend.app.db import SessionLocal
from backend.app.auth.models import User, OrganizationMembership, Organization

def investigate_role():
    db = SessionLocal()
    
    user = db.query(User).filter(User.id == 1).first()
    print(f"User 1: id={user.id if user else None}, email={user.email if user else None}")
    
    if user:
        member = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == 1,
            OrganizationMembership.organization_id == 1
        ).first()
        if member:
            print(f"OrgMember(user=1, org=1): role={member.role}")
        else:
            print("No OrganizationMember found for user=1, org=1")
    
    users = db.query(User).filter(User.email == "harshita.baghel@example.com").all()
    print(f"\nTotal users with email 'harshita.baghel@example.com': {len(users)}")
    for u in users:
        print(f"  User id={u.id}, email={u.email}")
        mems = db.query(OrganizationMembership).filter(OrganizationMembership.user_id == u.id).all()
        for m in mems:
            print(f"    OrganizationMembership org={m.organization_id}, role={m.role}")

    db.close()

if __name__ == "__main__":
    investigate_role()
