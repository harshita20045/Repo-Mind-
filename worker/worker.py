"""
RepoMind 2.0 Background Worker

DB-polling job executor — no Docker, no Celery, no Redis required.
Runs as a standalone Python process alongside the FastAPI server.

Architecture:
    while True:
        SELECT review_run WHERE status='pending' FOR UPDATE SKIP LOCKED
        → mark 'running'
        → execute run_review() pipeline
        → mark 'completed' / 'failed'
        sleep(POLL_INTERVAL_SECONDS)

Worker startup behavior:
    - On startup, any review_run with status='running' is reset to 'pending'
      (handles crash recovery — a run stuck in 'running' means the worker died).
    - Jobs are processed one at a time per worker process.
      Multiple worker processes can run in parallel safely (SKIP LOCKED).

Usage:
    # From repo root with venv active:
    python -m worker.worker

Environment variables (from .env):
    POSTGRES_URL      — Required
    JWT_SECRET        — Required
    FERNET_KEY        — Required
    LLM_PROVIDER      — local | claude (default: local)
    ANTHROPIC_API_KEY — Required when LLM_PROVIDER=claude
"""
import logging
import sys
import time
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Logging setup (before any imports that might trigger logging)
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("repomind.worker")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
POLL_INTERVAL_SECONDS = 5
MAX_CONSECUTIVE_ERRORS = 10  # Stop worker if DB is unreachable repeatedly


def poll_and_execute() -> None:
    """
    Main worker loop.
    Polls for pending ReviewRun jobs and executes them synchronously.
    """
    from sqlalchemy import text
    from backend.app.db import SessionLocal
    from backend.app.core.config import settings
    from backend.app.review.models import ReviewRun
    from backend.app.review.service import run_review, ReviewError
    from backend.app.review.provider import get_llm_provider

    provider = get_llm_provider(settings)
    logger.info(
        "Worker started. LLM provider: %s. Poll interval: %ds.",
        type(provider).__name__,
        POLL_INTERVAL_SECONDS,
    )

    # --- Crash recovery: reset stale 'running' jobs to 'pending' ---
    with SessionLocal() as db:
        stale_count = (
            db.query(ReviewRun)
            .filter(ReviewRun.status == "running")
            .update(
                {
                    "status": "pending",
                    "progress_message": "Reset by worker startup (crash recovery)",
                },
                synchronize_session=False,
            )
        )
        if stale_count:
            db.commit()
            logger.warning(
                "Crash recovery: reset %d stale 'running' job(s) to 'pending'.",
                stale_count,
            )
            
        from backend.app.organizations.models import Repository
        stale_repo_count = (
            db.query(Repository)
            .filter(Repository.index_status == "indexing")
            .update({"index_status": "unindexed"}, synchronize_session=False)
        )
        if stale_repo_count:
            db.commit()
            logger.warning(
                "Crash recovery: reset %d stale 'indexing' repository(s) to 'unindexed'.",
                stale_repo_count,
            )

    consecutive_errors = 0

    while True:
        try:
            _process_one_job(provider)
            _process_one_indexing_job()
            consecutive_errors = 0
        except Exception as exc:
            consecutive_errors += 1
            logger.error(
                "Worker loop error (%d/%d consecutive): %s: %s",
                consecutive_errors,
                MAX_CONSECUTIVE_ERRORS,
                type(exc).__name__,
                exc,
            )
            if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                logger.critical(
                    "Too many consecutive errors (%d). Worker shutting down.",
                    MAX_CONSECUTIVE_ERRORS,
                )
                sys.exit(1)

        time.sleep(POLL_INTERVAL_SECONDS)


def _process_one_job(provider) -> None:
    """
    Pick up one pending ReviewRun (with SELECT FOR UPDATE SKIP LOCKED)
    and run the full review pipeline.

    SKIP LOCKED ensures that multiple worker processes can run in parallel
    without picking the same job.
    """
    from sqlalchemy import text, select
    from backend.app.db import SessionLocal
    from backend.app.review.models import ReviewRun
    from backend.app.review.service import run_review, ReviewError
    from backend.app.organizations.models import Repository, Project
    from backend.app.github.models import PullRequest

    with SessionLocal() as db:
        # Atomically claim one pending job
        run = (
            db.query(ReviewRun)
            .filter(ReviewRun.status == "pending")
            .with_for_update(skip_locked=True)
            .order_by(ReviewRun.id.asc())   # FIFO order
            .first()
        )

        if run is None:
            return  # Nothing to process

        # Mark as running immediately (within the same transaction)
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        run.progress_message = "Fetching PR data..."
        db.commit()
        run_id = run.id

        logger.info("Worker picked up ReviewRun %d (PR #%s)", run_id, run.pull_request_id)

    # Execute review pipeline in a fresh session (long-running — don't hold the lock session)
    with SessionLocal() as db:
        run = db.get(ReviewRun, run_id)
        if not run:
            logger.warning("ReviewRun %d disappeared before execution.", run_id)
            return

        # Resolve organization_id for PAT retrieval
        pr = db.get(PullRequest, run.pull_request_id)
        if not pr:
            _fail_run(db, run, "PullRequest not found")
            return

        repo = db.get(Repository, pr.repository_id)
        if not repo:
            _fail_run(db, run, "Repository not found")
            return

        project = db.get(Project, repo.project_id)
        if not project:
            _fail_run(db, run, "Project not found")
            return

        organization_id = project.organization_id

        logger.info(
            "Executing review pipeline: ReviewRun %d, PR %d, repo %s/%s, org %d",
            run.id,
            pr.github_number,
            repo.github_owner,
            repo.github_name,
            organization_id,
        )

        try:
            # Update progress
            run.progress_message = "Running review pipeline..."
            db.commit()

            completed_run = run_review(
                db=db,
                pull_request_id=run.pull_request_id,
                organization_id=organization_id,
                provider=provider,
            )

            if completed_run.status == "completed":
                logger.info(
                    "ReviewRun %d completed successfully. Findings: %d.",
                    run_id,
                    len(completed_run.findings),
                )
            else:
                logger.warning(
                    "ReviewRun %d finished with status: %s",
                    run_id,
                    completed_run.status,
                )

        except ReviewError as exc:
            logger.error("ReviewRun %d ReviewError: %s", run_id, exc)
            _fail_run(db, run, str(exc))

        except Exception as exc:
            logger.error(
                "ReviewRun %d unexpected error: %s: %s",
                run_id,
                type(exc).__name__,
                exc,
            )
            _fail_run(db, run, f"{type(exc).__name__}: {exc}")


def _fail_run(db, run: "ReviewRun", reason: str) -> None:
    """Mark a ReviewRun as failed with an error message."""
    try:
        run.status = "failed"
        run.completed_at = datetime.now(timezone.utc)
        run.error_message = reason[:1000]  # Truncate for DB column
        run.progress_message = None
        db.commit()
    except Exception as commit_exc:
        logger.error("Failed to mark ReviewRun %d as failed: %s", run.id, commit_exc)


def _process_one_indexing_job() -> None:
    """
    Pick up one pending Repository indexing job (unindexed)
    and run the indexing pipeline.
    """
    from backend.app.db import SessionLocal
    from backend.app.organizations.models import Repository
    from backend.app.rag.service import index_repository

    with SessionLocal() as db:
        # Atomically claim one unindexed repository
        repo = (
            db.query(Repository)
            .filter(Repository.index_status == "unindexed")
            .with_for_update(skip_locked=True)
            .order_by(Repository.id.asc())
            .first()
        )

        if repo is None:
            return  # Nothing to index

        repo.index_status = "indexing"
        repo.last_indexed_at = datetime.now(timezone.utc)
        db.commit()
        repo_id = repo.id

        logger.info("Worker picked up Repository %d (%s/%s) for indexing", repo_id, repo.github_owner, repo.github_name)

    # Execute indexing in a fresh session
    with SessionLocal() as db:
        repo = db.get(Repository, repo_id)
        if not repo:
            return

        try:
            index_repository(db, repo_id)
            repo.index_status = "indexed"
            repo.last_indexed_at = datetime.now(timezone.utc)
            db.commit()
            logger.info("Repository %d indexed successfully.", repo_id)
        except Exception as exc:
            logger.error("Repository %d indexing error: %s: %s", repo_id, type(exc).__name__, exc)
            try:
                repo.index_status = "failed"
                repo.last_indexed_at = datetime.now(timezone.utc)
                db.commit()
            except Exception as commit_exc:
                logger.error("Failed to mark Repository %d as failed: %s", repo_id, commit_exc)

if __name__ == "__main__":
    poll_and_execute()
