import sys
import os

sys.path.append(os.path.abspath('.'))

from backend.app.db import SessionLocal
from backend.app.auth.models import User, OrganizationMembership, Organization, RoleEnum

def repair():
    db = SessionLocal()
    
    # 1. Query and confirm
    user = db.query(User).filter(User.id == 1).first()
    org = db.query(Organization).filter(Organization.id == 1).first()
    
    if not user or not org:
        print("Missing user 1 or org 1")
        return
        
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Organization ID: {org.id}")
    print(f"Organization name: {org.name}")
    
    member = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == 1,
        OrganizationMembership.organization_id == 1
    ).first()
    
    if not member:
        print("Membership not found")
        return
        
    print(f"Current role: {member.role}")
    
    # 2. Restore ONLY this membership to org_admin
    if user.email == "harshita.baghel@example.com" and member.role != RoleEnum.ORG_ADMIN:
        member.role = RoleEnum.ORG_ADMIN
        db.commit()
        print("\nRestored role to org_admin")
    
    # 3. Query and verify
    member_after = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == 1,
        OrganizationMembership.organization_id == 1
    ).first()
    print(f"\nFinal state:")
    print(f"{user.email} -> {org.name} -> {member_after.role}")

    db.close()

if __name__ == "__main__":
    repair()
