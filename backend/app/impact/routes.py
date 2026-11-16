"""
Change Impact & Blast Radius Analyzer API Routes — RepoMind 2.0.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.organizations.models import Repository, Project
from backend.app.organizations.service import verify_org_member
from backend.app.github.models import PullRequest
from backend.app.impact.models import ChangeImpactAnalysis
from backend.app.impact.schemas import (
    ImpactAnalysisTriggerRequest,
    ChangeImpactAnalysisResponse,
    GraphVisualizationResponse,
)
from backend.app.impact.engine import run_change_impact_analysis

router = APIRouter(tags=["change-impact"])


def _get_authorized_repo(db: Session, repository_id: int, current_user: User) -> Repository:
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    project = db.get(Project, repo.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    verify_org_member(db, current_user.id, project.organization_id)
    return repo


@router.post(
    "/repositories/{repository_id}/impact/analyze",
    response_model=ChangeImpactAnalysisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger Change Impact and Blast Radius analysis for a diff",
)
def trigger_impact_analysis(
    repository_id: int,
    payload: ImpactAnalysisTriggerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger change impact and blast radius analysis on demand."""
    _get_authorized_repo(db, repository_id, current_user)

    analysis = run_change_impact_analysis(
        db=db,
        repository_id=repository_id,
        diff=payload.diff,
        pull_request_id=payload.pull_request_id,
        commit_sha=payload.commit_sha,
        target_branch=payload.target_branch or "main",
        max_depth=payload.max_depth or 3,
    )
    return analysis


@router.get(
    "/repositories/{repository_id}/pull-requests/{pull_request_id}/impact",
    response_model=ChangeImpactAnalysisResponse,
    summary="Get the latest Change Impact analysis for a pull request",
)
def get_latest_pr_impact(
    repository_id: int,
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the latest Change Impact analysis record for a given pull request."""
    _get_authorized_repo(db, repository_id, current_user)

    pr = db.get(PullRequest, pull_request_id)
    if not pr or pr.repository_id != repository_id:
        raise HTTPException(status_code=404, detail="Pull request not found")

    analysis = (
        db.query(ChangeImpactAnalysis)
        .filter(
            ChangeImpactAnalysis.repository_id == repository_id,
            ChangeImpactAnalysis.pull_request_id == pull_request_id,
        )
        .order_by(ChangeImpactAnalysis.id.desc())
        .first()
    )

    if not analysis:
        # Return an empty/baseline analysis placeholder
        return ChangeImpactAnalysisResponse(
            id=0,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            risk_level="low",
            directly_affected_count=0,
            indirectly_affected_count=0,
            breaking_changes_count=0,
            affected_components=[],
            breaking_changes=[],
            test_recommendations=[],
            summary="No impact analysis recorded yet for this pull request.",
            created_at=pr.created_at,
        )

    return analysis


@router.get(
    "/impact/{analysis_id}",
    response_model=ChangeImpactAnalysisResponse,
    summary="Get Change Impact analysis by ID",
)
def get_impact_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a specific Change Impact analysis record."""
    analysis = db.get(ChangeImpactAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Impact analysis record not found")

    _get_authorized_repo(db, analysis.repository_id, current_user)
    return analysis


@router.get(
    "/impact/{analysis_id}/graph",
    response_model=GraphVisualizationResponse,
    summary="Get interactive dependency visualization for an impact analysis",
)
def get_impact_graph(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the interactive subgraph payload and Mermaid flowchart for an impact analysis."""
    analysis = db.get(ChangeImpactAnalysis, analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Impact analysis record not found")

    _get_authorized_repo(db, analysis.repository_id, current_user)

    viz = analysis.graph_visualization or {}
    return GraphVisualizationResponse(
        nodes=viz.get("nodes", []),
        edges=viz.get("edges", []),
        mermaid=viz.get("mermaid", "flowchart LR\n    Empty[\"No graph data\"]"),
    )
