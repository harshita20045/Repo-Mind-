"""
Review orchestration service — RepoMind 2.0.

Implements the full review pipeline:
  fetch diff → fetch PR files → retrieve RAG context → run static analysis →
  detect conflicts → call LLM → validate evidence → calculate risk →
  persist all → mark completed/failed

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
import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.orm import Session

from backend.app.github.models import PullRequest
from backend.app.github.service import get_pull_request_diff, get_decrypted_pat_for_org
from backend.app.github.client import GitHubClient
from backend.app.organizations.service import get_repository_by_id
from backend.app.organizations.models import Repository
from backend.app.rag.retriever import RAGRetriever, RetrievalResult
from backend.app.rag.embedder import LocalEmbedder
from backend.app.review.models import (
    ReviewRun, Finding, LinterResult,
    RiskAssessment, Conflict, FindingEvidence, HumanDecision,
)
from backend.app.review.provider import LLMProvider, LLMProviderError
from backend.app.review.schemas import (
    parse_llm_output, LLMOutputParseError, FindingSchema,
)
from backend.app.review.prompts import (
    SYSTEM_PROMPT, RETRY_SYSTEM_PROMPT, PROMPT_VERSION, REPOMIND_VERSION,
    build_user_content,
)
from backend.app.review.context import derive_query_from_diff, retrieve_context
from backend.app.review.evidence import validate_findings, ValidatedFinding
from backend.app.linter.service import run_linters
from backend.app.conflicts.engine import detect_conflicts, DetectedConflict
from backend.app.risk.engine import calculate_risk

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


def _mark_failed(db: Session, run: ReviewRun, reason: str = "") -> None:
    """Persist a failed ReviewRun state with optional error message."""
    run.status = "failed"
    run.completed_at = datetime.now(timezone.utc)
    run.progress_message = None
    if reason:
        run.error_message = reason[:1000]
    db.commit()


def _update_progress(db: Session, run: ReviewRun, message: str) -> None:
    """Update the progress message on a running ReviewRun for UI polling."""
    run.progress_message = message
    db.commit()


def _persist_validated_findings(
    db: Session, run: ReviewRun, validated_findings: List[ValidatedFinding]
) -> List[Finding]:
    """
    Map ValidatedFinding objects to Finding + FindingEvidence DB rows.
    Also calculates lifecycle_status (new, persistent, resolved) by comparing
    with the previous completed ReviewRun for this PR.
    Returns the list of created Finding ORM objects.
    """
    # 1. Fetch previous completed run
    previous_run = (
        db.query(ReviewRun)
        .filter(ReviewRun.pull_request_id == run.pull_request_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.id < run.id)
        .order_by(ReviewRun.id.desc())
        .first()
    )

    prev_findings = []
    if previous_run:
        prev_findings = db.query(Finding).filter(Finding.review_run_id == previous_run.id).all()

    created_findings: List[Finding] = []
    matched_prev_finding_ids = set()

    for vf in validated_findings:
        f = vf.finding
        
        # Determine lifecycle status
        lifecycle = "new"
        for pf in prev_findings:
            if pf.id in matched_prev_finding_ids:
                continue
            # Simple heuristic for finding match: same file and category, and line is close (or None)
            file_match = (f.file == pf.file)
            type_match = (f.category == pf.type)
            # Check line proximity (within 3 lines) to account for minor shifts
            line_match = False
            if f.line is None and pf.line is None:
                line_match = True
            elif f.line is not None and pf.line is not None:
                line_match = abs(f.line - pf.line) <= 3
                
            if file_match and type_match and line_match:
                lifecycle = "persistent"
                matched_prev_finding_ids.add(pf.id)
                break

        finding = Finding(
            review_run_id=run.id,
            type=f.category,
            severity=f.severity,
            file=f.file,
            line=f.line,
            title=f.title,
            explanation=f.problem,
            rule_source=f.evidence,
            recommendation=f.recommendation,
            confidence=vf.adjusted_confidence,
            status="open",
            evidence_status=vf.evidence_status,
            lifecycle_status=lifecycle,
        )
        db.add(finding)
        db.flush()  # Get finding.id

        # Persist evidence items
        for ev in vf.supporting_evidence:
            db.add(FindingEvidence(
                finding_id=finding.id,
                evidence_status="supported",
                source_type=ev.get("type", "documentation"),
                source_path=ev.get("path"),
                source_text=ev.get("text", "")[:2000],
                citation_metadata={
                    k: v for k, v in ev.items()
                    if k not in ("text",)
                },
            ))
        for ev in vf.contradicting_evidence:
            db.add(FindingEvidence(
                finding_id=finding.id,
                evidence_status="contradicted",
                source_type=ev.get("type", "diff_check"),
                source_path=None,
                source_text=ev.get("message", ""),
                citation_metadata=ev,
            ))

        created_findings.append(finding)
        
    # Carry over resolved findings from previous run so UI can show them
    for pf in prev_findings:
        if pf.id not in matched_prev_finding_ids:
            resolved_finding = Finding(
                review_run_id=run.id,
                type=pf.type,
                severity=pf.severity,
                file=pf.file,
                line=pf.line,
                title=pf.title,
                explanation=pf.explanation,
                rule_source=pf.rule_source,
                recommendation=pf.recommendation,
                confidence=pf.confidence,
                status="resolved",
                evidence_status=pf.evidence_status,
                lifecycle_status="resolved",
            )
            db.add(resolved_finding)
            created_findings.append(resolved_finding)

    db.flush()
    return created_findings



def _persist_conflicts(
    db: Session, run: ReviewRun, conflicts: List[DetectedConflict]
) -> None:
    """Persist detected conflicts to the conflict table."""
    for c in conflicts:
        db.add(Conflict(
            review_run_id=run.id,
            conflict_type=c.conflict_type,
            category=c.category,
            severity=c.severity,
            title=c.title,
            description=c.description,
            evidence=c.evidence,
            status="open",
        ))
    db.flush()


def _persist_risk(
    db: Session, run: ReviewRun, risk_result
) -> None:
    """Persist the risk assessment."""
    db.add(RiskAssessment(
        review_run_id=run.id,
        score=risk_result.score,
        level=risk_result.level,
        factors=risk_result.factors,
        blast_radius=risk_result.blast_radius,
        test_impact=risk_result.test_impact,
        summary=risk_result.summary,
        calculated_at=datetime.now(timezone.utc),
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
    Orchestrate the full RepoMind 2.0 review pipeline for a pull request.

    ReviewRun lifecycle:
      pending (created) → running → completed  (success)
                                  → failed     (any non-retryable failure)

    Pipeline stages:
      1. Resolve PR + repository (DB authoritative)
      2. Create ReviewRun record (pending → running)
      3. Fetch PR diff + changed files from GitHub
      4. Retrieve RAG context (repository documentation)
      5. Run static analysis (Ruff + Bandit)
      6. Detect semantic + mechanical conflicts
      7. Call LLM with structured prompt (with one retry on parse failure)
      8. Validate evidence against RAG chunks and linter results
      9. Calculate PR risk score (explainable factors)
      10. Persist all: findings, evidence, conflicts, risk assessment
      11. Mark completed

    Security invariants:
      - repository_id derived from PullRequest.repository_id (DB-authoritative).
      - PAT decrypted in-process, used only for GitHub API calls.
      - Diff + RAG chunks passed only as user_content, never mixed into system_prompt.
      - LLM output validated before persistence.

    Args:
        db:               SQLAlchemy session.
        pull_request_id:  DB primary key of the PullRequest to review.
        organization_id:  Used only to resolve the PAT for GitHub API access.
        provider:         LLMProvider protocol implementation.
        embedder:         Optional LocalEmbedder (reused if provided).

    Returns:
        The ReviewRun ORM object (status=completed or status=failed).

    Raises:
        ReviewError: If the PR or repository cannot be resolved.
    """
    # --- 1. Resolve PR and repository -----------------------------------------
    pr = db.get(PullRequest, pull_request_id)
    if not pr:
        raise ReviewError(f"PullRequest {pull_request_id} not found.")

    repo = get_repository_by_id(db, pr.repository_id)
    if not repo:
        raise ReviewError(f"Repository {pr.repository_id} not found for PR {pull_request_id}.")

    # repository_id is derived from the DB relationship — never from a client param
    repository_id = pr.repository_id

    # --- 2. Create ReviewRun (pending → running) -------------------------------
    run = ReviewRun(
        pull_request_id=pull_request_id,
        commit_sha=pr.head_sha,
        status="running",
        repomind_version=REPOMIND_VERSION,
        prompt_version=PROMPT_VERSION,
        llm_model=type(provider).__name__,
        rag_enabled=True,
        intelligence_mode="v1",
        started_at=datetime.now(timezone.utc),
        progress_message="Fetching PR data from GitHub...",
    )
    db.add(run)
    db.flush()  # Obtain run.id

    logger.info(
        "ReviewRun %d: starting pipeline for PR %d (repo %s/%s, org %d).",
        run.id, pr.github_number, repo.github_owner, repo.github_name, organization_id,
    )

    # --- 3. Fetch PR diff + changed files from GitHub -------------------------
    try:
        pat = get_decrypted_pat_for_org(db, organization_id)
        client = GitHubClient(pat)
        diff = client.get_pull_request_diff(
            repo.github_owner,
            repo.github_name,
            pr.github_number,
        )
        # Fetch file list for blast radius / conflict analysis
        try:
            pr_files_raw = client.get_pull_request_files(
                repo.github_owner, repo.github_name, pr.github_number
            )
            changed_files = [f.get("filename", "") for f in pr_files_raw if f.get("filename")]
            pr_additions = sum(f.get("additions", 0) for f in pr_files_raw)
            pr_deletions = sum(f.get("deletions", 0) for f in pr_files_raw)
        except Exception:
            changed_files = []
            pr_additions = None
            pr_deletions = None
    except Exception as exc:
        logger.warning(
            "ReviewRun %d: failed to fetch PR diff. Error type: %s. Marking failed.",
            run.id, type(exc).__name__,
        )
        _mark_failed(db, run, reason=f"GitHub API error: {type(exc).__name__}")
        return run

    # --- 4. Retrieve RAG context (repository-isolated) ------------------------
    _update_progress(db, run, "Analyzing repository knowledge...")
    query = derive_query_from_diff(pr_title=pr.title, diff=diff)
    retriever = RAGRetriever(db=db, embedder=embedder)
    retrieved_chunks = retrieve_context(
        retriever=retriever,
        repository_id=repository_id,   # DB-authoritative
        query=query,
        top_k=5,
    )

    # --- 5. Run static analysis -----------------------------------------------
    _update_progress(db, run, "Running static analysis...")
    run_linters(
        db=db,
        client=client,
        owner=repo.github_owner,
        repo=repo.github_name,
        pr_number=pr.github_number,
        review_run_id=run.id,
    )

    # Fetch linter results for prompt + validation
    linter_rows = db.query(LinterResult).filter(LinterResult.review_run_id == run.id).all()
    linter_results_raw = [{"tool": lr.tool, "raw_output": lr.raw_output} for lr in linter_rows]
    linter_text_parts = []
    for lr in linter_rows:
        try:
            formatted_output = json.dumps(lr.raw_output, indent=2)
            linter_text_parts.append(f"Tool: {lr.tool}\nResult:\n{formatted_output}")
        except Exception:
            linter_text_parts.append(f"Tool: {lr.tool}\nResult: Unparseable output")
    linter_results_text = "\n\n".join(linter_text_parts)

    # --- 6. Detect semantic + mechanical conflicts ----------------------------
    _update_progress(db, run, "Detecting semantic conflicts...")
    detected_conflicts: List[DetectedConflict] = detect_conflicts(
        diff=diff,
        retrieved_chunks=retrieved_chunks,
        pr_title=pr.title or "",
        pr_description="",
        changed_files=changed_files,
    )
    _persist_conflicts(db, run, detected_conflicts)

    # --- 7. Build prompt + call LLM (with one retry on parse failure) ---------
    _update_progress(db, run, "Generating AI review...")
    user_content = build_user_content(
        pr_title=pr.title,
        diff=diff,
        retrieved_chunks=retrieved_chunks,
        linter_results_text=linter_results_text,
    )

    raw_output: Optional[str] = None
    findings_raw: Optional[List[FindingSchema]] = None

    for attempt in (1, 2):
        system = SYSTEM_PROMPT if attempt == 1 else RETRY_SYSTEM_PROMPT
        try:
            raw_output = provider.complete(
                system_prompt=system,
                user_content=user_content,
            )
        except LLMProviderError as exc:
            logger.warning(
                "ReviewRun %d: provider infrastructure failure on attempt %d. Type: %s.",
                run.id, attempt, type(exc).__name__,
            )
            _mark_failed(db, run, reason=f"LLM provider error: {type(exc).__name__}")
            return run

        try:
            findings_raw = parse_llm_output(raw_output)
            break  # Success
        except LLMOutputParseError as exc:
            logger.warning(
                "ReviewRun %d: LLM output parse failure on attempt %d. Error: %s.",
                run.id, attempt, str(exc),
            )
            if attempt == 2:
                _mark_failed(db, run, reason=f"LLM output parse failed: {exc}")
                return run

    if findings_raw is None:
        _mark_failed(db, run, reason="No findings parsed from LLM output")
        return run

    # --- 8. Validate evidence for each finding --------------------------------
    _update_progress(db, run, "Validating evidence...")
    validated_findings = validate_findings(
        findings=findings_raw,
        retrieved_chunks=retrieved_chunks,
        linter_results=linter_results_raw,
        diff=diff,
    )

    # --- 9. Calculate PR risk -------------------------------------------------
    _update_progress(db, run, "Calculating risk score...")
    risk_result = calculate_risk(
        diff=diff,
        validated_findings=validated_findings,
        conflicts=detected_conflicts,
        linter_results=linter_results_raw,
        changed_files=changed_files,
        pr_title=pr.title or "",
        additions=pr_additions,
        deletions=pr_deletions,
    )
    _persist_risk(db, run, risk_result)

    # --- 10. Persist validated findings + evidence ----------------------------
    _persist_validated_findings(db, run, validated_findings)

    # --- 11. Mark completed ---------------------------------------------------
    run.status = "completed"
    run.completed_at = datetime.now(timezone.utc)
    run.progress_message = None
    db.commit()

    logger.info(
        "ReviewRun %d completed: %d finding(s), %d conflict(s), risk=%d/%s for PR %d.",
        run.id,
        len(validated_findings),
        len(detected_conflicts),
        risk_result.score,
        risk_result.level,
        pull_request_id,
    )
    return run


