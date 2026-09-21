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


def _enqueue_review(db: Session, repository_id: int, pr_github_number: int) -> Optional[ReviewRun]:
    """
    Find the PullRequest DB row and create a pending ReviewRun.
    Returns the ReviewRun if created, None if PR not found.
    """
    pr = (
        db.query(PullRequest)
        .filter(
            PullRequest.repository_id == repository_id,
            PullRequest.github_number == pr_github_number,
        )
        .first()
    )

    if not pr:
        logger.warning(
            "Webhook: PR #%d not found in DB for repository_id=%d. "
            "Sync the repository first.",
            pr_github_number,
            repository_id,
        )
        return None

    # Check if a review is already pending/running (avoid duplicates)
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

    # --- 3. Deduplicate by delivery ID ---
    if x_github_delivery:
        existing_event = (
            db.query(WebhookEvent)
            .filter(WebhookEvent.github_delivery_id == x_github_delivery)
            .first()
        )
        if existing_event:
            logger.info(
                "Webhook: duplicate delivery %s (already processed as %s). Returning 200.",
                x_github_delivery,
                existing_event.status,
            )
            return {"status": "duplicate", "event_id": existing_event.id}

    # --- 4. Resolve repository ---
    repository = _resolve_repository(db, payload)
    repository_id = repository.id if repository else None

    # --- 5. Persist webhook event ---
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
    db.flush()

    # --- 6. Handle ping (GitHub health check) ---
    if event_type == "ping":
        event.status = "skipped"
        db.commit()
        return {"status": "pong"}

    # --- 7. Handle pull_request events ---
    if event_type == "pull_request" and action in REVIEW_TRIGGER_ACTIONS:
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
                                                                  
        review_run = _enqueue_review(db, repository_id, pr_number)
        if review_run:
            event.status = "processed"
            event.processed_at = datetime.now(timezone.utc)
        else:
            event.status = "skipped"
            event.error_message = f"PR #{pr_number} not found in DB (sync first)"

        db.commit()
        return {
            "status": "processed" if review_run else "skipped",
            "event_type": event_type,
            "action": action,
            "review_run_id": review_run.id if review_run else None,
        }

    # --- 8. All other events — stored but skipped ---
    event.status = "skipped"
    db.commit()
    return {"status": "skipped", "event_type": event_type}
