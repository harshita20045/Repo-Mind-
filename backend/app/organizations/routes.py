from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, RoleEnum
from backend.app.organizations import schemas, service

router = APIRouter(tags=["organizations"])

@router.get("/organizations/{organization_id}/projects", response_model=List[schemas.ProjectResponse])
def list_projects(organization_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_member(db, current_user.id, organization_id)
    return service.get_projects(db, organization_id)

@router.post("/organizations/{organization_id}/projects", response_model=schemas.ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(organization_id: int, project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_admin(db, current_user.id, organization_id)
    return service.create_project(db, organization_id, project.name)

@router.get("/projects/{project_id}/repositories", response_model=List[schemas.RepositoryResponse])
def list_repositories(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service.verify_org_member(db, current_user.id, project.organization_id)
    return service.get_repositories(db, project_id)

@router.post("/projects/{project_id}/repositories", response_model=schemas.RepositoryResponse, status_code=status.HTTP_201_CREATED)
def create_repository(project_id: int, repo: schemas.RepositoryCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = service.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    service.verify_org_admin(db, current_user.id, project.organization_id)
    return service.create_repository(db, project_id, repo.github_owner, repo.github_name, repo.default_branch)

@router.get("/organizations/{organization_id}/members", response_model=List[schemas.OrganizationMemberResponse])
def list_members(organization_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_member(db, current_user.id, organization_id)
    return service.get_members(db, organization_id)

@router.post("/organizations/{organization_id}/members", response_model=schemas.OrganizationMemberInviteResponse, status_code=status.HTTP_201_CREATED)
def invite_member(organization_id: int, invite: schemas.MemberInvite, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_admin(db, current_user.id, organization_id)
    role = RoleEnum(invite.role)
    result = service.add_member(db, current_user.id, organization_id, invite.email, role, current_user.id)
    return result

@router.put("/organizations/{organization_id}/members/{target_user_id}/role", response_model=schemas.OrganizationMemberResponse)
def update_member_role(organization_id: int, target_user_id: int, role_update: schemas.MemberRoleUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_admin(db, current_user.id, organization_id)
    role = RoleEnum(role_update.role)
    return service.update_member_role(db, current_user.id, organization_id, target_user_id, role, current_user.id)

@router.delete("/organizations/{organization_id}/members/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(organization_id: int, target_user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    service.verify_org_admin(db, current_user.id, organization_id)
    service.remove_member(db, current_user.id, organization_id, target_user_id, current_user.id)
    return None

@router.get("/repositories/{repository_id}", response_model=schemas.RepositoryResponse)
def get_repository(repository_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repo = service.get_repository_by_id(db, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = service.get_project_by_id(db, repo.project_id)
    service.verify_org_member(db, current_user.id, project.organization_id)
    return repo
