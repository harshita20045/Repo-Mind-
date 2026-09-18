# 06 — Feature Flow: Static Analysis (Ruff + Bandit)

## Feature Summary
During Stage 5 of the review pipeline, changed Python files from the PR are downloaded to a temporary directory, and two linters run against them in isolated subprocesses: **Ruff** (style + linting) and **Bandit** (security). Results are stored as JSONB in `linter_result` and used in both the LLM prompt and the evidence validation layer.

---

## End-to-End Flow

### Step 1: Entry Point
File: `backend/app/review/service.py` (Stage 5)

```python
run_linters(
    db=db,
    client=client,             # Authenticated GitHubClient
    owner=repo.github_owner,
    repo=repo.github_name,
    pr_number=pr.github_number,
    review_run_id=run.id,
)
```

---

### Step 2: Fetch PR File Metadata
File: `backend/app/linter/service.py` → `run_linters()`

```python
pr_files = client.get_pull_request_files(owner, repo, pr_number)
# -> GET /repos/{owner}/{repo}/pulls/{number}/files

files_to_lint = [
    f for f in pr_files
    if f["filename"].endswith(".py")
    and f["status"] != "removed"
]
```

Only Python files are linted. Removed files are excluded.

---

### Step 3: Build Temporary Workspace
File: `backend/app/linter/service.py`

```python
with tempfile.TemporaryDirectory() as temp_dir:
    for f in files_to_lint:
        path = f["filename"]
        sha = f["sha"]
        
        # Safe join (path traversal prevention)
        secure_path = _safe_join(temp_dir, path)
        os.makedirs(os.path.dirname(secure_path), exist_ok=True)
        
        content = client.get_blob_content(owner, repo, sha)
        # -> GET /repos/{owner}/{repo}/git/blobs/{sha}
        
        with open(secure_path, "wb") as out:
            out.write(content)
```

`_safe_join()` verifies the final path is still within `temp_dir` (prevents `../../../etc/passwd` attacks).

---

### Step 4: Fetch Repository Config Files
File: `backend/app/linter/service.py`

```python
CONFIG_FILES = [
    "pyproject.toml", "ruff.toml", ".ruff.toml", "bandit.yaml", ".bandit"
]

for config_file in CONFIG_FILES:
    contents = client.get_repository_contents(owner, repo, config_file)
    # Decode base64 + write to temp_dir
```

This ensures Ruff and Bandit run with the repository's own configuration. If config files don't exist, GitHub API returns 404 which is silently ignored.

---

### Step 5: Run Ruff
File: `backend/app/linter/tools.py` → `RuffLinter.execute()`

```python
cmd = ["ruff", "check", "--output-format", "json"] + files_to_lint
result = subprocess.run(
    cmd,
    cwd=workspace_path,
    capture_output=True,
    text=True,
    timeout=30,
    shell=False     # NEVER shell=True
)
```

Exit codes:
- `0` — no violations
- `1` — violations found (still successful execution)
- Other — error (stored as error result)

Output parsed as JSON. Schema (per violation):
```json
{
    "filename": "app/auth/router.py",
    "location": {"row": 42, "column": 5},
    "code": "E501",
    "message": "Line too long (120 > 88)"
}
```

---

### Step 6: Run Bandit
File: `backend/app/linter/tools.py` → `BanditLinter.execute()`

```python
cmd = ["bandit", "-f", "json"] + files_to_lint
result = subprocess.run(
    cmd,
    cwd=workspace_path,
    capture_output=True,
    text=True,
    timeout=30,
    shell=False
)
```

Bandit output schema (per result):
```json
{
    "filename": "app/auth/service.py",
    "line_number": 15,
    "test_id": "B106",
    "issue_text": "Possible hardcoded password",
    "issue_severity": "MEDIUM"
}
```

---

### Step 7: Persist Results
File: `backend/app/linter/service.py` → `_persist_result()`

```python
lr = LinterResult(
    review_run_id=review_run_id,
    tool=tool_name,       # "ruff" or "bandit"
    raw_output=result     # Full JSON dict stored as JSONB
)
db.add(lr)
db.commit()
```

On failure:
```python
_persist_failure(db, review_run_id, tool_name, "execution_failed", stderr[:1000])
```

---

### Step 8: Usage in Review Pipeline

**In LLM prompt** (`review/service.py`):
```python
linter_rows = db.query(LinterResult).filter_by(review_run_id=run.id).all()
linter_text = "\n".join([f"Tool: {lr.tool}\nResult:\n{json.dumps(lr.raw_output, indent=2)}"])
# -> Injected into build_user_content() as "LINTER FINDINGS (UNTRUSTED EVIDENCE)"
```

**In evidence validation** (`review/evidence.py`):
```python
linter_issues = _extract_linter_issues(linter_results)
# -> Used to confirm LLM findings by file + line number matching
```

**In risk scoring** (`risk/engine.py`):
```python
linter_issue_count = sum(len(r["raw_output"].get("results", [])) for r in linter_results)
# -> Contributes to code_complexity factor
```

---

## Key Files

| File | Location | Role |
|---|---|---|
| `service.py` | `backend/app/linter/service.py` | `run_linters()` orchestration + `_persist_result()` |
| `tools.py` | `backend/app/linter/tools.py` | `LinterTool` protocol, `RuffLinter`, `BanditLinter` |
| `models.py` | `backend/app/review/models.py` | `LinterResult` (tool, raw_output JSONB) |

---

## Security Properties

| Property | Implementation |
|---|---|
| No shell injection | `shell=False` in all `subprocess.run()` calls |
| Path traversal prevention | `_safe_join()` validates all paths stay within `temp_dir` |
| Temp directory cleanup | `with tempfile.TemporaryDirectory()` — auto-cleanup on exit |
| Timeout | 30s per linter — prevents runaway processes |
| No secrets in output | PAT never written to temp workspace (only source files + config) |

---

## Linter Output in Evidence Validation

File: `backend/app/review/evidence.py` → `_extract_linter_issues()`

```python
# Ruff format
if tool == "ruff" and "results" in raw:
    for item in raw["results"]:
        issues.append({
            "tool": "ruff",
            "file": item["filename"],
            "line": item["location"]["row"],
            "code": item["code"],
            "message": item["message"],
        })

# Bandit format  
elif tool == "bandit" and "results" in raw:
    for item in raw["results"]:
        issues.append({
            "tool": "bandit",
            "file": item["filename"],
            "line": item["line_number"],
            "code": item["test_id"],
            "message": item["issue_text"],
            "severity": item["issue_severity"],
        })
```

Matching against findings:
```python
# File basename match + line within 5
finding_file_base == issue_file_base  AND  abs(finding.line - issue.line) <= 5
```
When matched: evidence `strength = "strong"`, boosts finding's `adjusted_confidence`.
