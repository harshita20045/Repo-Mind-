# 08 — Feature Flow: Conflict Detection Engine

## Feature Summary
The conflict detection engine runs as **Stage 6** of the review pipeline, before the LLM call. It uses 6 deterministic detectors combining regex pattern matching on the unified diff with RAG-grounded context to identify conflicts that go beyond standard Git merge conflicts. Results are stored in the `conflict` table and shown separately from findings in the UI.

---

## Entry Point

File: `backend/app/review/service.py` (Stage 6)

```python
detected_conflicts = detect_conflicts(
    diff=diff,
    retrieved_chunks=retrieved_chunks,
    pr_title=pr.title or "",
    pr_description="",
    changed_files=changed_files,
)
_persist_conflicts(db, run, detected_conflicts)
```

---

## `detect_conflicts()` Orchestrator

File: `backend/app/conflicts/engine.py` → `detect_conflicts()`

```python
conflicts = []
changed_files = changed_files or _extract_files_from_diff(diff)

conflicts.extend(_detect_mechanical_conflicts(diff))
conflicts.extend(_detect_architecture_conflicts(diff, retrieved_chunks, changed_files))
conflicts.extend(_detect_security_policy_conflicts(diff, retrieved_chunks, changed_files))
conflicts.extend(_detect_api_contract_conflicts(diff, retrieved_chunks, changed_files))
conflicts.extend(_detect_test_contract_conflicts(diff, retrieved_chunks, changed_files))
conflicts.extend(_detect_configuration_conflicts(diff, changed_files))

# Sort by severity: critical > high > medium > low
severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
conflicts.sort(key=lambda c: severity_order.get(c.severity, 99))
```

---

## Detector 1: Mechanical Conflicts

```python
def _detect_mechanical_conflicts(diff: str) -> List[DetectedConflict]:
    conflict_markers = ["<<<<<<< ", "=======", ">>>>>>> "]
    for marker in conflict_markers:
        if marker in diff:
            return [DetectedConflict(
                conflict_type="mechanical",
                category="git_merge",
                severity="critical",
                title="Git merge conflict markers detected",
                ...
            )]
    return []
```

Checks for any of the 3 standard Git conflict markers. Reports at most one conflict per PR (breaks after first hit).

---

## Detector 2: Architecture Conflicts

```python
_ARCHITECTURE_PATTERNS = [
    {
        "pattern": r"(controller|router|route).*\.(query|filter|execute|session)",
        "title": "Potential service layer bypass",
        "severity": "high",
        "category": "architecture",
    },
    {
        "pattern": r"^\+.*global\s+\w+",
        "title": "Global state modification",
        "severity": "medium",
        "category": "architecture",
    },
]
```

For each pattern:
1. `re.findall(pattern, diff, re.IGNORECASE | re.MULTILINE)`
2. If matches found, check for architecture docs in RAG chunks (path contains `architecture`, `adr`, `design`, `contributing`)
3. If no architecture docs: report as severity `"low"` with disclaimer
4. If docs present: report at stated severity with excerpt evidence

---

## Detector 3: Security Policy Conflicts

```python
_SECURITY_SENSITIVE_PATTERNS = [
    {
        "pattern": r'^+.*(password|secret|api_key|token)\s*=\s*["'][^"']{8,}["']',
        "title": "Potential hardcoded secret",
        "severity": "critical",
        "category": "security_policy",
    },
    {
        "pattern": r'^+.*f["'].*SELECT.*\{',
        "title": "Potential SQL injection (f-string query)",
        "severity": "high",
        "category": "security_policy",
    },
    {
        "pattern": r'^+.*@(router|app)\.(get|post|put|delete|patch)\(',
        "title": "New API endpoint — verify authorization",
        "severity": "medium",
        "category": "security_policy",
    },
]
```

Each pattern is matched against the unified diff. Security documentation chunks (path contains `security`, `auth`, `contributing`) are included as evidence sources.

---

## Detector 4: API Contract Conflicts

```python
def _detect_api_contract_conflicts(diff, retrieved_chunks, changed_files):
    schema_files = [
        f for f in changed_files
        if any(kw in f.lower() for kw in ["schema", "model", "serializer", "dto", "contract"])
    ]
    
    if not schema_files:
        return []
    
    removed_fields = re.findall(r'^-\s+(\w+)\s*:', diff, re.MULTILINE)
    added_fields = re.findall(r'^\+\s+(\w+)\s*:', diff, re.MULTILINE)
    removed_not_added = set(removed_fields) - set(added_fields)
    
    if removed_not_added:
        # Report: fields removed from schema without additions
        return [DetectedConflict(severity="high", category="api_contract", ...)]
```

Only triggers if schema/model files are in the changed file list. Detects breaking changes where fields are removed but not added back.

---

## Detector 5: Test Contract Conflicts

```python
def _detect_test_contract_conflicts(diff, retrieved_chunks, changed_files):
    source_files = [
        f for f in changed_files
        if not any(kw in f.lower() for kw in ["test", "spec", "fixture", "mock"])
        and f.endswith((".py", ".ts", ".js", ".java", ".go"))
    ]
    test_files = [f for f in changed_files if "test" in f.lower() or "spec" in f.lower()]
    
    if source_files and not test_files:
        test_chunks = [c for c in retrieved_chunks if "test" in c.path.lower()]
        if test_chunks:   # Only flag if repo has test conventions
            return [DetectedConflict(severity="medium", category="test_contract", ...)]
    
    return []
```

Requires both: source files changed AND RAG-indexed test documentation. Won't false-positive on repos with no test infrastructure.

---

## Detector 6: Configuration Conflicts

```python
_CONFIG_FILES = [
    "settings.py", "config.py", ".env", "pyproject.toml",
    "package.json", "docker-compose.yml", "alembic.ini",
]

def _detect_configuration_conflicts(diff, changed_files):
    config_files_changed = [
        f for f in changed_files
        if any(f.endswith(cfg) or f == cfg for cfg in _CONFIG_FILES)
        or "config" in f.lower()
    ]
    if config_files_changed:
        return [DetectedConflict(severity="low", category="configuration", ...)]
    return []
```

Flags any configuration file modifications for human review. Always reported at `"low"` severity as informational.

---

## DetectedConflict Dataclass

```python
@dataclass
class DetectedConflict:
    conflict_type: str   # "mechanical" | "semantic"
    category: str        # "git_merge" | "architecture" | "api_contract" | "security_policy"
                         # | "test_contract" | "configuration" | "data_model" | "recent_change"
    severity: str        # "critical" | "high" | "medium" | "low"
    title: str
    description: str
    evidence: dict       # {"expected": ..., "actual": ..., "sources": [...]}
    status: str = "open"
```

Maps directly to `Conflict` SQLAlchemy model.

---

## Persistence

File: `backend/app/review/service.py` → `_persist_conflicts()`

```python
for c in conflicts:
    db.add(Conflict(
        review_run_id=run.id,
        conflict_type=c.conflict_type,
        category=c.category,
        severity=c.severity,
        title=c.title,
        description=c.description,
        evidence=c.evidence,    # JSONB
        status="open",
    ))
db.flush()
```

---

## Conflict Lifecycle

| Status | Meaning |
|---|---|
| `open` | Conflict detected, not yet actioned |
| `dismissed` | Human reviewer dismissed as not applicable |
| `resolved` | Conflict resolved (future) |

Currently only `open` is ever set (dismiss/resolve via `HumanDecision` mechanism planned).

---

## Use of Conflicts in Risk Scoring

File: `backend/app/risk/engine.py`

```python
# Security exposure factor
sec_conflicts = [c for c in conflicts if c.category == "security_policy"]
score += min(len(sec_conflicts) * 15, 30)

# Architecture risk factor
arch_conflicts = [c for c in conflicts if c.category in ("architecture", "api_contract")]
score += min(len(arch_conflicts) * 25, 50)

# Test risk factor
test_conflicts = [c for c in conflicts if c.category == "test_contract"]
if test_conflicts:
    score += 30
```

---

## Key Files

| File | Location | Role |
|---|---|---|
| `engine.py` | `backend/app/conflicts/engine.py` | `detect_conflicts()`, 6 detector functions |
| `models.py` | `backend/app/review/models.py` | `Conflict` SQLAlchemy model |
| `service.py` | `backend/app/review/service.py` | `_persist_conflicts()` |
| `engine.py` (risk) | `backend/app/risk/engine.py` | Consumes `DetectedConflict` list |
