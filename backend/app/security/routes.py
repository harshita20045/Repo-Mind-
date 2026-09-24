from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.organizations.service import verify_org_member
from backend.app.review.models import Finding, ReviewRun
from backend.app.github.models import PullRequest
from backend.app.organizations.models import Repository, Project

router = APIRouter(tags=["security"])

class FindingStatusUpdate(BaseModel):
    status: str # "accept", "reject", "ignore"

class SecurityFindingResponse(BaseModel):
    id: int
    title: str
    severity: str
    type: str
    file: str
    line: Optional[int]
    status: str
    repository_name: str
    pull_request_number: int
    created_at: str

@router.get("/security/findings", response_model=List[SecurityFindingResponse])
def list_security_findings(
    org_id: int = Query(...),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get organization-wide security findings.
    """
    verify_org_member(db, current_user.id, org_id)

    query = db.query(
        Finding, Repository.github_name, PullRequest.github_number
    ).join(
        ReviewRun, Finding.review_run_id == ReviewRun.id
    ).join(
        PullRequest, ReviewRun.pull_request_id == PullRequest.id
    ).join(
        Repository, PullRequest.repository_id == Repository.id
    ).join(
        Project, Repository.project_id == Project.id
    ).filter(
        Project.organization_id == org_id
    )

    if severity:
        query = query.filter(Finding.severity == severity)
    if status:
        query = query.filter(Finding.status == status)

    query = query.order_by(desc(Finding.id))
    
    results = query.all()
    
    return [
        {
            "id": f.id,
            "title": f.title,
            "severity": f.severity,
            "type": f.type,
            "file": f.file,
            "line": f.line,
            "status": f.status,
            "repository_name": r_name,
            "pull_request_number": pr_num,
            "created_at": getattr(f, 'created_at', None) or ""
        }
        for f, r_name, pr_num in results
    ]

@router.put("/security/findings/{finding_id}/status")
def update_finding_status(
    finding_id: int,
    payload: FindingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    finding = db.get(Finding, finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
        
    run = db.get(ReviewRun, finding.review_run_id)
    pr = db.get(PullRequest, run.pull_request_id)
    repo = db.get(Repository, pr.repository_id)
    project = db.get(Project, repo.project_id)
    
    verify_org_member(db, current_user.id, project.organization_id)
    
    if payload.status not in ["accept", "reject", "ignore"]:
        raise HTTPException(status_code=400, detail="Invalid status")
        
    finding.status = payload.status
    db.commit()
    
    return {"message": "Finding status updated"}
