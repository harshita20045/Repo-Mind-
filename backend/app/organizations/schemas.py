from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    id: int
    organization_id: int
    
    model_config = ConfigDict(from_attributes=True)

class RepositoryBase(BaseModel):
    github_owner: str
    github_name: str
    default_branch: str = "main"

class RepositoryCreate(RepositoryBase):
    pass

class RepositoryResponse(RepositoryBase):
    id: int
    project_id: int
    index_status: str
    last_indexed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class MemberBase(BaseModel):
    role: str

class MemberRoleUpdate(MemberBase):
    pass

class MemberInvite(MemberBase):
    email: str

class OrganizationMemberResponse(BaseModel):
    id: int
    user_id: int
    organization_id: int
    role: str
    email: str
    
    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberInviteResponse(BaseModel):
    membership: OrganizationMemberResponse
    invitation_token: Optional[str] = None

class GithubConnectionBase(BaseModel):
    encrypted_token: str
    scope: str = "repo"

class GithubConnectionCreate(GithubConnectionBase):
    pass

class GithubConnectionResponse(BaseModel):
    id: int
    organization_id: int
    scope: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
