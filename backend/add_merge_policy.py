import re

file_path = 'backend/app/github/automation.py'
with open(file_path, 'r') as f:
    content = f.read()

merge_policy_logic = """
def evaluate_merge_policy(db: Session, pull_request_id: int):
    \"\"\"
    Evaluate the merge policy for a Pull Request.
    If it passes and auto-merge is enabled, queues a MERGE AutomationAction.
    \"\"\"
    from backend.app.github.models import ProjectMergePolicy, HumanReview, AIAnalysis, PullRequestCheck

    pr = db.query(PullRequest).filter(PullRequest.id == pull_request_id).first()
    if not pr or not pr.head_sha:
        return

    repo = db.query(Repository).filter(Repository.id == pr.repository_id).first()
    if not repo:
        return

    policy = db.query(ProjectMergePolicy).filter(ProjectMergePolicy.project_id == repo.project_id).first()
    if not policy or not policy.auto_merge_enabled:
        return

    # Check Human Approval
    if policy.require_human_approval:
        approvals = (
            db.query(HumanReview)
            .filter(
                HumanReview.pull_request_id == pr.id,
                HumanReview.commit_sha == pr.head_sha if policy.require_latest_commit_review else True,
                HumanReview.decision == "approve"
            ).count()
        )
        if approvals < policy.required_approvals:
            logger.info(f"PR {pr.id} blocked: not enough human approvals.")
            return
            
        # Check for any request_changes on the latest commit
        rejections = (
            db.query(HumanReview)
            .filter(
                HumanReview.pull_request_id == pr.id,
                HumanReview.commit_sha == pr.head_sha if policy.require_latest_commit_review else True,
                HumanReview.decision == "request_changes"
            ).count()
        )
        if rejections > 0:
            logger.info(f"PR {pr.id} blocked: changes requested.")
            return

    # Check AI Analysis
    if policy.require_ai_analysis:
        ai = (
            db.query(AIAnalysis)
            .filter(
                AIAnalysis.pull_request_id == pr.id,
                AIAnalysis.commit_sha == pr.head_sha,
                AIAnalysis.status == "completed"
            ).first()
        )
        if not ai:
            logger.info(f"PR {pr.id} blocked: AI analysis not completed for head sha.")
            return

    # Check CI Success
    if policy.require_ci_success:
        failed_checks = (
            db.query(PullRequestCheck)
            .filter(
                PullRequestCheck.pull_request_id == pr.id,
                PullRequestCheck.head_sha == pr.head_sha,
                PullRequestCheck.conclusion.in_(["failure", "timed_out", "action_required"])
            ).count()
        )
        if failed_checks > 0:
            logger.info(f"PR {pr.id} blocked: CI checks failed.")
            return

    # Check if a MERGE action is already queued or successful for this SHA
    existing_merge = (
        db.query(AutomationAction)
        .filter(
            AutomationAction.pull_request_id == pr.id,
            AutomationAction.action_type == "MERGE",
            AutomationAction.expected_head_sha == pr.head_sha,
            AutomationAction.status.in_(["PENDING", "RUNNING", "COMPLETED"])
        ).first()
    )
    if existing_merge:
        return

    # Policy passed! Queue MERGE action
    logger.info(f"PR {pr.id} passed merge policy. Queuing auto-merge.")
    action = AutomationAction(
        organization_id=repo.project.organization_id if repo.project else 0, # Note: handled via relations
        project_id=repo.project_id,
        repository_id=repo.id,
        pull_request_id=pr.id,
        action_type="MERGE",
        expected_head_sha=pr.head_sha,
        status="PENDING"
    )
    db.add(action)
    db.commit()
"""

with open(file_path, 'a') as f:
    f.write(merge_policy_logic)
