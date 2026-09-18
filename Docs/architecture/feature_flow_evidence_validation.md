# 20 — Feature Flow: Evidence Validation (Hallucination Mitigation)

## Feature Summary
After the LLM returns findings, `evidence.py` validates each finding against three independent evidence sources: RAG chunks, linter output, and the diff itself. Findings without supporting evidence have their confidence scores penalized. Findings citing files not present in the diff are classified as `contradicted` with a severe penalty. This is the primary anti-hallucination mechanism in RepoMind.

---

## Why This Exists

LLMs can hallucinate:
- File paths that don't exist in the PR
- Code patterns that aren't in the diff
- Rules from documentation that weren't retrieved
- Line numbers that are off by large amounts

Rather than trusting LLM output blindly, every finding is cross-validated against grounded evidence before being shown to the user.

---

## Entry Point

File: `backend/app/review/service.py` (Stage 8)

```python
validated_findings = validate_findings(
    findings=findings_raw,           # List[FindingSchema] from LLM
    retrieved_chunks=retrieved_chunks, # List[RetrievalResult] from RAG
    linter_results=linter_results_raw, # List[dict] from LinterResult rows
    diff=diff,                        # Unified diff string
)
```

---

## `validate_findings()` Orchestration

File: `backend/app/review/evidence.py` → `validate_findings()`

```python
linter_issues = _extract_linter_issues(linter_results)
diff_files = _extract_files_from_diff(diff)

validated = []
for finding in findings:
    evidence = _validate_finding(finding, retrieved_chunks, linter_issues, diff_files)
    validated.append(evidence)
return validated
```

---

## `_validate_finding()` — Per-Finding Logic

### Check 1: Diff Verification (Hallucination Detection)

```python
finding_file = finding.file
if finding_file:
    file_in_diff = any(
        finding_file in diff_file or diff_file in finding_file
        for diff_file in diff_files
    )
    if not file_in_diff and diff_files:
        # File cited by LLM is NOT in the diff — highly suspicious
        return ValidatedFinding(
            finding=finding,
            evidence_status="contradicted",
            adjusted_confidence=finding.confidence * 0.3,  # Severe penalty
            supporting_evidence=[],
            contradicting_evidence=[{
                "type": "diff_verification",
                "reason": f"File {finding_file!r} not found in PR diff",
                "diff_files": list(diff_files[:5]),
            }],
        )
```

If the LLM claims a finding is in `app/auth/service.py` but that file isn't in the diff, the confidence drops to 30% of the original.

---

### Check 2: RAG Chunk Support

```python
supporting_chunks = []
for chunk in retrieved_chunks:
    keywords = _extract_keywords(f"{finding.title} {finding.problem}")
    chunk_lower = chunk.text.lower()
    
    matching_keywords = [kw for kw in keywords if kw in chunk_lower]
    keyword_overlap = len(matching_keywords) / max(len(keywords), 1)
    
    if keyword_overlap > 0.3 and chunk.distance < 0.7:  # Semantic + keyword threshold
        strength = "strong" if chunk.distance < 0.4 else "weak"
        supporting_chunks.append({
            "type": "rag_chunk",
            "path": chunk.path,
            "text": chunk.text[:200],
            "strength": strength,
            "distance": chunk.distance,
        })
```

Keyword extraction (`_extract_keywords()`):
```python
# Remove common English stop words + short words
stop_words = {"the", "a", "an", "is", "in", "of", "to", "and", ...}
words = re.findall(r'\b[a-zA-Z][a-zA-Z_]{2,}\b', text)
return [w.lower() for w in words if w.lower() not in stop_words][:10]  # Top 10 keywords
```

---

### Check 3: Linter Confirmation

```python
confirming_linters = []
for issue in linter_issues:
    finding_basename = os.path.basename(finding.file or "")
    issue_basename = os.path.basename(issue["file"])
    
    file_match = finding_basename and issue_basename and finding_basename == issue_basename
    line_match = finding.line and abs(finding.line - issue.get("line", 0)) <= 5
    
    if file_match and line_match:
        confirming_linters.append({
            "type": "linter_confirmation",
            "tool": issue["tool"],
            "code": issue["code"],
            "message": issue["message"],
            "strength": "strong",
        })
```

---

### Evidence Status Assignment

```python
all_supporting = supporting_chunks + confirming_linters
has_strong = any(e.get("strength") == "strong" for e in all_supporting)

if has_strong:
    evidence_status = "supported"
    confidence_multiplier = 1.1   # Boost (capped at 1.0)
elif all_supporting:
    evidence_status = "supported"
    confidence_multiplier = 1.0   # No change
else:
    evidence_status = "unverified"
    confidence_multiplier = 0.8   # Penalty for no evidence
    
adjusted_confidence = min(finding.confidence * confidence_multiplier, 1.0)
```

Summary of confidence adjustments:

| Condition | Status | Confidence Multiplier |
|---|---|---|
| File not in diff | `contradicted` | × 0.3 (severe) |
| Strong RAG or linter match | `supported` | × 1.1 (capped at 1.0) |
| Weak RAG match only | `supported` | × 1.0 |
| No evidence at all | `unverified` | × 0.8 |

---

## `ValidatedFinding` Dataclass

```python
@dataclass
class ValidatedFinding:
    finding: FindingSchema                    # Original LLM finding
    evidence_status: str                      # supported | unverified | contradicted
    adjusted_confidence: float               # After multiplier applied
    supporting_evidence: List[dict]          # RAG chunks + linter issues
    contradicting_evidence: List[dict]       # Hallucination signals
```

---

## Linter Issue Extraction

```python
def _extract_linter_issues(linter_results: List[dict]) -> List[dict]:
    issues = []
    for result in linter_results:
        tool = result.get("tool")
        raw = result.get("raw_output", {})
        
        if tool == "ruff" and "findings" in raw:
            for item in raw["findings"]:
                issues.append({
                    "tool": "ruff",
                    "file": item.get("filename", ""),
                    "line": item.get("location", {}).get("row", 0),
                    "code": item.get("code", ""),
                    "message": item.get("message", ""),
                })
        
        elif tool == "bandit" and "results" in raw:
            for item in raw["results"]:
                issues.append({
                    "tool": "bandit",
                    "file": item.get("filename", ""),
                    "line": item.get("line_number", 0),
                    "code": item.get("test_id", ""),
                    "message": item.get("issue_text", ""),
                    "severity": item.get("issue_severity", ""),
                })
    return issues
```

---

## Persistence of Evidence

File: `backend/app/review/service.py` → `_persist_validated_findings()`

For each `ValidatedFinding`:

```python
# Look up previous run for lifecycle tracking
prev_run = db.query(ReviewRun).filter(
    ReviewRun.pull_request_id == run.pull_request_id,
    ReviewRun.status == "completed",
    ReviewRun.id < run.id,
).order_by(ReviewRun.id.desc()).first()

# Persist Finding
finding_row = Finding(
    review_run_id=run.id,
    type=vf.finding.category,
    severity=vf.finding.severity,
    file=vf.finding.file,
    line=vf.finding.line,
    title=vf.finding.title,
    explanation=vf.finding.problem,
    rule_source=vf.finding.evidence,
    recommendation=vf.finding.recommendation,
    confidence=vf.adjusted_confidence,
    evidence_status=vf.evidence_status,
    lifecycle_status=determine_lifecycle_status(vf.finding, prev_run, db),
)
db.add(finding_row)
db.flush()

# Persist FindingEvidence rows
for ev in vf.supporting_evidence + vf.contradicting_evidence:
    db.add(FindingEvidence(
        finding_id=finding_row.id,
        evidence_status="supported" if ev in vf.supporting_evidence else "contradicted",
        source_type=ev.get("type", "unknown"),
        source_path=ev.get("path"),
        source_text=ev.get("text", "")[:2000],  # Truncated
        citation_metadata=ev,
    ))
```

---

## Lifecycle Status Determination

```python
def determine_lifecycle_status(finding, prev_run, db):
    if not prev_run:
        return "new"
    
    prev_findings = db.query(Finding).filter_by(review_run_id=prev_run.id).all()
    
    for pf in prev_findings:
        same_file = pf.file == finding.file
        same_type = pf.type == finding.category
        close_line = abs((pf.line or 0) - (finding.line or 0)) <= 3
        
        if same_file and same_type and close_line:
            return "persistent"
    
    return "new"
```

Findings from the previous completed run that no longer appear in the current run are marked `"resolved"` (done during `_persist_validated_findings()` with a separate upsert pass).

---

## Key Files

| File | Location | Role |
|---|---|---|
| `evidence.py` | `backend/app/review/evidence.py` | `validate_findings()`, `ValidatedFinding`, all evidence checks |
| `service.py` | `backend/app/review/service.py` | `_persist_validated_findings()` |
| `models.py` | `backend/app/review/models.py` | `FindingEvidence` SQLAlchemy model |
