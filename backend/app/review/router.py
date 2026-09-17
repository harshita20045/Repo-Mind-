from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from backend.app.db import get_db
from backend.app.auth.models import User
from backend.app.auth.dependencies import get_current_user
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun, HumanDecision
from backend.app.review.schemas import (
    ReviewTriggerResponse, 
    ReviewRunResponse,
    HumanDecisionRequest,
    HumanDecisionResponse
)
from backend.app.review.prompts import REPOMIND_VERSION, PROMPT_VERSION
from backend.app.organizations.service import verify_org_member
from backend.app.review.service import _get_org_id_for_pr, ReviewError
from backend.app.github.service import get_decrypted_pat_for_org
from backend.app.github.client import GitHubClient
from backend.app.organizations.service import get_repository_by_id

router = APIRouter(tags=["review"])
logger = logging.getLogger(__name__)

@router.post(
    "/pull-requests/{pull_request_id}/review",
    response_model=ReviewTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def trigger_review(
    pull_request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Trigger a review for a pull request.
    Creates a pending job reference and returns immediately (Phase 13 worker handles execution).
    """
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    try:
        org_id = _get_org_id_for_pr(db, pr)
    except ReviewError as e:
        raise HTTPException(status_code=404, detail="Pull request or related resources not found")

    # Authorize organization access
    verify_org_member(db, current_user.id, org_id)

    # Determine current commit SHA via GitHub API (since PR might be stale in DB)
    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")

    try:
        pat = get_decrypted_pat_for_org(db, org_id)
        client = GitHubClient(pat)
        pr_data = client.get_pull_request(repo.github_owner, repo.github_name, pr.github_number)
        current_sha = pr_data["head"]["sha"]
        # Update our DB cache of the head_sha
        pr.head_sha = current_sha
        db.commit()
    except Exception as exc:
        logger.warning("Failed to fetch current PR SHA: %s", type(exc).__name__)
        # Fallback to DB value if GH fetch fails, or fail request
        current_sha = pr.head_sha
        if not current_sha:
            raise HTTPException(status_code=502, detail="Failed to retrieve PR head SHA from GitHub")

    # Enforce duplicate-review invariant: check for existing ReviewRun with same PR and SHA
    existing_run = db.query(ReviewRun).filter(
        ReviewRun.pull_request_id == pull_request_id,
        ReviewRun.commit_sha == current_sha
    ).order_by(ReviewRun.id.desc()).first()

    if existing_run:
        # Idempotently return the existing run if found
        return ReviewTriggerResponse(
            job_id=existing_run.id,
            status=existing_run.status
        )

    # Create new ReviewRun (status="pending")
    run = ReviewRun(
        pull_request_id=pull_request_id,
        commit_sha=current_sha,
        status="pending",
        repomind_version=REPOMIND_VERSION,
        prompt_version=PROMPT_VERSION,
        llm_model="API_Trigger",  # Will be updated by worker in Phase 13
        rag_enabled=True,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    return ReviewTriggerResponse(job_id=run.id, status=run.status)


@router.get("/review-runs/{review_run_id}", response_model=ReviewRunResponse)
def get_review_run(
    review_run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve review run details and findings."""
    run = db.get(ReviewRun, review_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Review run not found")

    pr = db.get(PullRequest, run.pull_request_id)
    if not pr:
        raise HTTPException(status_code=404, detail="Pull request not found")

    try:
        org_id = _get_org_id_for_pr(db, pr)
    except ReviewError:
        raise HTTPException(status_code=404, detail="Review run not found")

    # Authorize organization access
    verify_org_member(db, current_user.id, org_id)

    return run

@router.post("/review-runs/{review_run_id}/approve", response_model=HumanDecisionResponse)
def approve_review_run(
    review_run_id: int,
    decision: HumanDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve or reject a review run."""
    # Ensure user is reviewer or admin
    if current_user.role not in ("reviewer", "team_lead", "org_admin"):
        raise HTTPException(status_code=403, detail="Not authorized to approve reviews")

    run = db.get(ReviewRun, review_run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Review run not found")
        
    if run.status != "completed":
        raise HTTPException(status_code=400, detail="Cannot approve a review run that is not completed")

    pr = db.get(PullRequest, run.pull_request_id)
    try:
        org_id = _get_org_id_for_pr(db, pr)
    except ReviewError:
        raise HTTPException(status_code=404, detail="Review run not found")

    # Authorize organization access
    verify_org_member(db, current_user.id, org_id)

    # Check for existing decision
    existing = db.query(HumanDecision).filter_by(
        review_run_id=review_run_id,
        user_id=current_user.id
    ).first()

    if existing:
        existing.action = decision.action
        existing.note = decision.note
        existing.created_at = datetime.now(timezone.utc)
        human_decision = existing
    else:
        human_decision = HumanDecision(
            review_run_id=review_run_id,
            user_id=current_user.id,
            action=decision.action,
            note=decision.note,
            created_at=datetime.now(timezone.utc)
        )
        db.add(human_decision)
        
    db.commit()
    db.refresh(human_decision)

    return human_decision
