from sqlalchemy.orm import Session
from typing import List, Optional
from backend.app.organizations.models import Project, Repository, GithubConnection
from backend.app.auth.models import Organization, OrganizationMembership, RoleEnum, User
from fastapi import HTTPException, status
import secrets
from datetime import datetime, timedelta, timezone

ROLE_HIERARCHY = {
    RoleEnum.DEVELOPER: 1,
    RoleEnum.REVIEWER: 2,
    RoleEnum.TEAM_LEAD: 3,
    RoleEnum.ORG_ADMIN: 4
}

def verify_org_role(db: Session, user_id: int, organization_id: int, required_role: RoleEnum = RoleEnum.DEVELOPER):
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == user_id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    
    if not membership:
        # Prevent guessing IDs / cross-org access by returning a uniform 404
        # Wait, if they are not in the org, should it be 404 or 403?
        # Standard security practice: return 404 to not disclose org existence
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found or access denied")
        
    user_level = ROLE_HIERARCHY.get(membership.role, 0)
    required_level = ROLE_HIERARCHY.get(required_role, 0)
    
    if user_level < required_level:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {required_role.value} role or higher")

def verify_org_admin(db: Session, user_id: int, organization_id: int):
    verify_org_role(db, user_id, organization_id, RoleEnum.ORG_ADMIN)

def verify_org_member(db: Session, user_id: int, organization_id: int):
    verify_org_role(db, user_id, organization_id, RoleEnum.DEVELOPER)

def get_projects(db: Session, organization_id: int) -> List[Project]:
    return db.query(Project).filter(Project.organization_id == organization_id).all()

def create_project(db: Session, organization_id: int, name: str) -> Project:
    project = Project(organization_id=organization_id, name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_project_by_id(db: Session, project_id: int) -> Optional[Project]:
    return db.query(Project).filter(Project.id == project_id).first()

def get_repositories(db: Session, project_id: int) -> List[Repository]:
    return db.query(Repository).filter(Repository.project_id == project_id).all()

def get_repository_by_id(db: Session, repository_id: int) -> Optional[Repository]:
    return db.query(Repository).filter(Repository.id == repository_id).first()

def create_repository(db: Session, project_id: int, github_owner: str, github_name: str, default_branch: str) -> Repository:
    repo = Repository(
        project_id=project_id,
        github_owner=github_owner,
        github_name=github_name,
        default_branch=default_branch
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo

def get_members(db: Session, organization_id: int):
    memberships = db.query(OrganizationMembership).filter(OrganizationMembership.organization_id == organization_id).all()
    # attach user email
    for m in memberships:
        m.email = m.user.email if m.user else "Unknown"
    return memberships

def add_member(db: Session, user_id: int, organization_id: int, target_email: str, role: RoleEnum, actor_id: int):
    from backend.app.auth.service import get_user_by_email, hash_invitation_token
    target_user = get_user_by_email(db, target_email)
    
    raw_invitation_token = None
    
    if not target_user:
        raw_invitation_token = secrets.token_urlsafe(32)
        target_user = User(
            email=target_email,
            password_hash=None,
            invitation_token_hash=hash_invitation_token(raw_invitation_token),
            invitation_expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        db.add(target_user)
        db.flush()
        
    existing = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == target_user.id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="User is already a member")
        
    membership = OrganizationMembership(
        user_id=target_user.id,
        organization_id=organization_id,
        role=role
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    # Audit log
    from backend.app.audit.models import AuditLog
    db.add(AuditLog(user_id=actor_id, action=f"Added member {target_user.email} with role {role.value}", target_type="organization", target_id=organization_id))
    db.commit()
    
    membership.email = target_user.email
    return {
        "membership": membership,
        "invitation_token": raw_invitation_token
    }

def update_member_role(db: Session, user_id: int, organization_id: int, target_user_id: int, new_role: RoleEnum, actor_id: int):
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="Cannot change own role")
        
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == target_user_id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
        
    old_role = membership.role
    membership.role = new_role
    db.commit()
    db.refresh(membership)
    
    # Audit log
    from backend.app.audit.models import AuditLog
    db.add(AuditLog(user_id=actor_id, action=f"Changed member role from {old_role.value if hasattr(old_role, 'value') else old_role} to {new_role.value}", target_type="organization_membership", target_id=membership.id))
    db.commit()
    
    membership.email = membership.user.email if membership.user else "Unknown"
    return membership

def remove_member(db: Session, user_id: int, organization_id: int, target_user_id: int, actor_id: int):
    if user_id == target_user_id:
        raise HTTPException(status_code=400, detail="Cannot remove self")
        
    membership = db.query(OrganizationMembership).filter(
        OrganizationMembership.user_id == target_user_id,
        OrganizationMembership.organization_id == organization_id
    ).first()
    if not membership:
        raise HTTPException(status_code=404, detail="Membership not found")
        
    email = membership.user.email if membership.user else "Unknown"
    db.delete(membership)
    db.commit()
    
    # Audit log
    from backend.app.audit.models import AuditLog
    db.add(AuditLog(user_id=actor_id, action=f"Removed member {email}", target_type="organization", target_id=organization_id))
    db.commit()

