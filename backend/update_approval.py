import re

file_path = 'backend/app/review/router.py'
with open(file_path, 'r') as f:
    content = f.read()

new_approve_logic = """
@router.post("/review-runs/{review_run_id}/approve", response_model=HumanDecisionResponse)
def approve_review_run(
    review_run_id: int,
    decision: HumanDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    \"\"\"Approve or reject a review run and trigger a GitHub review via AutomationAction.\"\"\"
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

    verify_org_member(db, current_user.id, org_id)

    # 1. Update legacy HumanDecision (if necessary for backwards compatibility)
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

    # 2. Phase 13: Create HumanReview tracking the commit_sha
    from backend.app.github.models import HumanReview, AutomationAction
    human_review = (
        db.query(HumanReview)
        .filter_by(
            pull_request_id=pr.id,
            commit_sha=run.commit_sha,
            reviewer_id=current_user.id
        ).first()
    )
    if not human_review:
        human_review = HumanReview(
            pull_request_id=pr.id,
            commit_sha=run.commit_sha,
            reviewer_id=current_user.id,
            decision=decision.action,
            comment=decision.note
        )
        db.add(human_review)
    else:
        human_review.decision = decision.action
        human_review.comment = decision.note

    # 3. Create AutomationAction to sync this review to GitHub
    action_type = "APPROVE" if decision.action == "approve" else "REQUEST_CHANGES"
    
    # We need to find the github_identity_id for the current user
    from backend.app.github.models import GitHubIdentity
    identity = db.query(GitHubIdentity).filter_by(user_id=current_user.id).first()
    identity_id = identity.id if identity else None

    # Get project ID from repo
    repo = get_repository_by_id(db, pr.repository_id)
    
    automation_action = AutomationAction(
        organization_id=org_id,
        project_id=repo.project_id,
        repository_id=pr.repository_id,
        pull_request_id=pr.id,
        action_type=action_type,
        requested_by_user_id=current_user.id,
        github_identity_id=identity_id,
        commit_sha=run.commit_sha,
        status="PENDING"
    )
    db.add(automation_action)

    db.commit()
    db.refresh(human_decision)

    return human_decision
"""

content = re.sub(
    r'@router\.post\("/review-runs/\{review_run_id\}/approve".*',
    new_approve_logic,
    content,
    flags=re.DOTALL
)

with open(file_path, 'w') as f:
    f.write(content)
