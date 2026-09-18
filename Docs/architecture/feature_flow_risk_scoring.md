# 09 — Feature Flow: Risk Scoring Engine

## Feature Summary
After findings are validated and conflicts detected, the risk engine calculates a **0–100 risk score** with 7 weighted factors. Every score has a human-readable `summary`, a `factors` breakdown (JSONB), and `blast_radius`/`test_impact` estimates. No developer identity metrics are used (fairness rule enforced in code comments).

---

## Entry Point

File: `backend/app/review/service.py` (Stage 9)

```python
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
```

---

## `calculate_risk()` Structure

File: `backend/app/risk/engine.py`

```python
def calculate_risk(...) -> RiskResult:
    factors = {}
    
    security_score, sec_detail = _score_security(validated_findings, conflicts, changed_files)
    factors["security_exposure"] = {"score": security_score, "weight": 25, "weighted": int(security_score * 0.25), **sec_detail}
    
    arch_score, arch_detail = _score_architecture(validated_findings, conflicts)
    factors["architecture_risk"] = {"score": arch_score, "weight": 15, "weighted": int(arch_score * 0.15), **arch_detail}
    
    test_score, test_detail = _score_test_risk(conflicts, linter_results, changed_files)
    factors["test_risk"] = {"score": test_score, "weight": 15, "weighted": int(test_score * 0.15), **test_detail}
    
    complexity_score, comp_detail = _score_complexity(diff, validated_findings, linter_results)
    factors["code_complexity"] = {"score": complexity_score, "weight": 20, "weighted": int(complexity_score * 0.20), **comp_detail}
    
    size_score, size_detail = _score_change_size(additions, deletions, diff)
    factors["change_size"] = {"score": size_score, "weight": 10, "weighted": int(size_score * 0.10), **size_detail}
    
    dep_score, dep_detail = _score_dependency_risk(changed_files)
    factors["dependency_risk"] = {"score": dep_score, "weight": 10, "weighted": int(dep_score * 0.10), **dep_detail}
    
    blast_radius = _calculate_blast_radius(changed_files)
    br_score = min(blast_radius["directly_affected"] * 10 + blast_radius["potentially_affected"] * 5, 100)
    factors["blast_radius_factor"] = {"score": br_score, "weight": 5, "weighted": int(br_score * 0.05), ...}
    
    total = sum(f["weighted"] for f in factors.values())
    total = max(0, min(100, total))   # Clamp 0-100
    level = _score_to_level(total)
    summary = _generate_summary(total, level, factors, validated_findings, conflicts)
    test_impact = _calculate_test_impact(changed_files, diff)
    
    return RiskResult(score=total, level=level, factors=factors, blast_radius=blast_radius, test_impact=test_impact, summary=summary)
```

---

## 7 Weighted Factors

### Factor 1: Security Exposure (Weight: 25%)

```python
def _score_security(findings, conflicts, changed_files) -> tuple[int, dict]:
    score = 0
    
    critical_sec = [f for f in findings if f.finding.category == "security" and f.finding.severity == "critical"]
    high_sec = [f for f in findings if f.finding.category == "security" and f.finding.severity == "high"]
    score += min(len(critical_sec) * 40, 80)     # +40 per critical (capped 80)
    score += min(len(high_sec) * 20, 40)          # +20 per high (capped 40)
    
    sec_conflicts = [c for c in conflicts if c.category == "security_policy"]
    score += min(len(sec_conflicts) * 15, 30)     # +15 per sec conflict (capped 30)
    
    sensitive_files = [f for f in changed_files if any(kw in f.lower() for kw in
        ["auth", "permission", "security", "password", "token", "key", "secret"])]
    score += min(len(sensitive_files) * 10, 20)   # +10 per sensitive file (capped 20)
    
    return min(score, 100), {"reasons": reasons}
```

---

### Factor 2: Architecture Risk (Weight: 15%)

```python
def _score_architecture(findings, conflicts):
    arch_findings = [f for f in findings if f.finding.category in ("architecture", "standards_violation")]
    arch_conflicts = [c for c in conflicts if c.category in ("architecture", "api_contract")]
    
    score += min(len(arch_findings) * 20, 60)    # +20 per arch finding (capped 60)
    score += min(len(arch_conflicts) * 25, 50)   # +25 per arch conflict (capped 50)
```

---

### Factor 3: Test Risk (Weight: 15%)

```python
def _score_test_risk(conflicts, linter_results, changed_files):
    test_conflicts = [c for c in conflicts if c.category == "test_contract"]
    if test_conflicts: score += 30
    
    # Linter errors (status="error" in raw_output)
    for result in linter_results:
        if raw.get("status") == "error": score += 20
    
    # Source changed without test files
    if source_files and not test_files: score += 20
```

---

### Factor 4: Code Complexity (Weight: 20%)

```python
def _score_complexity(diff, findings, linter_results):
    finding_count = len(findings)
    score += min(finding_count * 8, 40)    # +8 per finding (capped 40)
    
    linter_issue_count = sum(len(r["raw_output"].get("results", [])) for r in linter_results)
    score += min(linter_issue_count * 3, 30)  # +3 per linter issue (capped 30)
    
    # Deep nesting: lines starting with 16+ spaces after "+"
    deep_indent = len(re.findall(r'^\+\s{16,}\S', diff, re.MULTILINE))
    score += min(deep_indent * 2, 20)
```

---

### Factor 5: Change Size (Weight: 10%)

```python
def _score_change_size(additions, deletions, diff):
    total = additions + deletions
    
    # Falls back to counting diff lines if GitHub metadata unavailable
    if additions is None: additions = len(re.findall(r'^\+[^+]', diff, re.MULTILINE))
    if deletions is None: deletions = len(re.findall(r'^-[^-]', diff, re.MULTILINE))
    
    if total < 50:     score = 10
    elif total < 200:  score = 30
    elif total < 500:  score = 60
    elif total < 1000: score = 80
    else:              score = 100
```

---

### Factor 6: Dependency Risk (Weight: 10%)

```python
_DEP_FILES = ["requirements.txt", "package.json", "Pipfile", "pyproject.toml",
              "go.mod", "pom.xml", "build.gradle", "Gemfile"]

def _score_dependency_risk(changed_files):
    dep_files = [f for f in changed_files if any(f.endswith(d) for d in _DEP_FILES)]
    score = min(len(dep_files) * 30, 100)   # +30 per dep file (capped 100)
```

---

### Factor 7: Blast Radius (Weight: 5%)

```python
def _calculate_blast_radius(changed_files):
    source_files = [f for f in changed_files if f.endswith((".py", ".ts", ".js", ".java", ".go"))]
    directly_affected = len(source_files)
    potentially_affected = directly_affected * 3   # Heuristic: ~3 dependent modules per file

br_score = min(directly_affected * 10 + potentially_affected * 5, 100)
```

---

## Risk Level Thresholds

```python
def _score_to_level(score: int) -> str:
    if score <= 25:  return "low"
    if score <= 50:  return "medium"
    if score <= 75:  return "high"
    return "critical"
```

---

## Summary Generation

```python
def _generate_summary(score, level, factors, findings, conflicts) -> str:
    top_factors = sorted(factors.items(), key=lambda x: x[1]["weighted"], reverse=True)[:3]
    critical_findings = sum(1 for f in findings
        if f.finding.severity in ("critical", "high") and f.evidence_status == "supported")
    
    parts = [f"Risk score: {score}/100 ({level.upper()})."]
    if top_names: parts.append(f"Top risk drivers: {', '.join(top_names)}.")
    if critical_findings: parts.append(f"{critical_findings} high/critical supported finding(s).")
    if conflicts: parts.append(f"{len(conflicts)} conflict(s) detected.")
    return " ".join(parts)
```

---

## Blast Radius and Test Impact

### `_calculate_blast_radius(changed_files)` returns:
```python
{
    "directly_affected": 3,      # Source files changed
    "potentially_affected": 9,   # heuristic: directly * 3
    "changed_source_files": [...],
    "changed_config_files": [...],
    "changed_test_files": [...]
}
```

### `_calculate_test_impact(changed_files, diff)` returns:
```python
{
    "affected_source_files": [...],
    "likely_affected_tests": ["test_service.py", "service_test.py", ...],  # Heuristic candidates
    "missing_test_recommendations": ["test_service.py", ...]
}
```

---

## Persistence

File: `backend/app/review/service.py` → `_persist_risk()`

```python
db.add(RiskAssessment(
    review_run_id=run.id,
    score=risk_result.score,              # int 0-100
    level=risk_result.level,              # "low"|"medium"|"high"|"critical"
    factors=risk_result.factors,          # JSONB: full breakdown
    blast_radius=risk_result.blast_radius, # JSONB
    test_impact=risk_result.test_impact,   # JSONB
    summary=risk_result.summary,          # Human-readable text
    calculated_at=datetime.now(timezone.utc),
))
db.flush()
```

---

## `RiskResult` Dataclass

```python
@dataclass
class RiskResult:
    score: int              # 0-100
    level: str              # low | medium | high | critical
    factors: Dict[str, Any] # Per-factor breakdown
    blast_radius: Dict[str, Any]
    test_impact: Dict[str, Any]
    summary: str            # Human-readable explanation
```

---

## Fairness Rule

From `engine.py` file docstring:
```
FAIRNESS RULE: This engine analyzes PR risk, NOT developer quality.
Do NOT add developer-scoring, developer ranking, or productivity metrics.
```

No `user_id`, `author`, or developer-identity fields are included in any risk calculation.

---

## Key Files

| File | Location | Role |
|---|---|---|
| `engine.py` | `backend/app/risk/engine.py` | `calculate_risk()`, all 7 scorer functions, `RiskResult` |
| `models.py` | `backend/app/review/models.py` | `RiskAssessment` SQLAlchemy model |
| `service.py` | `backend/app/review/service.py` | `_persist_risk()` |
