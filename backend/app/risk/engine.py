"""
PR Risk Engine — RepoMind 2.0

Computes a PR-level risk score (0-100) with explainable factors.
Every score has a breakdown — no opaque risk numbers.

FAIRNESS RULE: This engine analyzes PR risk, NOT developer quality.
Do NOT add developer-scoring, developer ranking, or productivity metrics.

Risk factors (weights sum to 100):
  code_complexity      20  — change size, cyclomatic complexity signals
  security_exposure    25  — security findings, sensitive file changes
  test_risk            15  — test coverage gap, failing tests
  architecture_risk    15  — architecture conflicts, layer violations
  change_size          10  — additions + deletions (raw scale)
  dependency_risk      10  — dependency file changes
  blast_radius_factor   5  — how many modules affected

Risk levels:
  0-25:   low
  26-50:  medium
  51-75:  high
  76-100: critical
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from backend.app.conflicts.engine import DetectedConflict
from backend.app.review.evidence import ValidatedFinding

logger = logging.getLogger(__name__)


@dataclass
class RiskResult:
    """
    Result of the risk calculation.
    Maps directly to the RiskAssessment DB model.
    """
    score: int                          # 0-100
    level: str                          # low | medium | high | critical
    factors: Dict[str, Any]             # Breakdown of each risk factor
    blast_radius: Dict[str, Any]        # Affected modules, files, tests
    test_impact: Dict[str, Any]         # Affected test files, missing tests
    summary: str                        # Human-readable explanation


def calculate_risk(
    diff: str,
    validated_findings: List[ValidatedFinding],
    conflicts: List[DetectedConflict],
    linter_results: List[dict],
    changed_files: List[str],
    pr_title: str = "",
    additions: Optional[int] = None,
    deletions: Optional[int] = None,
) -> RiskResult:
    """
    Calculate PR risk score from available signals.

    Args:
        diff:                The unified diff.
        validated_findings:  Evidence-validated findings from the LLM.
        conflicts:           Detected semantic/mechanical conflicts.
        linter_results:      Raw linter output.
        changed_files:       List of changed file paths.
        pr_title:            PR title for context.
        additions:           Line additions count from GitHub metadata.
        deletions:           Line deletions count from GitHub metadata.

    Returns:
        RiskResult with score, level, and full breakdown.
    """
    factors: Dict[str, Dict] = {}

    # --- Factor 1: Security exposure (weight 25) ---
    security_score, security_detail = _score_security(validated_findings, conflicts, changed_files)
    factors["security_exposure"] = {
        "score": security_score,
        "weight": 25,
        "weighted": int(security_score * 0.25),
        **security_detail,
    }

    # --- Factor 2: Architecture risk (weight 15) ---
    arch_score, arch_detail = _score_architecture(validated_findings, conflicts)
    factors["architecture_risk"] = {
        "score": arch_score,
        "weight": 15,
        "weighted": int(arch_score * 0.15),
        **arch_detail,
    }

    # --- Factor 3: Test risk (weight 15) ---
    test_score, test_detail = _score_test_risk(conflicts, linter_results, changed_files)
    factors["test_risk"] = {
        "score": test_score,
        "weight": 15,
        "weighted": int(test_score * 0.15),
        **test_detail,
    }

    # --- Factor 4: Code complexity (weight 20) ---
    complexity_score, complexity_detail = _score_complexity(diff, validated_findings, linter_results)
    factors["code_complexity"] = {
        "score": complexity_score,
        "weight": 20,
        "weighted": int(complexity_score * 0.20),
        **complexity_detail,
    }

    # --- Factor 5: Change size (weight 10) ---
    size_score, size_detail = _score_change_size(additions, deletions, diff)
    factors["change_size"] = {
        "score": size_score,
        "weight": 10,
        "weighted": int(size_score * 0.10),
        **size_detail,
    }

    # --- Factor 6: Dependency risk (weight 10) ---
    dep_score, dep_detail = _score_dependency_risk(changed_files)
    factors["dependency_risk"] = {
        "score": dep_score,
        "weight": 10,
        "weighted": int(dep_score * 0.10),
        **dep_detail,
    }

    # --- Factor 7: Blast radius (weight 5) ---
    blast_radius = _calculate_blast_radius(changed_files)
    br_score = min(blast_radius["directly_affected"] * 10 + blast_radius["potentially_affected"] * 5, 100)
    factors["blast_radius_factor"] = {
        "score": br_score,
        "weight": 5,
        "weighted": int(br_score * 0.05),
        "details": f"{blast_radius['directly_affected']} directly affected modules",
    }

    # --- Total score ---
    total = sum(f["weighted"] for f in factors.values())
    total = max(0, min(100, total))  # Clamp to 0-100

    level = _score_to_level(total)
    summary = _generate_summary(total, level, factors, validated_findings, conflicts)

    # --- Test impact ---
    test_impact = _calculate_test_impact(changed_files, diff)

    logger.info(
        "Risk calculation complete: score=%d level=%s findings=%d conflicts=%d",
        total,
        level,
        len(validated_findings),
        len(conflicts),
    )

    return RiskResult(
        score=total,
        level=level,
        factors=factors,
        blast_radius=blast_radius,
        test_impact=test_impact,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# Factor scorers
# ---------------------------------------------------------------------------

def _score_security(
    findings: List[ValidatedFinding],
    conflicts: List[DetectedConflict],
    changed_files: List[str],
) -> tuple[int, dict]:
    """Score security exposure (0-100)."""
    score = 0
    reasons = []

    # Critical security findings: +40 each (cap at 80)
    critical_sec = [f for f in findings if f.finding.category == "security" and f.finding.severity == "critical"]
    high_sec = [f for f in findings if f.finding.category == "security" and f.finding.severity == "high"]
    score += min(len(critical_sec) * 40, 80)
    score += min(len(high_sec) * 20, 40)

    if critical_sec:
        reasons.append(f"{len(critical_sec)} critical security finding(s)")
    if high_sec:
        reasons.append(f"{len(high_sec)} high security finding(s)")

    # Security policy conflicts
    sec_conflicts = [c for c in conflicts if c.category == "security_policy"]
    score += min(len(sec_conflicts) * 15, 30)
    if sec_conflicts:
        reasons.append(f"{len(sec_conflicts)} security policy conflict(s)")

    # Sensitive file changes
    sensitive_files = [
        f for f in changed_files
        if any(kw in f.lower() for kw in ["auth", "permission", "security", "password", "token", "key", "secret"])
    ]
    score += min(len(sensitive_files) * 10, 20)
    if sensitive_files:
        reasons.append(f"{len(sensitive_files)} sensitive file(s) modified")

    return min(score, 100), {"reasons": reasons}


def _score_architecture(
    findings: List[ValidatedFinding],
    conflicts: List[DetectedConflict],
) -> tuple[int, dict]:
    """Score architecture risk (0-100)."""
    score = 0
    reasons = []

    arch_findings = [f for f in findings if f.finding.category in ("architecture", "standards_violation")]
    arch_conflicts = [c for c in conflicts if c.category in ("architecture", "api_contract")]

    score += min(len(arch_findings) * 20, 60)
    score += min(len(arch_conflicts) * 25, 50)

    if arch_findings:
        reasons.append(f"{len(arch_findings)} architecture finding(s)")
    if arch_conflicts:
        reasons.append(f"{len(arch_conflicts)} architecture/API conflict(s)")

    return min(score, 100), {"reasons": reasons}


def _score_test_risk(
    conflicts: List[DetectedConflict],
    linter_results: List[dict],
    changed_files: List[str],
) -> tuple[int, dict]:
    """Score test risk (0-100)."""
    score = 0
    reasons = []

    # Test contract conflicts
    test_conflicts = [c for c in conflicts if c.category == "test_contract"]
    if test_conflicts:
        score += 30
        reasons.append("Source changes without test updates")

    # Check for test failures in linter/test output
    for result in linter_results:
        raw = result.get("raw_output", {})
        if isinstance(raw, dict) and raw.get("status") == "error":
            score += 20
            reasons.append(f"Static analysis error in {result.get('tool', 'unknown')}")

    # No test files at all in the PR
    test_files = [f for f in changed_files if "test" in f.lower() or "spec" in f.lower()]
    source_files = [
        f for f in changed_files
        if f.endswith((".py", ".ts", ".js")) and "test" not in f.lower()
    ]
    if source_files and not test_files:
        score += 20
        reasons.append("No test files modified")

    return min(score, 100), {"reasons": reasons}


def _score_complexity(
    diff: str,
    findings: List[ValidatedFinding],
    linter_results: List[dict],
) -> tuple[int, dict]:
    """Score code complexity (0-100)."""
    score = 0
    reasons = []

    # Finding count as complexity signal
    finding_count = len(findings)
    score += min(finding_count * 8, 40)
    if finding_count:
        reasons.append(f"{finding_count} finding(s)")

    # Linter issue count
    linter_issue_count = sum(
        len(r.get("raw_output", {}).get("results", []))
        for r in linter_results
        if isinstance(r.get("raw_output", {}), dict)
    )
    score += min(linter_issue_count * 3, 30)
    if linter_issue_count:
        reasons.append(f"{linter_issue_count} linter issue(s)")

    # Deep nesting in diff (crude proxy for complexity)
    deep_indent = len(re.findall(r'^\+\s{16,}\S', diff, re.MULTILINE))
    score += min(deep_indent * 2, 20)
    if deep_indent > 5:
        reasons.append("Deep nesting detected")

    return min(score, 100), {"reasons": reasons}


def _score_change_size(
    additions: Optional[int],
    deletions: Optional[int],
    diff: str,
) -> tuple[int, dict]:
    """Score change size (0-100)."""
    # Fall back to counting diff lines if metadata not available
    if additions is None:
        additions = len(re.findall(r'^\+[^+]', diff, re.MULTILINE))
    if deletions is None:
        deletions = len(re.findall(r'^-[^-]', diff, re.MULTILINE))

    total_changes = additions + deletions

    if total_changes < 50:
        score = 10
    elif total_changes < 200:
        score = 30
    elif total_changes < 500:
        score = 60
    elif total_changes < 1000:
        score = 80
    else:
        score = 100

    return score, {
        "additions": additions,
        "deletions": deletions,
        "total_changes": total_changes,
        "reasons": [f"{total_changes} total line changes (+{additions}/-{deletions})"],
    }


def _score_dependency_risk(changed_files: List[str]) -> tuple[int, dict]:
    """Score dependency risk (0-100)."""
    dep_files = [
        f for f in changed_files
        if any(f.endswith(dep) for dep in [
            "requirements.txt", "package.json", "Pipfile", "pyproject.toml",
            "go.mod", "pom.xml", "build.gradle", "Gemfile",
        ])
    ]

    score = min(len(dep_files) * 30, 100)
    return score, {
        "dependency_files": dep_files,
        "reasons": [f"{len(dep_files)} dependency file(s) modified"] if dep_files else [],
    }


def _calculate_blast_radius(changed_files: List[str]) -> Dict[str, Any]:
    """Estimate blast radius: how many modules are directly and potentially affected."""
    source_files = [
        f for f in changed_files
        if f.endswith((".py", ".ts", ".js", ".java", ".go"))
    ]
    config_files = [f for f in changed_files if "config" in f.lower() or f.endswith(".toml")]
    test_files = [f for f in changed_files if "test" in f.lower()]

    # Crude blast radius: source files affect ~3-5 modules each on average
    directly_affected = len(source_files)
    potentially_affected = directly_affected * 3  # heuristic

    return {
        "directly_affected": directly_affected,
        "potentially_affected": potentially_affected,
        "changed_source_files": source_files[:10],
        "changed_config_files": config_files[:5],
        "changed_test_files": test_files[:10],
    }


def _calculate_test_impact(changed_files: List[str], diff: str) -> Dict[str, Any]:
    """Estimate which tests are likely affected by the changes."""
    source_files = [
        f for f in changed_files
        if f.endswith((".py", ".ts", ".js")) and "test" not in f.lower()
    ]

    # Generate test file name candidates (heuristic)
    likely_affected_tests = []
    for src in source_files:
        basename = src.split("/")[-1].replace(".py", "").replace(".ts", "").replace(".js", "")
        likely_affected_tests.extend([
            f"test_{basename}.py",
            f"{basename}_test.py",
            f"{basename}.test.ts",
            f"{basename}.spec.ts",
        ])

    # Missing tests: source files that have no corresponding test file changed
    missing_tests = [
        f"test_{src.split('/')[-1]}"
        for src in source_files
        if not any("test" in cf.lower() for cf in changed_files)
    ]

    return {
        "affected_source_files": source_files[:10],
        "likely_affected_tests": likely_affected_tests[:10],
        "missing_test_recommendations": missing_tests[:5],
    }


def _score_to_level(score: int) -> str:
    """Convert numeric score to risk level label."""
    if score <= 25:
        return "low"
    elif score <= 50:
        return "medium"
    elif score <= 75:
        return "high"
    else:
        return "critical"


def _generate_summary(
    score: int,
    level: str,
    factors: Dict,
    findings: List[ValidatedFinding],
    conflicts: List[DetectedConflict],
) -> str:
    """Generate a human-readable risk summary."""
    top_factors = sorted(
        factors.items(),
        key=lambda x: x[1]["weighted"],
        reverse=True,
    )[:3]

    factor_names = {
        "security_exposure": "security exposure",
        "architecture_risk": "architecture risk",
        "test_risk": "test coverage risk",
        "code_complexity": "code complexity",
        "change_size": "change size",
        "dependency_risk": "dependency changes",
        "blast_radius_factor": "blast radius",
    }

    top_names = [factor_names.get(k, k) for k, _ in top_factors if _["weighted"] > 0]

    critical_findings = sum(
        1 for f in findings
        if f.finding.severity in ("critical", "high") and f.evidence_status == "supported"
    )

    parts = [f"Risk score: {score}/100 ({level.upper()})."]
    if top_names:
        parts.append(f"Top risk drivers: {', '.join(top_names)}.")
    if critical_findings:
        parts.append(f"{critical_findings} high/critical supported finding(s).")
    if conflicts:
        parts.append(f"{len(conflicts)} conflict(s) detected.")

    return " ".join(parts)
