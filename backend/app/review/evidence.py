"""
Evidence Validation Layer — RepoMind 2.0

Validates LLM findings against actual repository evidence from RAG retrieval
and static analysis results. Classifies each finding as:

  SUPPORTED    — Repository evidence confirms the finding
  UNVERIFIED   — LLM suspects an issue but evidence is insufficient
  CONTRADICTED — LLM claims a violation but repository evidence disagrees

This layer runs AFTER the LLM produces findings, BEFORE persisting them.
It never trusts LLM output blindly.

Security: Repository ID is derived from the PR's repository relationship.
It is never accepted from client input.
"""
import logging
from typing import List, Optional
from dataclasses import dataclass, field

from backend.app.rag.retriever import RetrievalResult
from backend.app.review.schemas import FindingSchema

logger = logging.getLogger(__name__)

# Maximum cosine distance to consider a RAG chunk as supporting evidence
# (lower = more similar; all-mpnet-base-v2 cosine distances typically 0.0-2.0)
_STRONG_EVIDENCE_THRESHOLD = 0.4
_WEAK_EVIDENCE_THRESHOLD = 0.7


@dataclass
class ValidatedFinding:
    """
    A finding after evidence validation.
    Wraps FindingSchema with grounding metadata.
    """
    finding: FindingSchema
    # supported | unverified | contradicted
    evidence_status: str = "unverified"
    # Evidence items that support or contradict this finding
    supporting_evidence: List[dict] = field(default_factory=list)
    contradicting_evidence: List[dict] = field(default_factory=list)
    # Updated confidence after evidence check
    adjusted_confidence: float = 0.0


def validate_findings(
    findings: List[FindingSchema],
    retrieved_chunks: List[RetrievalResult],
    linter_results: List[dict],
    diff: str,
) -> List[ValidatedFinding]:
    """
    Validate a list of LLM findings against available evidence.

    Args:
        findings:         Raw findings from the LLM.
        retrieved_chunks: RAG chunks retrieved for this PR.
        linter_results:   Structured linter output (Ruff, Bandit).
        diff:             The unified diff for this PR.

    Returns:
        List of ValidatedFinding objects with evidence status and adjusted confidence.
    """
    validated: List[ValidatedFinding] = []

    # Pre-process linter findings for quick lookup
    linter_issues = _extract_linter_issues(linter_results)

    for finding in findings:
        vf = _validate_single_finding(finding, retrieved_chunks, linter_issues, diff)
        validated.append(vf)
        logger.debug(
            "Finding '%s' → %s (confidence: %.2f → %.2f)",
            finding.title,
            vf.evidence_status,
            finding.confidence,
            vf.adjusted_confidence,
        )

    return validated


def _validate_single_finding(
    finding: FindingSchema,
    retrieved_chunks: List[RetrievalResult],
    linter_issues: List[dict],
    diff: str,
) -> ValidatedFinding:
    """
    Validate a single finding.

    Strategy:
    1. For security/architecture findings: look for matching rule in RAG chunks.
    2. For linter-overlapping findings: check if linter confirmed the issue.
    3. For diff-based findings: verify the cited file/line appears in the diff.
    4. Apply confidence adjustments based on evidence strength.
    """
    vf = ValidatedFinding(
        finding=finding,
        evidence_status="unverified",
        adjusted_confidence=finding.confidence,
    )

    # --- Check 1: Does any RAG chunk support this finding? ---
    chunk_evidence = _find_supporting_chunks(finding, retrieved_chunks)
    if chunk_evidence:
        vf.supporting_evidence.extend(chunk_evidence)

    # --- Check 2: Does a linter result confirm this? ---
    linter_evidence = _find_linter_confirmation(finding, linter_issues)
    if linter_evidence:
        vf.supporting_evidence.extend(linter_evidence)

    # --- Check 3: Does the cited file/line appear in the diff? ---
    diff_confirmed = _verify_file_in_diff(finding, diff)

    # --- Classify evidence status ---
    if finding.category == "standards_violation" and not chunk_evidence:
        # standards_violation MUST cite a rule — no chunk support = unverified
        vf.evidence_status = "unverified"
        vf.adjusted_confidence = min(finding.confidence, 0.5)
    elif vf.supporting_evidence:
        # Has supporting evidence from RAG or linter
        strong_evidence = [e for e in vf.supporting_evidence if e.get("strength") == "strong"]
        if strong_evidence:
            vf.evidence_status = "supported"
            # Boost confidence slightly for strongly supported findings
            vf.adjusted_confidence = min(finding.confidence * 1.1, 1.0)
        else:
            vf.evidence_status = "supported"
            vf.adjusted_confidence = finding.confidence
    elif not diff_confirmed and finding.file:
        # The cited file doesn't appear in the diff — likely a hallucination
        vf.evidence_status = "contradicted"
        vf.adjusted_confidence = min(finding.confidence * 0.3, 0.3)
        vf.contradicting_evidence.append({
            "type": "diff_check",
            "message": f"File '{finding.file}' not found in PR diff",
        })
    else:
        # No strong evidence either way — unverified
        vf.evidence_status = "unverified"
        vf.adjusted_confidence = min(finding.confidence * 0.8, 0.8)

    return vf


def _find_supporting_chunks(
    finding: FindingSchema,
    retrieved_chunks: List[RetrievalResult],
) -> List[dict]:
    """Find RAG chunks that support a finding based on relevance."""
    supporting = []
    title_lower = finding.title.lower()
    problem_lower = finding.problem.lower()

    for chunk in retrieved_chunks:
        chunk_text_lower = chunk.text.lower()

        # Check semantic relevance: key terms from finding appear in chunk
        relevance_score = _compute_relevance(title_lower, problem_lower, chunk_text_lower)

        if relevance_score > 0 and chunk.distance < _WEAK_EVIDENCE_THRESHOLD:
            strength = "strong" if chunk.distance < _STRONG_EVIDENCE_THRESHOLD else "weak"
            supporting.append({
                "type": "documentation",
                "path": chunk.path,
                "text": chunk.text[:300],
                "distance": chunk.distance,
                "strength": strength,
                "chunk_id": chunk.chunk_id,
            })

    return supporting


def _compute_relevance(title_lower: str, problem_lower: str, chunk_text: str) -> int:
    """Simple keyword overlap relevance score (0 = none, 1+ = relevant)."""
    # Extract meaningful words (>4 chars) from finding
    finding_words = set(
        w for w in (title_lower + " " + problem_lower).split()
        if len(w) > 4 and w.isalpha()
    )
    # Count how many appear in the chunk
    return sum(1 for word in finding_words if word in chunk_text)


def _find_linter_confirmation(
    finding: FindingSchema,
    linter_issues: List[dict],
) -> List[dict]:
    """Check if any linter issue confirms this finding."""
    confirmations = []

    for issue in linter_issues:
        # Match by file and approximate line
        if finding.file and issue.get("file"):
            finding_file_base = finding.file.split("/")[-1]
            issue_file_base = issue.get("file", "").split("/")[-1]
            if finding_file_base == issue_file_base:
                # File matches — check if line is close (within 5 lines)
                if finding.line and issue.get("line"):
                    if abs(finding.line - issue.get("line", 0)) <= 5:
                        confirmations.append({
                            "type": "linter",
                            "tool": issue.get("tool", "unknown"),
                            "code": issue.get("code"),
                            "file": issue.get("file"),
                            "line": issue.get("line"),
                            "message": issue.get("message", ""),
                            "strength": "strong",
                        })

    return confirmations


def _verify_file_in_diff(finding: FindingSchema, diff: str) -> bool:
    """Verify the finding's cited file appears in the PR diff."""
    if not finding.file:
        return True  # No file cited — can't contradict
    file_name = finding.file.split("/")[-1]
    return file_name in diff or finding.file in diff


def _extract_linter_issues(linter_results: List[dict]) -> List[dict]:
    """
    Flatten linter results into a list of individual issues for lookup.
    Handles Ruff and Bandit output formats.
    """
    issues = []
    for result in linter_results:
        tool = result.get("tool", "unknown")
        raw = result.get("raw_output", {})
        if not isinstance(raw, dict):
            continue

        # Ruff format: {"results": [...]}
        if tool == "ruff" and "results" in raw:
            for item in raw.get("results", []):
                issues.append({
                    "tool": "ruff",
                    "file": item.get("filename"),
                    "line": item.get("location", {}).get("row"),
                    "code": item.get("code"),
                    "message": item.get("message"),
                })

        # Bandit format: {"results": [...]}
        elif tool == "bandit" and "results" in raw:
            for item in raw.get("results", []):
                issues.append({
                    "tool": "bandit",
                    "file": item.get("filename"),
                    "line": item.get("line_number"),
                    "code": item.get("test_id"),
                    "message": item.get("issue_text"),
                    "severity": item.get("issue_severity"),
                })

    return issues
