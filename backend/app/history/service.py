"""
Historical Code Intelligence Service — RepoMind 2.0.

Provides core query, search, comparison, and evidence-grounded recommendation engines:
1. Search historical PRs
2. Search previous code changes
3. Identify recurring issues & hotspots
4. Retrieve relevant Architecture Decision Records (ADRs)
5. Identify previously resolved similar bugs
6. Compare current changes with historical changes and original decisions
"""
import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc, select, Text

from backend.app.history.models import (
    ArchitectureDecisionRecord,
    HistoricalCommitRecord,
    RecurringIssueHotspot,
)
from backend.app.history.schemas import (
    HistoricalPRResponse,
    HistoricalCommitResponse,
    RecurringHotspotResponse,
    ADRResponse,
    SimilarBugResponse,
    ChangeComparisonItem,
    ChangeComparisonResponse,
)
from backend.app.github.models import PullRequest, PullRequestFile, PullRequestCommit
from backend.app.review.models import ReviewRun, Finding, FindingEvidence, HumanDecision
from backend.app.history.indexer import parse_and_index_adrs, mine_and_index_commits, compute_and_index_hotspots

logger = logging.getLogger(__name__)


def search_historical_prs(
    db: Session,
    repository_id: int,
    q: Optional[str] = None,
    file_path: Optional[str] = None,
    state: Optional[str] = None,
    author: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[HistoricalPRResponse]:
    """
    Search historical pull requests with tenant scoping and multi-attribute filters.
    """
    query = db.query(PullRequest).filter(PullRequest.repository_id == repository_id)

    if state and state.lower() != "all":
        query = query.filter(PullRequest.state == state.lower())

    if author:
        query = query.filter(PullRequest.github_author_login.ilike(f"%{author}%"))

    if q:
        search_filter = or_(
            PullRequest.title.ilike(f"%{q}%"),
            PullRequest.description.ilike(f"%{q}%"),
            PullRequest.source_branch.ilike(f"%{q}%"),
        )
        if q.isdigit():
            search_filter = or_(search_filter, PullRequest.github_number == int(q))
        query = query.filter(search_filter)

    if file_path:
        query = query.join(PullRequestFile).filter(PullRequestFile.file_path.ilike(f"%{file_path}%"))

    prs = query.order_by(desc(PullRequest.created_at)).offset(offset).limit(limit).all()

    results = []
    for pr in prs:
        # Count files
        f_count = db.query(PullRequestFile).filter(PullRequestFile.pull_request_id == pr.id).count()
        # Issues
        linked = []
        if pr.title:
            matches = re.findall(r'#(\d+)|([A-Z]{2,}-\d+)', pr.title)
            for m in matches:
                ref = m[0] or m[1]
                if ref:
                    linked.append(f"#{ref}" if ref.isdigit() else ref)

        results.append(
            HistoricalPRResponse(
                id=pr.id,
                github_number=pr.github_number,
                title=pr.title,
                state=pr.state,
                github_author_login=pr.github_author_login,
                source_branch=pr.source_branch,
                target_branch=pr.target_branch,
                head_sha=pr.head_sha,
                files_changed_count=f_count,
                additions=pr.additions or 0,
                deletions=pr.deletions or 0,
                merged_at=pr.merged_at,
                created_at=pr.created_at,
                linked_issues=linked,
                summary=pr.description[:200] if pr.description else None,
            )
        )
    return results


def search_previous_changes(
    db: Session,
    repository_id: int,
    q: Optional[str] = None,
    file_path: Optional[str] = None,
    is_bugfix: Optional[bool] = None,
    limit: int = 20,
    offset: int = 0,
) -> List[HistoricalCommitResponse]:
    """
    Search historical commit records, diff changes, and original decision rationale.
    """
    query = db.query(HistoricalCommitRecord).filter(HistoricalCommitRecord.repository_id == repository_id)

    if is_bugfix is not None:
        query = query.filter(HistoricalCommitRecord.is_bugfix == is_bugfix)

    if q:
        query = query.filter(
            or_(
                HistoricalCommitRecord.message.ilike(f"%{q}%"),
                HistoricalCommitRecord.commit_sha.ilike(f"%{q}%"),
                HistoricalCommitRecord.author.ilike(f"%{q}%"),
            )
        )

    if file_path:
        # Cast JSONB to text for path searching
        query = query.filter(HistoricalCommitRecord.files_changed.cast(Text).ilike(f"%{file_path}%"))

    commits = query.order_by(desc(HistoricalCommitRecord.committed_at)).offset(offset).limit(limit).all()

    return [
        HistoricalCommitResponse(
            id=c.id,
            commit_sha=c.commit_sha,
            author=c.author,
            committer=c.committer,
            message=c.message,
            committed_at=c.committed_at,
            is_bugfix=c.is_bugfix,
            files_changed=c.files_changed,
            linked_issues=c.linked_issues,
            original_decision_rationale=c.original_decision_rationale,
        )
        for c in commits
    ]


def get_recurring_issues(
    db: Session,
    repository_id: int,
    severity: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 20,
) -> List[RecurringHotspotResponse]:
    """
    Retrieve recurring issue hotspots ranked by severity and hotspot score.
    """
    query = db.query(RecurringIssueHotspot).filter(RecurringIssueHotspot.repository_id == repository_id)

    if severity and severity.lower() != "all":
        query = query.filter(RecurringIssueHotspot.severity == severity.lower())

    if min_score is not None:
        query = query.filter(RecurringIssueHotspot.hotspot_score >= min_score)

    hotspots = query.order_by(desc(RecurringIssueHotspot.hotspot_score)).limit(limit).all()

    return [
        RecurringHotspotResponse(
            id=h.id,
            file_path=h.file_path,
            total_commits=h.total_commits,
            bugfix_commits_count=h.bugfix_commits_count,
            recurring_findings_count=h.recurring_findings_count,
            hotspot_score=h.hotspot_score,
            severity=h.severity,
            recurring_finding_categories=h.recurring_finding_categories,
            historical_references=h.historical_references,
            last_bugfix_at=h.last_bugfix_at,
        )
        for h in hotspots
    ]


def get_relevant_adrs(
    db: Session,
    repository_id: int,
    file_path: Optional[str] = None,
    module: Optional[str] = None,
    status: Optional[str] = None,
) -> List[ADRResponse]:
    """
    Retrieve Architecture Decision Records governing the repository or a specific module.
    """
    query = db.query(ArchitectureDecisionRecord).filter(ArchitectureDecisionRecord.repository_id == repository_id)

    if status and status.lower() != "all":
        query = query.filter(ArchitectureDecisionRecord.status.ilike(f"%{status}%"))

    target = file_path or module
    if target:
        cleaned_target = target.strip("/").lower()
        parts = cleaned_target.split("/")
        conditions = [
            ArchitectureDecisionRecord.affected_modules.cast(Text).ilike(f"%{cleaned_target}%"),
            ArchitectureDecisionRecord.title.ilike(f"%{cleaned_target}%"),
            ArchitectureDecisionRecord.context.ilike(f"%{cleaned_target}%"),
            ArchitectureDecisionRecord.decision.ilike(f"%{cleaned_target}%"),
        ]
        for part in parts:
            if len(part) >= 4 and part not in ("backend", "app", "frontend", "src"):
                conditions.append(ArchitectureDecisionRecord.affected_modules.cast(Text).ilike(f"%{part}%"))
                conditions.append(ArchitectureDecisionRecord.title.ilike(f"%{part}%"))
        query = query.filter(or_(*conditions))

    adrs = query.order_by(ArchitectureDecisionRecord.adr_number.asc()).all()

    return [
        ADRResponse(
            id=a.id,
            adr_number=a.adr_number,
            title=a.title,
            status=a.status,
            context=a.context,
            decision=a.decision,
            options_considered=a.options_considered,
            reason=a.reason,
            consequences=a.consequences,
            superseded_alternative=a.superseded_alternative,
            file_source=a.file_source,
            affected_modules=a.affected_modules,
            date=a.date,
        )
        for a in adrs
    ]


def get_similar_resolved_bugs(
    db: Session,
    repository_id: int,
    file_path: Optional[str] = None,
    symbol: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 10,
) -> List[SimilarBugResponse]:
    """
    Identify previously resolved bugs and findings matching the file, symbol, or category.
    """
    results: List[SimilarBugResponse] = []

    # 1. Historical bugfix commits on this file
    if file_path:
        commits = (
            db.query(HistoricalCommitRecord)
            .filter(
                HistoricalCommitRecord.repository_id == repository_id,
                HistoricalCommitRecord.is_bugfix == True,
                HistoricalCommitRecord.files_changed.cast(Text).ilike(f"%{file_path}%"),
            )
            .order_by(desc(HistoricalCommitRecord.committed_at))
            .limit(limit)
            .all()
        )
        for c in commits:
            date_str = c.committed_at.strftime("%Y-%m-%d") if c.committed_at else None
            results.append(
                SimilarBugResponse(
                    reference=f"Commit {c.commit_sha[:8]}",
                    file_path=file_path,
                    date=date_str,
                    title=c.original_decision_rationale or c.message.splitlines()[0],
                    description=c.message,
                    category="commit_bugfix",
                    resolution_details=f"Bugfix commit by {c.author} touching {file_path}",
                    supporting_evidence=f"Commit SHA {c.commit_sha} | Message: {c.message[:200]}",
                )
            )

    # 2. Resolved findings on this file
    findings_q = (
        db.query(Finding)
        .join(ReviewRun)
        .join(PullRequest)
        .filter(
            PullRequest.repository_id == repository_id,
            Finding.status.in_(["resolved", "accepted"]),
        )
    )
    if file_path:
        findings_q = findings_q.filter(Finding.file.ilike(f"%{file_path}%"))
    if category:
        findings_q = findings_q.filter(Finding.type.ilike(f"%{category}%"))

    resolved_findings = findings_q.order_by(desc(Finding.id)).limit(limit).all()

    for rf in resolved_findings:
        evidence_text = ""
        if rf.evidence:
            evidence_text = "\n".join([f"L{e.line_start}-{e.line_end}: {e.code_snippet or ''}" for e in rf.evidence[:2]])
        else:
            evidence_text = f"Rule: {rf.rule_source or 'Standard'} | Explanation: {rf.explanation[:150]}"

        pr = db.get(PullRequest, rf.review_run.pull_request_id) if rf.review_run else None
        pr_num = pr.github_number if pr else "?"
        date_str = rf.review_run.completed_at.strftime("%Y-%m-%d") if rf.review_run and rf.review_run.completed_at else None

        results.append(
            SimilarBugResponse(
                reference=f"PR #{pr_num} - Finding #{rf.id}",
                file_path=rf.file or file_path or "unknown",
                date=date_str,
                title=rf.title,
                description=rf.explanation,
                category=rf.type,
                resolution_details=rf.recommendation or f"Marked {rf.status} by engineering team",
                supporting_evidence=evidence_text,
            )
        )

    return results[:limit]


def compare_changes_with_history(
    db: Session,
    repository_id: int,
    file_path: str,
    diff_snippet: Optional[str] = None,
    pull_request_id: Optional[int] = None,
) -> ChangeComparisonResponse:
    """
    Compare current code modifications on a file against historical commits and original decisions.
    Provides supporting evidence and warns if changes conflict with prior bug fixes or ADRs.
    """
    # 1. Check if file is a recurring issue hotspot
    hotspot = (
        db.query(RecurringIssueHotspot)
        .filter(
            RecurringIssueHotspot.repository_id == repository_id,
            RecurringIssueHotspot.file_path == file_path,
        )
        .first()
    )
    is_hotspot = hotspot is not None and hotspot.severity in ("critical", "high")
    hotspot_score = hotspot.hotspot_score if hotspot else 0.0

    # 2. Get governing ADRs
    governing_adrs = get_relevant_adrs(db=db, repository_id=repository_id, file_path=file_path)

    # 3. Retrieve historical commits touching this file
    commits = (
        db.query(HistoricalCommitRecord)
        .filter(
            HistoricalCommitRecord.repository_id == repository_id,
            HistoricalCommitRecord.files_changed.cast(Text).ilike(f"%{file_path}%"),
        )
        .order_by(desc(HistoricalCommitRecord.committed_at))
        .limit(10)
        .all()
    )

    items: List[ChangeComparisonItem] = []

    for c in commits:
        date_str = c.committed_at.strftime("%Y-%m-%d %H:%M UTC") if c.committed_at else None
        decision = c.original_decision_rationale or c.message.splitlines()[0]

        # Supporting evidence: excerpt of commit message and touched file metadata
        evidence_lines = [f"Commit message: {c.message.strip()}"]
        if c.files_changed:
            for fc in c.files_changed:
                if fc.get("path") == file_path:
                    evidence_lines.append(f"Diff stats: +{fc.get('additions', 0)} / -{fc.get('deletions', 0)}")
        evidence_text = "\n".join(evidence_lines)

        risk_warning = None
        if c.is_bugfix:
            risk_warning = f"High caution: This file was previously patched for a bug in {c.commit_sha[:8]} ('{decision}'). Verify this change does not re-introduce the regression."

        items.append(
            ChangeComparisonItem(
                reference=f"Commit {c.commit_sha[:8]}",
                file=file_path,
                date=date_str,
                author=c.author,
                original_decision=decision,
                supporting_evidence=evidence_text,
                is_bugfix=c.is_bugfix,
                risk_warning=risk_warning,
            )
        )

    # 4. Formulate summary guidance
    if not items and not governing_adrs:
        summary_guidance = (
            f"No previous recorded changes or governing architecture decisions found for '{file_path}'. "
            "This file appears to be a new component or unmonitored module."
        )
    else:
        guidance_parts = [f"Found {len(items)} historical change(s) touching '{file_path}'."]
        if is_hotspot:
            guidance_parts.append(
                f"WARNING: This file is a RECURRING HOTSPOT (Score: {hotspot_score}, Severity: {hotspot.severity.upper()}) "
                f"with {hotspot.bugfix_commits_count} prior bug fixes and {hotspot.recurring_findings_count} review findings."
            )
        if governing_adrs:
            adr_titles = [f"{a.adr_number} ({a.title})" for a in governing_adrs[:2]]
            guidance_parts.append(f"Governed by ADRs: {', '.join(adr_titles)}.")
        summary_guidance = " ".join(guidance_parts)

    return ChangeComparisonResponse(
        file_path=file_path,
        total_historical_changes=len(items),
        is_hotspot=is_hotspot,
        hotspot_score=hotspot_score,
        governing_adrs=governing_adrs,
        historical_changes=items,
        summary_guidance=summary_guidance,
    )
