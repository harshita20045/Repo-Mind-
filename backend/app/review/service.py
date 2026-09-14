"""
Review orchestration service — Phase 8.

Implements the full synchronous review pipeline:
  fetch diff → derive query → retrieve RAG context → call LLM →
  validate output → retry once on failure → persist → mark completed/failed

Phase 13 (background jobs) will wrap this function in a worker job.
Phase 10 (review API) will expose HTTP endpoints that call this function.
Neither is implemented here.

Security invariants:
  - repository_id is derived from PullRequest.repository_id (DB-authoritative).
    It is never accepted from an external parameter.
  - PATs are decrypted in-process, used for the GitHub API call only, and
    never passed to the LLM provider.
  - Diff, RAG chunks, and PR metadata are passed only as user_content to the
    provider, never mixed into the system prompt.
  - Raw LLM failure output is logged at WARNING level without diff or PAT content.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.github.models import PullRequest
from backend.app.github.service import get_pull_request_diff, get_decrypted_pat_for_org
from backend.app.github.client import GitHubClient
from backend.app.organizations.service import get_repository_by_id
from backend.app.organizations.models import Repository
from backend.app.rag.retriever import RAGRetriever
from backend.app.rag.embedder import LocalEmbedder
from backend.app.review.models import ReviewRun, Finding
from backend.app.review.provider import LLMProvider, LLMProviderError
from backend.app.review.schemas import (
    parse_llm_output, LLMOutputParseError, FindingSchema,
)
from backend.app.review.prompts import (
    SYSTEM_PROMPT, RETRY_SYSTEM_PROMPT, PROMPT_VERSION, REPOMIND_VERSION,
    build_user_content,
)
from backend.app.review.context import derive_query_from_diff, retrieve_context

logger = logging.getLogger(__name__)


class ReviewError(Exception):
    """Raised for non-retryable errors during review orchestration."""


def _get_org_id_for_pr(db: Session, pr: PullRequest) -> int:
    """Walk PullRequest → Repository → Project → organization_id."""
    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise ReviewError(f"Repository {pr.repository_id} not found.")
    from backend.app.organizations.models import Project
    project = db.get(Project, repo.project_id)
    if not project:
        raise ReviewError(f"Project {repo.project_id} not found.")
    return project.organization_id


def _mark_failed(db: Session, run: ReviewRun) -> None:
    """Persist a failed ReviewRun state."""
    run.status = "failed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()


def _persist_findings(
    db: Session, run: ReviewRun, findings: list[FindingSchema]
) -> None:
    """Map validated FindingSchema objects to Finding DB rows."""
    for f in findings:
        db.add(Finding(
            review_run_id=run.id,
            type=f.category,             # category → finding.type
            severity=f.severity,
            file=f.file,
            line=f.line,
            title=f.title,
            explanation=f.problem,       # problem → finding.explanation
            rule_source=f.evidence,      # evidence → finding.rule_source
            recommendation=f.recommendation,
            confidence=f.confidence,
            status="open",
        ))
    db.flush()


def run_review(
    db: Session,
    pull_request_id: int,
    organization_id: int,
    provider: LLMProvider,
    embedder: Optional[LocalEmbedder] = None,
) -> ReviewRun:
    """
    Orchestrate a synchronous Phase 8 LLM review for a pull request.

    ReviewRun lifecycle:
      pending (created) → running → completed  (success)
                                  → failed     (parse/validation/provider failure)

    Args:
        db:               SQLAlchemy session bound to repomind (or repomind_test in tests).
        pull_request_id:  DB primary key of the PullRequest to review.
        organization_id:  Organization context (from the authenticated session).
                          Used only to resolve the PAT — never trusted as the
                          repository's own isolation boundary.
        provider:         An object satisfying LLMProvider protocol.
                          Injected by the caller; never instantiated here.
        embedder:         Optional LocalEmbedder (for testing/reuse). If None,
                          RAGRetriever will create one lazily.

    Returns:
        The ReviewRun ORM object after the pipeline completes (status=completed
        or status=failed).

    Raises:
        ReviewError: If the PR or repository cannot be resolved.
    """
    # --- 1. Resolve PR and repository ----------------------------------------
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise ReviewError(f"PullRequest {pull_request_id} not found.")

    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise ReviewError(f"Repository {pr.repository_id} not found for PR {pull_request_id}.")

    # repository_id is derived from the DB relationship — never from a client param
    repository_id = pr.repository_id

    # --- 2. Create ReviewRun (pending → running) ------------------------------
    run = ReviewRun(
        pull_request_id=pull_request_id,
        commit_sha=pr.head_sha,
        status="running",
        repomind_version=REPOMIND_VERSION,
        prompt_version=PROMPT_VERSION,
        llm_model=type(provider).__name__,
        rag_enabled=True,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.flush()  # Obtain run.id before proceeding

    # --- 3. Fetch PR diff from GitHub ----------------------------------------
    try:
        pat = get_decrypted_pat_for_org(db, organization_id)
        client = GitHubClient(pat)
        diff = client.get_pull_request_diff(
            repo.github_owner,
            repo.github_name,
            pr.github_number,
        )
    except Exception as exc:
        logger.warning(
            "ReviewRun %d: failed to fetch PR diff. "
            "Error type: %s. ReviewRun marked failed.",
            run.id, type(exc).__name__,
            # NOTE: exc message is not logged to avoid leaking PAT fragments
        )
        _mark_failed(db, run)
        return run

    # --- 4. Deterministic RAG query derivation (no LLM call) -----------------
    query = derive_query_from_diff(pr_title=pr.title, diff=diff)

    # --- 5. Retrieve relevant documentation chunks (repository-isolated) ------
    retriever = RAGRetriever(db=db, embedder=embedder)
    retrieved_chunks = retrieve_context(
        retriever=retriever,
        repository_id=repository_id,   # DB-authoritative, not a client param
        query=query,
        top_k=5,
    )

    # --- 6. Build prompt (system separated from untrusted content) -----------
    user_content = build_user_content(
        pr_title=pr.title,
        diff=diff,
        retrieved_chunks=retrieved_chunks,
    )

    # --- 7. Call provider + validate (with one retry on parse failure) --------
    raw_output: Optional[str] = None
    findings: Optional[list] = None

    for attempt in (1, 2):
        system = SYSTEM_PROMPT if attempt == 1 else RETRY_SYSTEM_PROMPT
        try:
            raw_output = provider.complete(
                system_prompt=system,
                user_content=user_content,
            )
        except LLMProviderError as exc:
            # Infrastructure failure — do not retry
            logger.warning(
                "ReviewRun %d: provider infrastructure failure on attempt %d. "
                "Error type: %s.",
                run.id, attempt, type(exc).__name__,
            )
            _mark_failed(db, run)
            return run

        try:
            findings = parse_llm_output(raw_output)
            break  # Success — exit retry loop
        except LLMOutputParseError as exc:
            logger.warning(
                "ReviewRun %d: LLM output parse/validation failure on attempt %d. "
                "Error: %s. Raw output length: %d chars.",
                run.id, attempt, str(exc), len(raw_output or ""),
            )
            if attempt == 2:
                # Second failure — mark failed per ADR-011
                _mark_failed(db, run)
                return run
            # attempt == 1: continue to retry

    # --- 8. Persist findings and mark completed --------------------------------
    if findings is None:
        # Should not be reachable, but be defensive
        _mark_failed(db, run)
        return run

    _persist_findings(db, run, findings)

    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    db.commit()

    logger.info(
        "ReviewRun %d completed: %d finding(s) for PR %d (repository_id=%d).",
        run.id, len(findings), pull_request_id, repository_id,
    )
    return run
