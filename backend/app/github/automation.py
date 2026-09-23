import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from backend.app.github.models import AutomationAction, PullRequest, GitHubCredential, GitHubIdentity
from backend.app.organizations.models import Repository
from backend.app.github.client import GitHubClient, GitHubAPIError, GitHubTransientError
from backend.app.github.encryption import decrypt_token

logger = logging.getLogger(__name__)

def _get_token_for_identity(db: Session, identity_id: int) -> str:
    credential = db.query(GitHubCredential).filter(GitHubCredential.github_identity_id == identity_id).first()
    if not credential:
        raise ValueError(f"No GitHub credential found for identity {identity_id}")
    return decrypt_token(credential.encrypted_access_token)

def process_automation_actions(db: Session):
    """
    Process pending AutomationActions in the central queue.
    Should be called periodically by a background task/cron.
    """
    pending_actions = (
        db.query(AutomationAction)
        .filter(AutomationAction.status == "PENDING")
        .order_by(AutomationAction.created_at.asc())
        .limit(10)
        .all()
    )

    if not pending_actions:
        return

    logger.info(f"Processing {len(pending_actions)} pending automation actions.")

    for action in pending_actions:
        action.status = "RUNNING"
        action.started_at = datetime.now(timezone.utc)
        action.attempt_count += 1
        db.commit()

        try:
            repo = db.query(Repository).filter(Repository.id == action.repository_id).first()
            pr = db.query(PullRequest).filter(PullRequest.id == action.pull_request_id).first()
            
            if not repo or not pr:
                raise ValueError("Repository or PullRequest not found.")

            # Resolve token
            if action.github_identity_id:
                pat = _get_token_for_identity(db, action.github_identity_id)
            else:
                # Fallback to system token for this repo (e.g., for auto-merge)
                from backend.app.webhooks.routes import _get_system_user_id_for_repo
                sys_user_id = _get_system_user_id_for_repo(db, repo.id)
                if not sys_user_id:
                    raise ValueError("No system user found with repository access.")
                sys_identity = db.query(GitHubIdentity).filter(GitHubIdentity.user_id == sys_user_id).first()
                if not sys_identity:
                    raise ValueError("System user has no GitHub Identity.")
                pat = _get_token_for_identity(db, sys_identity.id)

            client = GitHubClient(pat)

            if action.action_type in ("APPROVE", "REQUEST_CHANGES"):
                if not action.commit_sha:
                    raise ValueError("commit_sha is required for APPROVE/REQUEST_CHANGES.")
                    
                res = client.submit_pull_request_review(
                    owner=repo.github_owner,
                    repo=repo.github_name,
                    pr_number=pr.github_number,
                    commit_id=action.commit_sha,
                    event=action.action_type
                )
                action.github_resource_id = str(res.get("id"))
                
            elif action.action_type == "MERGE":
                if not action.expected_head_sha:
                    raise ValueError("expected_head_sha is required for MERGE.")
                    
                res = client.merge_pull_request(
                    owner=repo.github_owner,
                    repo=repo.github_name,
                    pr_number=pr.github_number,
                    sha=action.expected_head_sha
                )
                action.github_resource_id = res.get("sha")
            else:
                raise ValueError(f"Unknown action_type: {action.action_type}")

            action.status = "COMPLETED"
            action.completed_at = datetime.now(timezone.utc)
            
        except GitHubAPIError as e:
            action.status = "FAILED"
            action.error_code = str(e.status_code)
            action.error_message = str(e)[:1000]
            logger.error(f"AutomationAction {action.id} failed: {e}")
        except GitHubTransientError as e:
            # Leave as PENDING or retry logic could go here
            action.status = "PENDING"
            action.error_message = str(e)[:1000]
            logger.warning(f"AutomationAction {action.id} transient error: {e}")
        except Exception as e:
            action.status = "FAILED"
            action.error_message = str(e)[:1000]
            logger.exception(f"AutomationAction {action.id} failed with unexpected error.")

        db.commit()

def evaluate_merge_policy(db: Session, pull_request_id: int):
    """
    Evaluate the merge policy for a Pull Request.
    If it passes and auto-merge is enabled, queues a MERGE AutomationAction.
    """
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
