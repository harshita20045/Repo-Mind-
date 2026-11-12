"""
GitHub Webhook Handler — RepoMind 2.0

Receives GitHub webhook events and automatically triggers PR reviews.

Security:
  - Every incoming request is verified using HMAC-SHA256 with GITHUB_WEBHOOK_SECRET.
  - The raw request body is used for signature verification (before JSON parsing).
  - Webhook events are persisted BEFORE processing (enables deduplication + replay).
  - Deduplication via X-GitHub-Delivery header.
  - Only pull_request events are acted upon; others are stored but skipped.

Required configuration:
  GITHUB_WEBHOOK_SECRET — must match the secret set in GitHub repo settings.

Supported events:
  pull_request.opened       → trigger review
  pull_request.synchronize  → trigger review (new commits pushed)
  pull_request.reopened     → trigger review
  ping                      → return 200 (health check from GitHub)

All other events are stored with status='skipped'.
"""
import hashlib
import hmac
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import settings
from backend.app.db import get_db
from backend.app.webhooks.models import WebhookEvent
from backend.app.review.models import ReviewRun
from backend.app.organizations.models import Repository
from backend.app.github.models import PullRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhooks"])

# Events that trigger a PR review
REVIEW_TRIGGER_ACTIONS = frozenset(["opened", "synchronize", "reopened"])


def _verify_github_signature(raw_body: bytes, signature: Optional[str]) -> bool:
    """
    Verify the GitHub webhook signature using HMAC-SHA256.

    GitHub sends the signature in: X-Hub-Signature-256: sha256=<hex>
    We compute the expected signature and compare using constant-time comparison
    to prevent timing attacks.
    """
    if not signature:
        return False

    secret = getattr(settings, "GITHUB_WEBHOOK_SECRET", None)
    if not secret:
        logger.warning(
            "GITHUB_WEBHOOK_SECRET not configured. All webhook signatures will fail."
        )
        return False

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature)


def _resolve_repository(db: Session, payload: dict) -> Optional[Repository]:
    """
    Resolve the repository from the webhook payload.
    Matches by github_owner + github_name (case-insensitive where possible).
    """
    repo_data = payload.get("repository", {})
    github_owner = repo_data.get("owner", {}).get("login", "")
    github_name = repo_data.get("name", "")

    if not github_owner or not github_name:
        return None

    return (
        db.query(Repository)
        .filter(
            Repository.github_owner == github_owner,
            Repository.github_name == github_name,
        )
        .first()
    )



def _get_system_user_id_for_repo(db: Session, repository_id: int) -> Optional[int]:
    from backend.app.organizations.models import Repository, Project
    from backend.app.auth.models import OrganizationMembership, User
    from backend.app.github.models import GitHubIdentity, GitHubCredential
    
    res = (
        db.query(User.id)
        .join(OrganizationMembership, OrganizationMembership.user_id == User.id)
        .join(Project, Project.organization_id == OrganizationMembership.organization_id)
        .join(Repository, Repository.project_id == Project.id)
        .join(GitHubIdentity, GitHubIdentity.user_id == User.id)
        .join(GitHubCredential, GitHubCredential.github_identity_id == GitHubIdentity.id)
        .filter(Repository.id == repository_id, OrganizationMembership.role == 'org_admin')
        .first()
    )
    return res[0] if res else None

def _upsert_pr_from_webhook(db: Session, repository_id: int, pr_payload: dict) -> PullRequest:
    from datetime import datetime
    
    pr_github_number = pr_payload.get("number")
    pr = (
        db.query(PullRequest)
        .filter(
            PullRequest.repository_id == repository_id,
            PullRequest.github_number == pr_github_number,
        )
        .first()
    )
    
    def parse_dt(s):
        return datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None

    if not pr:
        pr = PullRequest(
            repository_id=repository_id,
            github_pr_id=str(pr_payload.get("id")),
            github_number=pr_github_number,
        )
        db.add(pr)
        
    pr.title = pr_payload.get("title", "")[:512]
    pr.description = pr_payload.get("body")
    pr.github_url = pr_payload.get("html_url")
    pr.state = pr_payload.get("state", "open")
    pr.github_author_login = pr_payload.get("user", {}).get("login")
    pr.source_branch = pr_payload.get("head", {}).get("ref")
    pr.target_branch = pr_payload.get("base", {}).get("ref")
    pr.head_sha = pr_payload.get("head", {}).get("sha")
    pr.base_sha = pr_payload.get("base", {}).get("sha")

    # GAP-03: Only update diff/size metrics when present in the payload (non-None).
    # Partial payloads like pull_request_review_comment omit these fields (None);
    # do not overwrite existing metrics with None. Distinguish 0 from None.
    if pr_payload.get("additions") is not None:
        pr.additions = pr_payload.get("additions")
    if pr_payload.get("deletions") is not None:
        pr.deletions = pr_payload.get("deletions")
    if pr_payload.get("changed_files") is not None:
        pr.files_changed = pr_payload.get("changed_files")
    
    created_at = pr_payload.get("created_at")
    if created_at:
        pr.created_at = parse_dt(created_at)
    else:
        pr.created_at = datetime.utcnow()
        
    pr.updated_at = parse_dt(pr_payload.get("updated_at"))
    pr.merged_at = parse_dt(pr_payload.get("merged_at"))
    pr.closed_at = parse_dt(pr_payload.get("closed_at"))
    
    db.commit()
    db.refresh(pr)
    
    # Try deep sync if a system user exists
    sys_user_id = _get_system_user_id_for_repo(db, repository_id)
    if sys_user_id:
        from backend.app.github.service import sync_pull_request_details
        try:
            pr = sync_pull_request_details(db, pr.id, sys_user_id)
        except Exception as e:
            logger.error(f"Failed to deep sync PR {pr.id} during webhook ingestion: {e}")
            
    return pr

def _enqueue_review(db: Session, repository_id: int, pr_payload: dict, is_comment: bool = False) -> Optional[ReviewRun]:
    """
    Upsert the PullRequest from payload and manage review run execution.

    DEF-05: Comments must NEVER reset completed ReviewRuns to pending or trigger
    duplicate review execution over the same run. Comments are conversation/timeline
    events recorded via WebhookEvent.
    """
    pr_github_number = pr_payload.get("number")
    pr = _upsert_pr_from_webhook(db, repository_id, pr_payload)

    if is_comment:
        existing = (
            db.query(ReviewRun)
            .filter(ReviewRun.pull_request_id == pr.id)
            .order_by(ReviewRun.id.desc())
            .first()
        )
        if existing:
            logger.info(
                "Webhook: comment event for PR #%d associated with latest ReviewRun %d (status=%s). "
                "Event preserved without resetting run status or duplicating findings.",
                pr_github_number,
                existing.id,
                existing.status,
            )
            return existing
        else:
            logger.info("Webhook: No ReviewRun found for PR #%d comment.", pr_github_number)
            return None

    existing = (
        db.query(ReviewRun)
        .filter(
            ReviewRun.pull_request_id == pr.id,
            ReviewRun.status.in_(["pending", "running"]),
        )
        .first()
    )
    if existing:
        logger.info(
            "Webhook: ReviewRun %d already pending/running for PR #%d. Skipping duplicate.",
            existing.id,
            pr_github_number,
        )
        return existing

    # Create a new pending ReviewRun for the worker to pick up
    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="pending",
        progress_message="Queued via GitHub webhook",
    )
    db.add(run)
    db.flush()

    logger.info(
        "Webhook: created ReviewRun %d (pending) for PR #%d (repository_id=%d).",
        run.id,
        pr_github_number,
        repository_id,
    )
    return run


@router.post(
    "/webhooks/github",
    status_code=status.HTTP_200_OK,
    summary="GitHub webhook receiver",
    include_in_schema=False,  # Not in public API docs
)
async def github_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_github_event: Optional[str] = Header(None, alias="X-GitHub-Event"),
    x_hub_signature_256: Optional[str] = Header(None, alias="X-Hub-Signature-256"),
    x_github_delivery: Optional[str] = Header(None, alias="X-GitHub-Delivery"),
):
    """
    Receive and process GitHub webhook events.

    1. Verify HMAC-SHA256 signature.
    2. Deduplicate by X-GitHub-Delivery.
    3. Persist the event.
    4. For pull_request.opened/synchronize/reopened: enqueue a ReviewRun.
    5. Return 200 immediately (GitHub expects a fast response).
    """
    # --- Read raw body BEFORE parsing (required for signature verification) ---
    raw_body = await request.body()

    # --- 1. Signature verification ---
    if not _verify_github_signature(raw_body, x_hub_signature_256):
        logger.warning(
            "Webhook: signature verification failed for delivery %s.",
            x_github_delivery,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Webhook signature verification failed",
        )

    # --- 2. Parse payload ---
    try:
        import json
        payload = json.loads(raw_body)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    action = payload.get("action")
    event_type = x_github_event or "unknown"

    # --- 3. Deduplicate by delivery ID and handle retries ---
    is_retry = False
    event = None

    if x_github_delivery:
        existing_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.github_delivery_id == x_github_delivery)
            .first()
        )
        if existing_event:
            if existing_event.status in ("processed", "skipped"):
                logger.info(
                    "Webhook: duplicate delivery %s (already processed as %s). Returning 200.",
                    x_github_delivery,
                    existing_event.status,
                )
                return {"status": "duplicate", "event_id": existing_event.id}
            elif existing_event.status == "received":
                logger.info(
                    "Webhook: delivery %s is currently being processed. Returning 200.",
                    x_github_delivery,
                )
                return {"status": "duplicate", "event_id": existing_event.id, "detail": "processing"}
            elif existing_event.status == "failed":
                logger.info(
                    "Webhook: retrying previously failed delivery %s (event_id=%d).",
                    x_github_delivery,
                    existing_event.id,
                )
                is_retry = True
                event = existing_event
                event.error_message = None
                event.received_at = datetime.now(timezone.utc)

    # --- 4. Persist webhook event with concurrency protection if new ---
    if not event:
        repository = _resolve_repository(db, payload)
        repository_id = repository.id if repository else None

        event = WebhookEvent(
            github_delivery_id=x_github_delivery,
            event_type=event_type,
            action=action,
            repository_id=repository_id,
            payload=payload,
            status="received",
            received_at=datetime.now(timezone.utc),
        )
        db.add(event)
        try:
            db.commit()
            db.refresh(event)
        except IntegrityError:
            db.rollback()
            if x_github_delivery:
                concurrent_event = (
                    db.query(WebhookEvent)
                    .filter(WebhookEvent.github_delivery_id == x_github_delivery)
                    .first()
                )
                if concurrent_event:
                    logger.info(
                        "Webhook: concurrent duplicate delivery %s handled safely.",
                        x_github_delivery,
                    )
                    return {"status": "duplicate", "event_id": concurrent_event.id}
            raise

    # --- 5. Process event safely ---
    try:
        # Handle ping (GitHub health check)
        if event_type == "ping":
            event.status = "skipped"
            db.commit()
            return {"status": "pong"}

        # Handle pull_request and pull_request_review_comment events
        is_pr_event = (event_type == "pull_request" and action in REVIEW_TRIGGER_ACTIONS)
        is_comment_event = (event_type == "pull_request_review_comment" and action == "created")

        if is_pr_event or is_comment_event:
            repository = _resolve_repository(db, payload)
            if not repository:
                logger.warning(
                    "Webhook: repository not found in DB for delivery %s. "
                    "Event stored but not processed.",
                    x_github_delivery,
                )
                event.status = "skipped"
                event.error_message = "Repository not found in RepoMind database"
                db.commit()
                return {"status": "skipped", "reason": "repository_not_found"}

            pr_number = payload.get("pull_request", {}).get("number")
            if not pr_number:
                event.status = "skipped"
                event.error_message = "No PR number in payload"
                db.commit()
                return {"status": "skipped", "reason": "no_pr_number"}

            review_run = _enqueue_review(
                db, repository.id, payload.get("pull_request", {}), is_comment=is_comment_event
            )
            if review_run:
                event.status = "processed"
                event.processed_at = datetime.now(timezone.utc)
                event.error_message = None
            else:
                event.status = "skipped"
                event.error_message = f"PR #{pr_number} not found in DB (sync first)"

            db.commit()
            return {
                "status": "retried" if is_retry else ("processed" if review_run else "skipped"),
                "event_type": event_type,
                "action": action,
                "review_run_id": review_run.id if review_run else None,
            }

        # All other events — stored but skipped
        event.status = "skipped"
        db.commit()
        return {"status": "skipped", "event_type": event_type}

    except Exception as exc:
        db.rollback()
        event.status = "failed"
        event.error_message = str(exc)[:1000]
        db.add(event)
        db.commit()
        logger.exception("Webhook: unexpected error processing delivery %s", x_github_delivery)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook processing failed",
        )
