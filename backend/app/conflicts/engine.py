"""
Semantic Conflict Engine — RepoMind 2.0

Detects conflicts BEYOND Git merge conflicts.

Supported conflict types:
  mechanical:   Git merge conflict markers in the diff
  semantic:     Architecture, API contract, security policy, data model,
                dependency, test contract, configuration conflicts

The engine runs BEFORE the LLM call and passes findings to the LLM as context.
It also runs AFTER the LLM call to validate LLM-identified conflicts against
actual repository evidence.

Key principle: Never trust the LLM alone for conflict detection.
Every semantic conflict must be grounded in repository evidence (RAG chunks).

Security: Repository isolation is enforced — never mix contexts.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from backend.app.rag.retriever import RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class DetectedConflict:
    """
    A conflict detected by the semantic conflict engine.
    Maps directly to the Conflict DB model.
    """
    conflict_type: str          # mechanical | semantic
    category: str               # architecture | api_contract | security_policy | ...
    severity: str               # critical | high | medium | low
    title: str
    description: str
    evidence: dict = field(default_factory=dict)  # {"expected": ..., "actual": ..., "sources": [...]}
    status: str = "open"


def detect_conflicts(
    diff: str,
    retrieved_chunks: List[RetrievalResult],
    pr_title: str = "",
    pr_description: str = "",
    changed_files: Optional[List[str]] = None,
) -> List[DetectedConflict]:
    """
    Run all conflict detectors and return a combined list.

    Args:
        diff:             The unified diff for the PR.
        retrieved_chunks: RAG chunks retrieved for this PR (repository knowledge).
        pr_title:         PR title for context.
        pr_description:   PR body/description for context.
        changed_files:    List of changed file paths (from PR files API).

    Returns:
        List of DetectedConflict objects sorted by severity.
    """
    conflicts: List[DetectedConflict] = []
    changed_files = changed_files or _extract_files_from_diff(diff)

    # Run each detector
    conflicts.extend(_detect_mechanical_conflicts(diff))
    conflicts.extend(_detect_architecture_conflicts(diff, retrieved_chunks, changed_files))
    conflicts.extend(_detect_security_policy_conflicts(diff, retrieved_chunks, changed_files))
    conflicts.extend(_detect_api_contract_conflicts(diff, retrieved_chunks, changed_files))
    conflicts.extend(_detect_test_contract_conflicts(diff, retrieved_chunks, changed_files))
    conflicts.extend(_detect_configuration_conflicts(diff, changed_files))

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    conflicts.sort(key=lambda c: severity_order.get(c.severity, 99))

    logger.info(
        "Conflict engine: %d conflict(s) detected (%d mechanical, %d semantic)",
        len(conflicts),
        sum(1 for c in conflicts if c.conflict_type == "mechanical"),
        sum(1 for c in conflicts if c.conflict_type == "semantic"),
    )

    return conflicts


# ---------------------------------------------------------------------------
# Detector 1: Mechanical (Git merge conflicts)
# ---------------------------------------------------------------------------

def _detect_mechanical_conflicts(diff: str) -> List[DetectedConflict]:
    """Detect Git merge conflict markers in the diff."""
    conflicts = []
    conflict_markers = ["<<<<<<< ", "=======", ">>>>>>> "]

    for marker in conflict_markers:
        if marker in diff:
            conflicts.append(DetectedConflict(
                conflict_type="mechanical",
                category="git_merge",
                severity="critical",
                title="Git merge conflict markers detected",
                description=(
                    "The PR diff contains unresolved Git merge conflict markers. "
                    "These must be resolved before the PR can be reviewed or merged."
                ),
                evidence={
                    "marker": marker,
                    "message": "Unresolved merge conflict found in diff",
                },
            ))
            break  # One report per PR is sufficient

    return conflicts


# ---------------------------------------------------------------------------
# Detector 2: Architecture conflicts
# ---------------------------------------------------------------------------

_ARCHITECTURE_PATTERNS = [
    # Direct DB access in a controller (bypassing service layer)
    {
        "pattern": r"(controller|router|route).*\.(query|filter|execute|session)",
        "title": "Potential service layer bypass",
        "description": (
            "The PR appears to access the database directly from a controller or router. "
            "Most repository architectures require database access to go through a service layer. "
            "Check ARCHITECTURE.md for the required layering convention."
        ),
        "severity": "high",
        "category": "architecture",
    },
    # Global state modification
    {
        "pattern": r"^\+.*global\s+\w+",
        "title": "Global state modification",
        "description": "The PR modifies global state, which may violate the repository's architectural patterns.",
        "severity": "medium",
        "category": "architecture",
    },
]

_ARCHITECTURE_KEYWORDS_IN_DOCS = [
    "architecture", "service layer", "repository pattern", "layered", "mvc", "clean architecture",
    "must not", "should not", "prohibited", "required pattern",
]

def _detect_architecture_conflicts(
    diff: str,
    retrieved_chunks: List[RetrievalResult],
    changed_files: List[str],
) -> List[DetectedConflict]:
    """Detect architecture pattern violations using diff patterns + RAG knowledge."""
    conflicts = []

    # Check if architecture documentation was retrieved
    arch_chunks = [
        c for c in retrieved_chunks
        if any(kw in c.path.lower() for kw in ["architecture", "adr", "design", "contributing"])
    ]

    for pat_def in _ARCHITECTURE_PATTERNS:
        matches = re.findall(pat_def["pattern"], diff, re.IGNORECASE | re.MULTILINE)
        if not matches:
            continue

        # Only report if we have architecture documentation to back the claim
        sources = [{"path": c.path, "excerpt": c.text[:200]} for c in arch_chunks[:2]]
        if not sources:
            # No architecture docs indexed — emit as unverified (lower severity)
            severity = "low"
            description = (
                pat_def["description"] +
                " Note: No architecture documentation indexed for this repository. "
                "This is an automated heuristic — verify against your conventions."
            )
        else:
            severity = pat_def["severity"]
            description = pat_def["description"]

        conflicts.append(DetectedConflict(
            conflict_type="semantic",
            category=pat_def["category"],
            severity=severity,
            title=pat_def["title"],
            description=description,
            evidence={
                "pattern_matched": str(matches[:3]),
                "sources": sources,
            },
        ))

    return conflicts


# ---------------------------------------------------------------------------
# Detector 3: Security policy conflicts
# ---------------------------------------------------------------------------

_SECURITY_SENSITIVE_PATTERNS = [
    # Hardcoded secrets / credentials
    {
        "pattern": r'^\+.*(password|secret|api_key|token)\s*=\s*["\'][^"\']{8,}["\']',
        "title": "Potential hardcoded secret",
        "severity": "critical",
        "category": "security_policy",
        "description": "The PR appears to contain a hardcoded secret, password, or API key.",
    },
    # SQL injection risk
    {
        "pattern": r'^\+.*f["\'].*SELECT.*\{',
        "title": "Potential SQL injection (f-string query)",
        "severity": "high",
        "category": "security_policy",
        "description": "The PR constructs an SQL query using an f-string, risking SQL injection.",
    },
    # Missing authorization check
    {
        "pattern": r'^\+.*@(router|app)\.(get|post|put|delete|patch)\(',
        "title": "New API endpoint — verify authorization",
        "severity": "medium",
        "category": "security_policy",
        "description": (
            "The PR adds a new API endpoint. Verify that proper authentication and "
            "authorization checks are in place per the repository's security policy."
        ),
    },
]

def _detect_security_policy_conflicts(
    diff: str,
    retrieved_chunks: List[RetrievalResult],
    changed_files: List[str],
) -> List[DetectedConflict]:
    """Detect security policy violations."""
    conflicts = []

    # Check for security documentation
    sec_chunks = [
        c for c in retrieved_chunks
        if any(kw in c.path.lower() for kw in ["security", "auth", "contributing"])
    ]

    for pat_def in _SECURITY_SENSITIVE_PATTERNS:
        matches = re.findall(pat_def["pattern"], diff, re.IGNORECASE | re.MULTILINE)
        if not matches:
            continue

        sources = [{"path": c.path, "excerpt": c.text[:200]} for c in sec_chunks[:2]]
        conflicts.append(DetectedConflict(
            conflict_type="semantic",
            category=pat_def["category"],
            severity=pat_def["severity"],
            title=pat_def["title"],
            description=pat_def["description"],
            evidence={
                "pattern_matched": str(matches[:2]),
                "sources": sources,
            },
        ))

    return conflicts


# ---------------------------------------------------------------------------
# Detector 4: API contract conflicts
# ---------------------------------------------------------------------------

def _detect_api_contract_conflicts(
    diff: str,
    retrieved_chunks: List[RetrievalResult],
    changed_files: List[str],
) -> List[DetectedConflict]:
    """Detect changes that may break existing API contracts."""
    conflicts = []

    # Check if any schema/model files are changed
    schema_files = [
        f for f in changed_files
        if any(kw in f.lower() for kw in ["schema", "model", "serializer", "dto", "contract"])
    ]

    if not schema_files:
        return conflicts

    # Look for field removal/rename patterns in diff
    removed_fields = re.findall(r'^-\s+(\w+)\s*:', diff, re.MULTILINE)
    added_fields = re.findall(r'^\+\s+(\w+)\s*:', diff, re.MULTILINE)

    removed_not_added = set(removed_fields) - set(added_fields)
    if removed_not_added and schema_files:
        api_chunks = [
            c for c in retrieved_chunks
            if any(kw in c.path.lower() for kw in ["api", "schema", "contract", "readme"])
        ]
        conflicts.append(DetectedConflict(
            conflict_type="semantic",
            category="api_contract",
            severity="high",
            title="Potential API contract break — fields removed from schema",
            description=(
                f"Fields removed from schema files without corresponding additions: "
                f"{', '.join(list(removed_not_added)[:5])}. "
                f"This may break existing API consumers."
            ),
            evidence={
                "removed_fields": list(removed_not_added)[:10],
                "affected_files": schema_files[:5],
                "sources": [{"path": c.path, "excerpt": c.text[:200]} for c in api_chunks[:2]],
            },
        ))

    return conflicts


# ---------------------------------------------------------------------------
# Detector 5: Test contract conflicts
# ---------------------------------------------------------------------------

def _detect_test_contract_conflicts(
    diff: str,
    retrieved_chunks: List[RetrievalResult],
    changed_files: List[str],
) -> List[DetectedConflict]:
    """Detect when source files are changed but tests are not updated."""
    conflicts = []

    source_files = [
        f for f in changed_files
        if not any(kw in f.lower() for kw in ["test", "spec", "fixture", "mock"])
        and f.endswith((".py", ".ts", ".js", ".java", ".go"))
    ]
    test_files = [
        f for f in changed_files
        if any(kw in f.lower() for kw in ["test", "spec"])
    ]

    if source_files and not test_files:
        # Source changed but no test files changed — check if tests exist for these modules
        test_chunks = [
            c for c in retrieved_chunks
            if any(kw in c.path.lower() for kw in ["test", "testing", "contributing"])
        ]
        if test_chunks:
            # Only flag if the repo clearly has a test convention
            conflicts.append(DetectedConflict(
                conflict_type="semantic",
                category="test_contract",
                severity="medium",
                title="Source changes without test updates",
                description=(
                    f"{len(source_files)} source file(s) modified but no test files updated. "
                    "The repository has a testing convention. Consider adding or updating tests."
                ),
                evidence={
                    "source_files": source_files[:5],
                    "test_files_changed": [],
                    "sources": [{"path": c.path, "excerpt": c.text[:200]} for c in test_chunks[:2]],
                },
            ))

    return conflicts


# ---------------------------------------------------------------------------
# Detector 6: Configuration conflicts
# ---------------------------------------------------------------------------

_CONFIG_FILES = [
    "settings.py", "config.py", ".env", "pyproject.toml",
    "package.json", "docker-compose.yml", "alembic.ini",
]

def _detect_configuration_conflicts(
    diff: str,
    changed_files: List[str],
) -> List[DetectedConflict]:
    """Flag configuration file changes for human review."""
    conflicts = []

    config_files_changed = [
        f for f in changed_files
        if any(f.endswith(cfg) or f == cfg for cfg in _CONFIG_FILES)
        or "config" in f.lower()
    ]

    if config_files_changed:
        conflicts.append(DetectedConflict(
            conflict_type="semantic",
            category="configuration",
            severity="low",
            title="Configuration files modified",
            description=(
                f"The PR modifies configuration files: {', '.join(config_files_changed[:5])}. "
                "Verify that these changes are intentional and do not affect other environments."
            ),
            evidence={
                "config_files": config_files_changed[:10],
            },
        ))

    return conflicts


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _extract_files_from_diff(diff: str) -> List[str]:
    """Extract changed file paths from unified diff headers."""
    paths = re.findall(r'^\+\+\+ b/(.+)$', diff, flags=re.MULTILINE)
    return [p for p in paths if p != "/dev/null"]
