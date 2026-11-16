"""
Indexer and Miner for Historical Code Intelligence — RepoMind 2.0.

Provides automated extraction for:
1. Architecture Decision Records (ADRs) from repository documentation.
2. Historical commits, touched files, bugfix flags, and decision rationale.
3. Recurring issue hotspots and high-churn problem files.
"""
import os
import re
import glob
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from backend.app.history.models import (
    ArchitectureDecisionRecord,
    HistoricalCommitRecord,
    RecurringIssueHotspot,
)
from backend.app.github.models import PullRequest, PullRequestCommit, PullRequestFile
from backend.app.review.models import ReviewRun, Finding, FindingEvidence, HumanDecision
from backend.app.rag.models import Document

logger = logging.getLogger(__name__)

BUGFIX_REGEX = re.compile(r'\b(fix|fixed|fixes|bug|patch|resolve|resolved|resolves|defect|hotfix|regression)\b', re.IGNORECASE)
ISSUE_REF_REGEX = re.compile(r'#(\d+)|([A-Z]{2,}-\d+)')


def parse_and_index_adrs(db: Session, repository_id: int, base_dir: Optional[str] = None) -> int:
    """
    Scans repository documentation for Architecture Decision Records (ADRs)
    and persists them in the database.
    """
    root_path = base_dir or os.getcwd()
    adr_files = []

    # Common ADR locations
    search_patterns = [
        os.path.join(root_path, "docs", "**", "*decision*.md"),
        os.path.join(root_path, "docs", "**", "*adr*.md"),
        os.path.join(root_path, "doc", "**", "*decision*.md"),
        os.path.join(root_path, "doc", "**", "*adr*.md"),
    ]

    for pat in search_patterns:
        for f in glob.glob(pat, recursive=True):
            if os.path.isfile(f) and f not in adr_files:
                adr_files.append(f)

    indexed_count = 0

    for file_path in adr_files:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            rel_path = os.path.relpath(file_path, root_path).replace("\\", "/")
            records = _extract_adrs_from_markdown(content, rel_path)

            for rec in records:
                existing = (
                    db.query(ArchitectureDecisionRecord)
                    .filter(
                        ArchitectureDecisionRecord.repository_id == repository_id,
                        ArchitectureDecisionRecord.adr_number == rec["adr_number"],
                    )
                    .first()
                )
                if not existing:
                    existing = ArchitectureDecisionRecord(
                        repository_id=repository_id,
                        adr_number=rec["adr_number"],
                        title=rec["title"],
                        status=rec.get("status", "Confirmed"),
                        context=rec.get("context"),
                        decision=rec.get("decision", ""),
                        options_considered=rec.get("options_considered"),
                        reason=rec.get("reason"),
                        consequences=rec.get("consequences"),
                        superseded_alternative=rec.get("superseded_alternative"),
                        file_source=rel_path,
                        affected_modules=rec.get("affected_modules", []),
                        date=rec.get("date"),
                    )
                    db.add(existing)
                    indexed_count += 1
                else:
                    # Update fields
                    existing.title = rec["title"]
                    existing.status = rec.get("status", existing.status)
                    existing.context = rec.get("context", existing.context)
                    existing.decision = rec.get("decision", existing.decision)
                    existing.reason = rec.get("reason", existing.reason)
                    existing.consequences = rec.get("consequences", existing.consequences)
                    existing.file_source = rel_path
                    existing.affected_modules = rec.get("affected_modules", existing.affected_modules)
                    indexed_count += 1

            db.commit()
        except Exception as e:
            logger.warning(f"Error parsing ADR file {file_path}: {e}")
            db.rollback()

    return indexed_count


def _extract_adrs_from_markdown(content: str, rel_path: str) -> List[Dict[str, Any]]:
    """
    Parses individual ADR blocks from markdown text.
    Handles blocks starting with ### ADR-XXX or ## ADR-XXX.
    """
    adrs = []
    # Split by ADR headers: ### ADR-001 — Modular Monolith Architecture
    header_pattern = re.compile(r'###?\s+(ADR[-_]\d+)\s*[-—:]?\s*(.+)', re.IGNORECASE)

    lines = content.splitlines()
    current_adr: Optional[Dict[str, Any]] = None
    current_field: Optional[str] = None
    field_buffer: List[str] = []

    def save_current_field():
        nonlocal current_field, field_buffer
        if current_adr and current_field:
            val = "\n".join(field_buffer).strip()
            if current_field == "options_considered":
                current_adr["options_considered"] = [opt.strip() for opt in val.split(",") if opt.strip()]
            else:
                current_adr[current_field] = val
        current_field = None
        field_buffer = []

    for line in lines:
        if line.strip().startswith('---'):
            save_current_field()
            continue

        match = header_pattern.match(line.strip())
        if match:
            # New ADR started
            save_current_field()
            if current_adr and current_adr.get("decision"):
                adrs.append(current_adr)

            adr_num = match.group(1).upper().replace("_", "-")
            adr_title = match.group(2).strip()
            current_adr = {
                "adr_number": adr_num,
                "title": adr_title,
                "status": "Confirmed",
                "affected_modules": _infer_modules_from_title_and_text(adr_title),
            }
            continue

        if not current_adr:
            continue

        # Check for sub-fields: - **Decision:** ... or - **Decision**: ...
        subfield_match = re.match(r'^\s*[-*]\s*\*\*([A-Za-z\s]+?):?\*\*:?\s*(.*)', line)
        if subfield_match:
            save_current_field()
            key_name = subfield_match.group(1).lower().replace(" ", "_")
            inline_val = subfield_match.group(2).strip()

            if "decision" in key_name:
                current_field = "decision"
            elif "context" in key_name:
                current_field = "context"
            elif "reason" in key_name:
                current_field = "reason"
            elif "consequence" in key_name:
                current_field = "consequences"
            elif "option" in key_name:
                current_field = "options_considered"
            elif "status" in key_name:
                current_field = "status"
            elif "supersede" in key_name:
                current_field = "superseded_alternative"
            else:
                current_field = key_name

            if inline_val:
                field_buffer.append(inline_val)
        elif current_field:
            field_buffer.append(line)

    save_current_field()
    if current_adr and current_adr.get("decision"):
        adrs.append(current_adr)

    return adrs


def _infer_modules_from_title_and_text(text: str) -> List[str]:
    """Infers relevant modules or layers governed by the ADR."""
    modules = []
    text_lower = text.lower()
    if "architecture" in text_lower or "monolith" in text_lower:
        modules.extend(["backend/app", "backend/app/main.py"])
    if "auth" in text_lower or "role" in text_lower or "rbac" in text_lower:
        modules.extend(["backend/app/auth", "backend/app/auth/service.py", "backend/app/auth/routes.py"])
    if "database" in text_lower or "postgres" in text_lower or "alembic" in text_lower:
        modules.extend(["backend/app/db.py", "backend/app/models", "backend/alembic"])
    if "vector" in text_lower or "pgvector" in text_lower or "embedding" in text_lower or "rag" in text_lower:
        modules.extend(["backend/app/rag", "backend/app/rag/retriever.py", "backend/app/rag/models.py"])
    if "frontend" in text_lower or "react" in text_lower:
        modules.extend(["frontend/src", "frontend/src/pages"])
    if "review" in text_lower or "llm" in text_lower or "finding" in text_lower:
        modules.extend(["backend/app/review", "backend/app/review/service.py", "backend/app/review/analysis.py"])
    if "worker" in text_lower or "job" in text_lower:
        modules.extend(["worker", "worker/worker.py"])
    if "test" in text_lower:
        modules.extend(["backend/tests", "frontend/tests"])
    return list(set(modules))


def mine_and_index_commits(db: Session, repository_id: int) -> int:
    """
    Mines commit history from PullRequestCommit and PullRequestFile models,
    classifies bugfixes, extracts issue links and original decision rationale.
    """
    # 1. Fetch commits associated with repository's PRs
    pr_commits = (
        db.query(PullRequestCommit)
        .join(PullRequest)
        .filter(PullRequest.repository_id == repository_id)
        .order_by(PullRequestCommit.created_at.desc())
        .all()
    )

    indexed_count = 0

    for c in pr_commits:
        msg = c.message or ""
        is_bug = bool(BUGFIX_REGEX.search(msg))

        # Extract linked issues like #42 or PROJ-101
        issue_matches = ISSUE_REF_REGEX.findall(msg)
        issues = []
        for im in issue_matches:
            ref = im[0] or im[1]
            if ref and ref not in issues:
                issues.append(f"#{ref}" if ref.isdigit() else ref)

        # Get changed files for this PR/commit
        pr_files = (
            db.query(PullRequestFile)
            .filter(PullRequestFile.pull_request_id == c.pull_request_id)
            .limit(15)
            .all()
        )
        files_data = [
            {
                "path": pf.file_path,
                "status": pf.status,
                "additions": pf.additions,
                "deletions": pf.deletions,
            }
            for pf in pr_files if pf.file_path
        ]

        # Extract rationale from commit message body (first non-empty line after header)
        msg_lines = [l.strip() for l in msg.splitlines() if l.strip()]
        rationale = msg_lines[1] if len(msg_lines) > 1 else (msg_lines[0] if msg_lines else "Code modification commit")

        existing = (
            db.query(HistoricalCommitRecord)
            .filter(
                HistoricalCommitRecord.repository_id == repository_id,
                HistoricalCommitRecord.commit_sha == c.sha,
            )
            .first()
        )

        commit_time = c.created_at if c.created_at else datetime.now(timezone.utc)

        if not existing:
            rec = HistoricalCommitRecord(
                repository_id=repository_id,
                commit_sha=c.sha,
                author=c.author or "developer",
                committer=c.committer or c.author or "developer",
                message=msg,
                committed_at=commit_time,
                is_bugfix=is_bug,
                files_changed=files_data,
                linked_issues=issues,
                original_decision_rationale=rationale,
            )
            db.add(rec)
            indexed_count += 1
        else:
            existing.message = msg
            existing.is_bugfix = is_bug
            existing.files_changed = files_data
            existing.linked_issues = issues
            existing.original_decision_rationale = rationale
            indexed_count += 1

    db.commit()
    return indexed_count


def compute_and_index_hotspots(db: Session, repository_id: int) -> int:
    """
    Computes recurring issue hotspots by aggregating bugfix commits and
    past review findings per modified file path.
    """
    # 1. Gather all files changed in historical commits
    commits = (
        db.query(HistoricalCommitRecord)
        .filter(HistoricalCommitRecord.repository_id == repository_id)
        .all()
    )

    file_stats: Dict[str, Dict[str, Any]] = {}

    for c in commits:
        if not c.files_changed:
            continue
        for fc in c.files_changed:
            fpath = fc.get("path")
            if not fpath:
                continue
            if fpath not in file_stats:
                file_stats[fpath] = {
                    "total_commits": 0,
                    "bugfix_commits": 0,
                    "last_bugfix_at": None,
                    "references": [],
                }
            file_stats[fpath]["total_commits"] += 1
            if c.is_bugfix:
                file_stats[fpath]["bugfix_commits"] += 1
                if not file_stats[fpath]["last_bugfix_at"] or c.committed_at > file_stats[fpath]["last_bugfix_at"]:
                    file_stats[fpath]["last_bugfix_at"] = c.committed_at
                file_stats[fpath]["references"].append({
                    "ref": f"Commit {c.commit_sha[:8]}",
                    "date": c.committed_at.strftime("%Y-%m-%d") if c.committed_at else None,
                    "reason": c.original_decision_rationale or c.message[:100],
                })

    # 2. Gather findings per file
    findings = (
        db.query(Finding)
        .join(ReviewRun)
        .join(PullRequest)
        .filter(
            PullRequest.repository_id == repository_id,
            Finding.file.isnot(None),
        )
        .all()
    )

    finding_counts_per_file: Dict[str, int] = {}
    finding_cats_per_file: Dict[str, Dict[str, int]] = {}

    for fn in findings:
        fpath = fn.file
        finding_counts_per_file[fpath] = finding_counts_per_file.get(fpath, 0) + 1
        if fpath not in finding_cats_per_file:
            finding_cats_per_file[fpath] = {}
        finding_cats_per_file[fpath][fn.type] = finding_cats_per_file[fpath].get(fn.type, 0) + 1

        if fpath not in file_stats:
            file_stats[fpath] = {
                "total_commits": 1,
                "bugfix_commits": 0,
                "last_bugfix_at": None,
                "references": [],
            }
        file_stats[fpath]["references"].append({
            "ref": f"Review Finding: {fn.title[:50]}",
            "date": fn.review_run.completed_at.strftime("%Y-%m-%d") if fn.review_run and fn.review_run.completed_at else None,
            "reason": fn.explanation[:120],
        })

    indexed_hotspots = 0

    for fpath, stats in file_stats.items():
        bug_count = stats["bugfix_commits"]
        total_comm = stats["total_commits"]
        rec_findings = finding_counts_per_file.get(fpath, 0)
        cats = finding_cats_per_file.get(fpath, {})

        # Hotspot score: formula combines bugfix frequency, finding volume, and commit churn
        score = min(100.0, (bug_count * 25.0) + (rec_findings * 15.0) + (total_comm * 2.0))

        if score >= 60.0 or bug_count >= 2 or rec_findings >= 3:
            severity = "critical"
        elif score >= 35.0 or bug_count >= 1 or rec_findings >= 2:
            severity = "high"
        elif score >= 15.0 or rec_findings >= 1:
            severity = "medium"
        else:
            severity = "low"

        existing = (
            db.query(RecurringIssueHotspot)
            .filter(
                RecurringIssueHotspot.repository_id == repository_id,
                RecurringIssueHotspot.file_path == fpath,
            )
            .first()
        )

        if not existing:
            hotspot = RecurringIssueHotspot(
                repository_id=repository_id,
                file_path=fpath,
                total_commits=total_comm,
                bugfix_commits_count=bug_count,
                recurring_findings_count=rec_findings,
                hotspot_score=round(score, 1),
                severity=severity,
                recurring_finding_categories=cats,
                historical_references=stats["references"][:6],
                last_bugfix_at=stats["last_bugfix_at"],
            )
            db.add(hotspot)
            indexed_hotspots += 1
        else:
            existing.total_commits = total_comm
            existing.bugfix_commits_count = bug_count
            existing.recurring_findings_count = rec_findings
            existing.hotspot_score = round(score, 1)
            existing.severity = severity
            existing.recurring_finding_categories = cats
            existing.historical_references = stats["references"][:6]
            existing.last_bugfix_at = stats["last_bugfix_at"]
            indexed_hotspots += 1

    db.commit()
    return indexed_hotspots
