# RepoMind — Human Approval, GitHub Review & Merge Lifecycle Deep Analysis

**Status:** Investigation Only — No Implementation Changes  
**Date:** 2026-09-22  
**Scope:** Architecture + Code-Flow + Product-Behavior Investigation

---

## 1. Executive Summary

RepoMind is designed as an **internal human approval gate** — an advisory system that produces AI code review findings, risk assessments, and conflict analysis. Humans review these findings inside the RepoMind UI and record their approval or rejection. **RepoMind explicitly never auto-merges.** The merge decision always belongs to a human acting directly on GitHub.

### Critical Finding

The documentation and code are consistent on one point: **RepoMind is not a GitHub review synchronization system, and it is not a merge automation system.** It is an internal advisory and audit tool. However, the project has evolved beyond its original scope (manual-only, no webhooks) by adding webhook infrastructure. This creates an architectural gap: webhook events arrive from GitHub, but only `pull_request` events are processed. **GitHub review events (`pull_request_review`) and merge events (`pull_request.closed+merged`) are received but explicitly skipped.** No bi-directional synchronization exists.

### The Three Operations Are Distinct

```
RepoMind HumanDecision  ≠  GitHub PR Review  ≠  GitHub PR Merge
```

| Operation | Currently Implemented | Direction |
|---|---|---|
| RepoMind HumanDecision | ✅ Yes — internal DB record | RepoMind → DB only |
| GitHub PR Review | ❌ No — not read or written | Neither direction |
| GitHub PR Merge | ❌ No — not read or written | Neither direction |

---

## 2. Current HumanDecision Implementation

### Model Definition

File: `backend/app/review/models.py:256-289`

```python
class HumanDecision(Base):
    """
    Records human review decisions on a ReviewRun.
    This is the human approval gate — RepoMind never auto-merges.
    """
    __tablename__ = "human_decision"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    review_run_id = Column(Integer, ForeignKey("review_run.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(50), nullable=False)          # approve | request_changes | dismiss | resolve_finding
    target_type = Column(String(50), nullable=True)      # finding | conflict | review
    target_id = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), ...)

    review_run = relationship("ReviewRun", back_populates="human_decisions")
```

### Key Observations

| Aspect | Value |
|---|---|
| Primary Key | `id` (auto-increment integer) |
| Foreign Keys | `review_run_id` → `review_run.id` (CASCADE), `user_id` → `user.id` (SET NULL) |
| Action Values (model) | `approve`, `request_changes`, `dismiss`, `resolve_finding` |
| Action Values (schema validation) | Only `approve` or `reject` accepted via API |
| Reviewer relationship | Via `user_id` FK — no `github_username` field |
| ReviewRun relationship | One-to-many (one run → many decisions) |
| No unique constraint | Multiple decisions per user per run possible (but upsert logic in router prevents this) |
| No `head_sha` field | Decision is tied to ReviewRun, not directly to a commit |
| No `source` field | Cannot distinguish "from RepoMind UI" vs "from GitHub webhook" |

### What HumanDecision Represents

Based on code + documentation analysis:

**Answer: (A) — Human accepts/rejects RepoMind's AI review findings.**

Evidence:
- `project-overview.md:18`: _"Automated Merging: A human always decides whether a PR merges. RepoMind is an advisory gate only."_
- `project-overview.md:27`: _"Reviewer — reviews findings, accepts/rejects/ignores them, still makes the actual merge decision on GitHub."_
- `feature_flow_human_approval.md:4`: _"This is an audit trail, not a GitHub merge action."_
- `models.py:259`: _"This is the human approval gate — RepoMind never auto-merges."_

**IMPORTANT:** However, the frontend `ApprovalModal` uses language that blurs this boundary:
- _"Confirm AI risk findings reviewed and PR is safe to merge."_
- _"This will mark the PR as approved for merge."_
- _"This will request changes and block merging."_

These UI strings imply merge authorization, but the backend does **nothing** with GitHub. This is a product-level inconsistency, not a code bug.

---

## 3. Current ReviewRun Implementation

### Model Definition

File: `backend/app/review/models.py:29-85`

```python
class ReviewRun(Base):
    __tablename__ = "review_run"

    id = Column(Integer, primary_key=True)
    pull_request_id = Column(Integer, ForeignKey("pull_request.id", ondelete="CASCADE"), nullable=False, index=True)
    commit_sha = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="pending")  # pending | running | completed | failed | cancelled
    repomind_version = Column(String(50), nullable=True)
    prompt_version = Column(String(50), nullable=True)
    llm_model = Column(String(255), nullable=True)
    rag_enabled = Column(Boolean, nullable=False, default=True)
    intelligence_mode = Column(String(20), nullable=True, default="v1")
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    progress_message = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)

    findings = relationship("Finding", ...)
    linter_results = relationship("LinterResult", ...)
    risk_assessment = relationship("RiskAssessment", uselist=False, ...)
    conflicts = relationship("Conflict", ...)
    human_decisions = relationship("HumanDecision", ...)
```

### Lifecycle

```
pending → running → completed
                  → failed
(cancelled reserved for async-job orchestration)
```

### Key Observations

| Question | Answer |
|---|---|
| Multiple ReviewRuns per PR? | **Yes** — no unique constraint on `pull_request_id` |
| How is latest run determined? | By `id DESC` ordering (see `router.py:74-77`) |
| How is active run determined? | By `status IN ('pending', 'running')` (see `webhooks/routes.py:121-128`) |
| `commit_sha` behavior | Set at creation time from `PullRequest.head_sha` or fetched from GitHub |
| Idempotency | Same `commit_sha` on same PR → returns existing run (see `router.py:74-84`) |
| Webhook idempotency | Checks for `pending`/`running` status, not `commit_sha` (see `webhooks/routes.py:120-135`) |

### Which ReviewRun receives a HumanDecision?

The frontend determines this: `ReviewPage.jsx` sends the decision to `activeRunId`, which is the run ID returned by `triggerReview()` or the most recent run. The backend endpoint (`/review-runs/{review_run_id}/approve`) accepts an explicit `review_run_id` — there is **no automatic "find the latest ReviewRun" logic** in the approval endpoint.

---

## 4. Current PullRequest Implementation

### Model Definition

File: `backend/app/github/models.py:13-45`

```python
class PullRequest(Base):
    __tablename__ = "pull_request"
    __table_args__ = (
        UniqueConstraint("repository_id", "github_number", name="uq_pull_request_repo_number"),
    )

    id = Column(Integer, primary_key=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    github_number = Column(Integer, nullable=False)
    title = Column(String(512), nullable=False)
    author = Column(String(255), nullable=True)
    state = Column(String(50), nullable=False, default="open")
    created_at = Column(DateTime(timezone=True), nullable=False)
    merged_at = Column(DateTime(timezone=True), nullable=True)
    additions = Column(Integer, nullable=True)
    deletions = Column(Integer, nullable=True)
    files_changed = Column(Integer, nullable=True)
    head_sha = Column(String(255), nullable=True)
```

### PR Identification Chain

```
GitHub webhook payload
    ↓  repository.owner.login + repository.name
Repository (github_owner + github_name)
    ↓  repository.id
PullRequest (repository_id + github_number)  ← UniqueConstraint
    ↓  pull_request.id
ReviewRun (pull_request_id)
```

**`repository_id + github_number` is sufficient to uniquely identify a GitHub PR** — enforced by the `uq_pull_request_repo_number` unique constraint.

### Key Observations

| Field | Present? | Notes |
|---|---|---|
| `repository_id` | ✅ | FK to `repository.id` |
| `github_number` | ✅ | GitHub PR number |
| `head_sha` | ✅ | Updated on sync, used for re-analysis |
| `base_sha` | ❌ | Not tracked |
| `state` | ✅ | `open`/`closed` — updated during sync |
| `merged_at` | ✅ | Set if PR was merged (from GitHub API) |
| `github_url` | ❌ | Not tracked (but constructible from owner/name/number) |
| `closed_at` | ❌ | Not tracked separately |

---

## 5. Current RepoMind Approval Flow

### Complete Trace: Browser → Database

```
ReviewPage.jsx (Approve PR button)
    ↓ onClick → setApprovalModal({isOpen: true, action: 'approve'})
ApprovalModal (user types optional note, clicks "Approve PR")
    ↓ onSubmit({action: 'approve', note: '...'})
useMutation → reviewApi.approveReviewRun(activeRunId, decision)
    ↓ POST /review-runs/{runId}/approve
        body: {"action": "approve", "note": "..."}
FastAPI router → approve_review_run()
    ↓ 1. Role check: current_user.role in ("reviewer", "team_lead", "org_admin")
    ↓ 2. ReviewRun must be status="completed"
    ↓ 3. Org membership verified via verify_org_member()
    ↓ 4. Upsert HumanDecision (one per user per run)
    ↓ 5. db.commit()
Response → HumanDecisionResponse
    ↓
queryClient.invalidateQueries(['reviewRun', activeRunId])
    ↓
UI refreshes → shows "Approved" badge
```

### Exact Code Path

| Layer | File | Location |
|---|---|---|
| Button | `ReviewPage.jsx:313-321` | `<Button variant="success-solid">Approve PR</Button>` |
| Modal | `ReviewPage.jsx:92-156` | `ApprovalModal` component |
| Mutation | `ReviewPage.jsx:208-217` | `useMutation` calling `reviewApi.approveReviewRun` |
| API client | `api.js:63-67` | `POST /review-runs/${runId}/approve` |
| Endpoint | `review/router.py:129-181` | `approve_review_run()` |
| Schema | `review/schemas.py:150-160` | `HumanDecisionRequest` validates `action ∈ {approve, reject}` |
| Permission (frontend) | `ReviewPage.jsx:169` | `can(Permissions.PRS_APPROVE)` |
| Permission (backend) | `review/router.py:138` | `current_user.role not in ("reviewer", "team_lead", "org_admin")` |

### What Happens Today When "Approve" Is Clicked

1. A `HumanDecision` row is created/updated in the database with `action="approve"`.
2. The decision is returned to the frontend and displayed as an "Approved" badge.
3. **Nothing happens on GitHub.** No review is submitted, no approval is posted, no merge is triggered.
4. The `ReviewRun.status` does **not** change (remains `completed`).

---

## 6. Current Reject / Request-Changes Flow

### Exact Flow

The "Request Changes" button follows the identical path as approval, but with `action: 'reject'`.

| Aspect | Value |
|---|---|
| Frontend action value | `'reject'` (set in `ReviewPage.jsx:309`) |
| Schema-validated values | `approve` or `reject` only (see `schemas.py:158`) |
| Model action values | `approve`, `request_changes`, `dismiss`, `resolve_finding` |
| DB state after reject | `HumanDecision.action = "reject"` |
| ReviewRun state | **Unchanged** (stays `completed`) |
| Frontend display | Shows "Changes Requested" badge (maps `reject` → UI label) |
| Reasoning stored? | Yes — optional `note` field |
| Anything sent to GitHub? | **No** |

**Schema/Model mismatch:** The `HumanDecisionRequest` schema validates `action ∈ {approve, reject}`, but the `HumanDecision` model documents `action ∈ {approve, request_changes, dismiss, resolve_finding}`. The API only accepts `approve` or `reject`, making `request_changes`, `dismiss`, and `resolve_finding` unreachable via the approval endpoint.

**Does RepoMind rejection currently create a GitHub "Request changes" review?**

```
NOT IMPLEMENTED
```

---

## 7. Current GitHub Webhooks

### File: `backend/app/webhooks/routes.py`

### Complete Event Matrix

| Event Type | Action | Handled? | Effect |
|---|---|---|---|
| `ping` | — | ✅ Stored + pong | Returns `{"status": "pong"}` |
| `pull_request` | `opened` | ✅ Triggers review | Creates `ReviewRun(status="pending")` |
| `pull_request` | `synchronize` | ✅ Triggers review | Creates `ReviewRun(status="pending")` |
| `pull_request` | `reopened` | ✅ Triggers review | Creates `ReviewRun(status="pending")` |
| `pull_request` | `closed` | ❌ Stored, skipped | No DB effect beyond WebhookEvent |
| `pull_request` | `labeled` | ❌ Stored, skipped | No DB effect beyond WebhookEvent |
| `pull_request` | any other | ❌ Stored, skipped | No DB effect beyond WebhookEvent |
| `pull_request_review` | any | ❌ Stored, skipped | **Not handled at all** |
| `pull_request_review_comment` | any | ❌ Stored, skipped | Not handled |
| `issue_comment` | any | ❌ Stored, skipped | Not handled |

### Key Findings

- **Only `pull_request` events with `opened`/`synchronize`/`reopened` actions trigger any processing.**
- `pull_request_review` events are **not parsed, not matched, and fall through to the "all other events — stored but skipped" catch-all** at line 279-282.
- There is no `pull_request.closed` handler — merged PRs are not detected via webhooks.
- The `PullRequest.state` and `PullRequest.merged_at` fields are only updated during explicit PR sync (`sync_pull_requests()`), not via webhooks.

---

## 8. GitHub Review Event Analysis

### Current Behavior

**`pull_request_review` is NOT handled.** If GitHub sends a `pull_request_review` event (any action: `submitted`, `edited`, `dismissed`), the webhook handler:

1. Verifies the HMAC signature.
2. Stores the event as a `WebhookEvent` with `status="skipped"`.
3. Returns `{"status": "skipped", "event_type": "pull_request_review"}`.

| GitHub Event | Current RepoMind Behavior | DB Effect | ReviewRun Effect | UI Effect |
|---|---|---|---|---|
| Review approved | Stored as `WebhookEvent(status="skipped")` | WebhookEvent row only | None | None |
| Changes requested | Stored as `WebhookEvent(status="skipped")` | WebhookEvent row only | None | None |
| Commented | Stored as `WebhookEvent(status="skipped")` | WebhookEvent row only | None | None |

---

## 9. Should GitHub Approval Create HumanDecision?

### Analysis

The proposed mapping:
```
GitHub review approved → HumanDecision(action="approve") → ReviewRun
```

is **architecturally problematic** for the following reasons:

| Issue | Analysis |
|---|---|
| **Reviewer identity** | GitHub reviewer is identified by `review.user.login` (GitHub username). RepoMind users are identified by `user.email`. There is **no `github_username` column** on the `User` model. Mapping is impossible without schema changes. |
| **Unknown reviewer** | A GitHub reviewer may not be a RepoMind user at all. The `HumanDecision.user_id` would be NULL, breaking the audit trail. |
| **Cross-organization** | A GitHub reviewer might belong to a different RepoMind organization (or none). RBAC cannot be enforced. |
| **Permission mismatch** | GitHub allows anyone with repo access to review. RepoMind restricts approval to `reviewer`, `team_lead`, `org_admin`. A GitHub `developer`-role user's approval should not bypass RepoMind RBAC. |
| **Which ReviewRun?** | GitHub approval is for the PR, not for a specific ReviewRun. If multiple ReviewRuns exist, which one receives the decision? |
| **Stale approval** | GitHub approval may be for a different commit than the current ReviewRun's `commit_sha`. |

### Security Implications

- **Privilege escalation:** A user without RepoMind `reviewer` role could approve by reviewing on GitHub, bypassing RBAC.
- **Audit gap:** `user_id = NULL` decisions break the audit trail.
- **Cross-tenant risk:** A GitHub user from another organization could trigger a decision in the wrong RepoMind org.

### Conclusion

`PRODUCT DECISION REQUIRED` — GitHub approval → HumanDecision mapping requires explicit design for identity mapping, RBAC enforcement, and ReviewRun targeting.

---

## 10. What Does "Approve" Mean?

### Source Analysis

| Source | Statement | Implied Meaning |
|---|---|---|
| `project-overview.md:6` | _"Human Approval Gate"_ | Advisory gate, not merge gate |
| `project-overview.md:18` | _"A human always decides whether a PR merges. RepoMind is an advisory gate only."_ | **(A)** — accept AI findings |
| `project-overview.md:27` | _"Reviewer — reviews findings, accepts/rejects/ignores them, still makes the actual merge decision on GitHub."_ | **(A)** — accept AI findings |
| `requirements.md:30` | _"Human Approval Gate: A human always decides whether a PR merges."_ | **(A)** |
| `feature_flow_human_approval.md:4` | _"This is an audit trail, not a GitHub merge action."_ | **(A)** |
| `models.py:259` | _"This is the human approval gate — RepoMind never auto-merges."_ | **(A)** |
| Frontend `ApprovalModal` | _"Confirm AI risk findings reviewed and PR is safe to merge"_ | Ambiguous — implies **(B)** |
| Frontend `ApprovalModal` | _"This will mark the PR as approved for merge"_ | Implies **(B)** or **(E)** |

### Determination

**The current intended meaning is (A): Human accepts RepoMind's AI review.**

The backend and documentation are consistent. The frontend UI language is misleading but does not reflect actual behavior. The UI says "approved for merge" but the system does nothing with GitHub.

**WARNING:** The frontend ApprovalModal copy should be corrected to match the actual system behavior. Current wording implies merge authorization that does not exist.

---

## 11. Auto-Merge Investigation

### Search Results

**There is NO merge implementation anywhere in the codebase.**

| Search Term | Results |
|---|---|
| `merge_pull_request` | Not found |
| `mergePullRequest` | Not found |
| `PUT /pulls/` | Not found |
| `auto_merge` | Not found |
| `enable_auto_merge` | Not found |
| `merge_method` | Not found |
| `squash` | Not found |
| `rebase` | Not found |

The `GitHubClient` class (`client.py`) has **only `_get` method** — no `_post`, `_put`, `_patch`, or `_delete`. It is a **read-only** client by design.

### GitHub Capability Matrix

| Capability | Implemented? | Method |
|---|---|---|
| **Read** repository metadata | ✅ | `validate_repository_access()` |
| **Read** PR list | ✅ | `list_pull_requests()` |
| **Read** PR detail | ✅ | `get_pull_request()` |
| **Read** PR diff | ✅ | `get_pull_request_diff()` |
| **Read** PR files | ✅ | `get_pull_request_files()` |
| **Read** PR commits | ✅ | `list_pull_request_commits()` |
| **Read** repository contents | ✅ | `get_repository_contents()` |
| **Read** repository tree | ✅ | `get_repository_tree()` |
| **Read** blob content | ✅ | `get_blob_content()` |
| **Write** PR review | ❌ | Not implemented |
| **Write** PR comment | ❌ | Not implemented |
| **Write** merge PR | ❌ | Not implemented |
| **Write** any mutation | ❌ | No HTTP POST/PUT/PATCH/DELETE methods exist |

---

## 12. GitHub Token/PAT Permissions

### Token Configuration

File: `github/service.py` + `github/encryption.py`

| Aspect | Value |
|---|---|
| Token type | Personal Access Token (classic or fine-grained) |
| Storage | Encrypted at rest via Fernet in `github_connection.encrypted_token` |
| Scope (per config) | `"repo"` — stored in `GithubConnection.scope` |
| Decryption | On-demand, in-memory only, never logged |
| One token per | Organization (not per user, not per repository) |

### Documented Permissions

From `security.md:19-20`:

> _"The GitHub connection uses a **read-only** Personal Access Token, scoped to the specific repositories being analyzed — never organization-wide admin access."_
> 
> _"RepoMind never requests or uses commit/write access — it should never modify code (a 'never' constraint, not merely unbuilt)."_

### Permissions Analysis

| Access Type | Required for Current Code | Required for GitHub Review Write | Required for Merge |
|---|---|---|---|
| `repo` (read) | ✅ | — | — |
| `repo` (write) | ❌ | ✅ | ✅ |
| `pull_request:write` | ❌ | ✅ | ✅ |
| Admin | ❌ | ❌ | ❌ |

**CAUTION:** The current PAT is explicitly documented as read-only. Implementing GitHub review writes or merges would require changing the PAT scope, updating the security documentation, user consent for the expanded permissions, and security review.

---

## 13. Scope Analysis

### Classification

| Feature | Status | Evidence |
|---|---|---|
| GitHub PR comments | `OUT OF SCOPE` | `scope.md:36`: _"Inline PR review comments posted back to GitHub"_ listed under Out of Scope |
| GitHub review submission | `OUT OF SCOPE` | No write methods in GitHubClient; security.md prohibits writes |
| GitHub approval | `OUT OF SCOPE` | Implied by read-only PAT mandate and anti-goal #2 |
| GitHub request changes | `OUT OF SCOPE` | Same as above |
| GitHub merge | `EXPLICITLY EXCLUDED` | `project-overview.md:18`: Anti-Goal #2 — "Automated Merging" |
| GitHub auto-merge | `EXPLICITLY EXCLUDED` | Same as above |
| Webhook reception | `PARTIALLY IMPLEMENTED` | Webhook handler exists but was `OUT OF SCOPE` per `scope.md:35` — now implemented beyond original scope |
| Webhook synchronization | `PARTIALLY IMPLEMENTED` | Only `pull_request` events processed; reviews/merge ignored |

**IMPORTANT:** Documentation/Implementation conflict: `scope.md:35` lists _"GitHub App, OAuth install flow, and webhooks (automatic triggering)"_ as **Out of Scope**. However, webhook infrastructure has been implemented. The scope document has not been updated to reflect this evolution.

---

## 14. PR Merge/Close Lifecycle

### What happens when GitHub sends `pull_request.action=closed, merged=true`?

**Currently: NOTHING.**

The webhook handler receives the event, stores it as `WebhookEvent(status="skipped")`, and returns `{"status": "skipped"}`. No state updates occur.

### What happens when GitHub sends `pull_request.action=closed, merged=false`?

**Same: NOTHING.** Stored and skipped.

### State Updates That *Should* Happen (but don't)

| State | Current Behavior | Missing Behavior |
|---|---|---|
| `PullRequest.state` | Unchanged (stays `open` until next sync) | Should update to `closed` |
| `PullRequest.merged_at` | Unchanged | Should be set from payload |
| `ReviewRun.status` | Unchanged | Could be updated to reflect PR is now closed |
| `HumanDecision` | Unchanged | No action needed |
| UI state | Shows stale `open` status | Should reflect `closed`/`merged` |

### When Do These Fields Get Updated?

Only during explicit PR sync (`sync_pull_requests()`) — triggered manually from the UI or lazily on first PR list view. **There is no webhook-driven state synchronization for PR status.**

---

## 15. Human Approval vs GitHub Merge — State Model

### Current Model (as implemented)

```
AI Review → Risk Analysis → Human Review (in RepoMind) → Internal Record → DONE
                                                          ↑
                                                          └─ No connection to GitHub
```

The merge happens entirely outside RepoMind:

```
Developer opens GitHub PR page → clicks "Merge" → GitHub merges → RepoMind is unaware
```

### Current Conceptual Flow

```
AI Review
    ↓
Risk Analysis + Conflict Detection
    ↓
Human reviews findings in RepoMind UI
    ↓
Human records "Approve" or "Reject" in RepoMind
    ↓
HumanDecision stored in DB (audit trail)
    ↓
Human separately goes to GitHub
    ↓
Human merges PR on GitHub (completely independent)
    ↓
RepoMind remains unaware until next PR sync
```

---

## 16. Security Analysis

### Case 1: RepoMind Approval Only Changes Internal State (CURRENT)

| Aspect | Analysis |
|---|---|
| Required permissions | Read-only PAT ✅ |
| Abuse scenario | Low risk — approval is advisory only |
| Authorization | RepoMind RBAC enforced (`reviewer`+) |
| Auditability | Full audit trail via `HumanDecision` |
| Credential requirement | No additional credentials needed |
| Risk of accidental merge | **Zero** — no merge capability exists |
| Reviewer identity | RepoMind `user_id` — fully controlled |
| Organization boundaries | Enforced via `verify_org_member()` |

### Case 2: RepoMind Approval Submits GitHub Approval (NOT IMPLEMENTED)

| Aspect | Analysis |
|---|---|
| Required permissions | Read-write PAT or GitHub App with `pull_request:write` |
| Abuse scenario | **High** — a RepoMind reviewer could submit GitHub approvals; if branch protection requires only 1 approval, this enables unilateral merge |
| Authorization | Must enforce both RepoMind RBAC AND GitHub permissions |
| Auditability | GitHub audit log shows RepoMind bot as reviewer, not the human |
| Credential requirement | Write-capable PAT (violates current security doc) |
| Risk of accidental merge | **Medium** — if auto-merge is enabled on GitHub, RepoMind approval could trigger automatic merge |
| Reviewer identity | **Problem** — GitHub sees the PAT owner, not the actual human reviewer |
| Organization boundaries | Must verify the PAT's repo access matches the RepoMind org |

### Case 3: RepoMind Approval Merges GitHub PR (NOT IMPLEMENTED, EXPLICITLY EXCLUDED)

| Aspect | Analysis |
|---|---|
| Required permissions | Write PAT + merge permissions |
| Abuse scenario | **Critical** — any authorized RepoMind user could merge any PR |
| Authorization | Requires strictest RBAC + additional confirmation |
| Auditability | GitHub shows RepoMind bot as merger, not the human |
| Credential requirement | Write-capable PAT with merge permissions |
| Risk of accidental merge | **Very High** |
| Reviewer identity | Lost — RepoMind acts as proxy |
| Organization boundaries | Critical — cross-org merge would be catastrophic |

---

## 17. Webhook Security Analysis

### Current Protections

| Protection | Status | Implementation |
|---|---|---|
| HMAC-SHA256 signature verification | ✅ | `_verify_github_signature()` with `hmac.compare_digest()` |
| Secret management | ✅ | `GITHUB_WEBHOOK_SECRET` via environment variable |
| Timing attack prevention | ✅ | Constant-time comparison |
| Replay protection | ✅ | `github_delivery_id` unique constraint |
| Duplicate event handling | ✅ | Check before processing |
| Event persistence before processing | ✅ | `db.flush()` before action |
| Repository ownership verification | ✅ | `_resolve_repository()` matches known repos |
| Unknown repository handling | ✅ | Stored as `skipped` |
| Unknown PR handling | ✅ | `_enqueue_review()` returns None |

### Missing Protections

| Protection | Status | Risk |
|---|---|---|
| Event ordering | ❌ Not enforced | Events may be processed out of order |
| Timestamp validation | ❌ Not checked | Old events accepted if signature valid |
| Organization ownership validation | ❌ Not checked | Only repo name is matched, not org boundary |
| Unknown reviewer handling | N/A | Reviews not processed |

### Can Same Webhook Create Duplicate HumanDecisions?

**No** — webhooks do not create `HumanDecision` records at all. They only create `ReviewRun` records, and those have idempotency checks (pending/running status check).

---

## 18. Race Condition Analysis

### Scenario A: AI Review Running + Human Approves on GitHub

| Current | Correct |
|---|---|
| GitHub `pull_request_review` event is stored and skipped | No RepoMind state change |
| ReviewRun continues running | ReviewRun should continue (GitHub approval is irrelevant to AI processing) |

**Current behavior is correct by accident** — the event is ignored, which happens to be the right behavior.

### Scenario B: RepoMind Human Approves → GitHub Requests Changes 5s Later

| Current | Issue |
|---|---|
| RepoMind approval: `HumanDecision(action="approve")` stored | No conflict detection |
| GitHub event: stored and skipped | RepoMind is unaware of GitHub's request for changes |

**Stale approval in RepoMind.** The RepoMind UI continues showing "Approved" while GitHub shows "Changes Requested". `PRODUCT DECISION REQUIRED` — should RepoMind automatically invalidate its approval?

### Scenario C: Two GitHub Approvals Arrive

**Current: Both stored as `WebhookEvent(status="skipped")`.** No issue since reviews aren't processed.

### Scenario D: Approval Arrives for Old ReviewRun

**Current: Not applicable** — GitHub approvals aren't mapped to ReviewRuns. If they were: `PRODUCT DECISION REQUIRED` — should old ReviewRun decisions be allowed?

### Scenario E: New Commit After Approval

**Current:**
1. `pull_request.synchronize` webhook → new `ReviewRun(status="pending")` created.
2. Old `ReviewRun`'s `HumanDecision` is preserved (not invalidated).
3. New ReviewRun has no decisions.
4. Frontend shows the new ReviewRun (via `triggerReview()` which returns or creates the latest).

**Old approval is effectively abandoned** — it still exists in the DB but the UI shows the new run. However, there is no explicit invalidation mechanism.

### Scenario F: PR Merged Before Approval Webhook Arrives

**Current: Not applicable** — merge events are not processed.

### Scenario G: Webhook After ReviewRun Is Completed

**For `pull_request.synchronize`:** A new `ReviewRun` is created (the completed one is not re-used). This is correct.

**For `pull_request_review`:** Event is skipped. If it were processed, the completed ReviewRun could receive a HumanDecision, which is architecturally valid (the endpoint already requires `status="completed"`).

---

## 19. Head SHA / Stale Approval Analysis

### Current Architecture

```
ReviewRun.commit_sha = PR.head_sha (at creation time)
HumanDecision → ReviewRun (via FK)
HumanDecision has NO direct head_sha field
```

### Scenario

```
PR HEAD = abc123
ReviewRun created with commit_sha = abc123
Human approves → HumanDecision linked to that ReviewRun
New commit pushed → PR HEAD = def456
Webhook: pull_request.synchronize → new ReviewRun with commit_sha = def456
```

### Current Behavior

The old approval is **implicitly stale** — it's linked to a ReviewRun with `commit_sha=abc123`, but the PR now has `head_sha=def456`. The new ReviewRun has no decisions.

### Should HumanDecision Be Tied to `head_sha`?

**No — the current design is correct.** `HumanDecision` is tied to `ReviewRun`, which already captures `commit_sha`. Adding `head_sha` to `HumanDecision` would be redundant. The important question is: **should the system prevent new ReviewRun creation from invalidating old decisions?**

Current answer: Old decisions are preserved but naturally superseded by the new ReviewRun. This is a reasonable design.

`PRODUCT DECISION REQUIRED`: Should old approvals be explicitly marked as `invalidated` when a new commit arrives?

---

## 20. Domain Model Analysis

### Currently Represented

| Concept | Model | Status Values |
|---|---|---|
| AI Review Status | `ReviewRun.status` | `pending`, `running`, `completed`, `failed`, `cancelled` |
| Human Decision Status | `HumanDecision.action` | `approve`, `reject` (via API); `approve`, `request_changes`, `dismiss`, `resolve_finding` (via model) |
| PR Status | `PullRequest.state` | `open`, `closed` (from GitHub sync) |
| PR Merge Status | `PullRequest.merged_at` | NULL or timestamp |

### NOT Represented

| Concept | Status |
|---|---|
| GitHub Review Status | ❌ No model — not tracked |
| GitHub Merge Status (via webhook) | ❌ Only updated during manual sync |
| Composite Review Verdict | ❌ No aggregate status combining AI + human decisions |
| Decision Validity | ❌ No stale/valid flag on HumanDecision |
| Decision Source | ❌ No field distinguishing RepoMind UI vs GitHub webhook origin |

### Minimal Additions (If Synchronization Were Desired)

```python
# Potential additions — NOT a recommendation to implement
class HumanDecision:
    source = Column(String(50))          # "repomind_ui" | "github_webhook"
    github_review_id = Column(Integer)   # GitHub review ID for dedup
    is_valid = Column(Boolean)           # Invalidated by new commits?

class PullRequest:
    github_review_state = Column(String(50))  # "approved" | "changes_requested" | None
```

---

## 21. State Machines

### Current System State Machine

```
ReviewRun States:
  [*] --> pending --> running --> completed
                             --> failed
  (cancelled reserved)

HumanDecision States:
  [*] --> no_decision --> approve (user clicks Approve)
                     --> reject (user clicks Request Changes)
  approve <--> reject (user can change decision)

PullRequest States:
  [*] --> open --> closed (updated during sync only)
  Note: merged_at set if merged

GitHub Review State: NOT TRACKED
```

### Proposed Target State Machine

```
ReviewRun States:
  [*] --> pending --> running --> completed
                             --> failed
  completed --> superseded (new commit arrives)

HumanDecision States:
  [*] --> no_decision --> approve --> stale (new commit pushes new ReviewRun)
                     --> reject --> stale (new commit pushes new ReviewRun)
  approve <--> reject

PullRequest States:
  [*] --> open --> closed (webhook or sync)
             --> merged (webhook or sync)
```

---

## 22. Architecture Diagrams

### CURRENT Architecture

```
GitHub ──────────────────────────────────────────────── RepoMind
  │                                                      │
  ├── PR webhook (opened/sync/reopen) ──→ Webhook Handler ──→ ReviewRun (pending)
  │                                         │
  ├── Review webhook (any) ──→ Webhook Handler ──→ SKIPPED (stored only)
  │                                         │
  └── Merge webhook (closed) ──→ Webhook Handler ──→ SKIPPED (stored only)

RepoMind UI ────────────────────────────────────────── RepoMind Backend
  │                                                      │
  └── Approve/Reject button ──→ POST /approve ──→ HumanDecision (DB record)
                                                         │
                                                    NO GITHUB WRITE
```

### TARGET Architecture (Minimal — Option A Enhanced)

```
GitHub ──────────────────────────────────────────────── RepoMind
  │                                                      │
  ├── PR webhook (opened/sync/reopen) ──→ Webhook Handler ──→ ReviewRun (pending)
  │                                         │
  ├── PR webhook (closed/merged) ──→ Webhook Handler ──→ PullRequest state update
  │                                         │
  ├── Review webhook (any) ──→ Webhook Handler ──→ PRODUCT DECISION REQUIRED
  │
RepoMind UI ────────────────────────────────────────── RepoMind Backend
  │                                                      │
  └── Approve/Reject button ──→ POST /approve ──→ HumanDecision (DB record)
                                                         │
                                                    NO GITHUB WRITE
```

---

## 23. Implementation Options

### OPTION A — Internal Approval Only (Current + Fixes)

```
RepoMind approval
→ HumanDecision (DB record)
→ No GitHub write
→ Human merges manually on GitHub
```

**Required changes:**

| Area | Change |
|---|---|
| Backend | Handle `pull_request.closed` webhook to update `PullRequest.state` and `merged_at` |
| Backend | Fix `HumanDecisionRequest` schema to accept `request_changes` (not just `reject`) |
| Backend | Use permissions framework instead of raw `current_user.role` check |
| Frontend | Fix ApprovalModal copy to say "approve AI findings" not "approve for merge" |
| GitHub permissions | No change — read-only PAT sufficient |
| DB changes | None required |
| Security | No new risks |
| Webhooks | Add `closed` action handling |
| Risks | Minimal — preserves current architecture |
| Scope compatibility | ✅ Fully compatible with documented scope |

### OPTION B — GitHub Review Synchronization

```
RepoMind approval → HumanDecision → GitHub approval/review
GitHub approval → webhook → HumanDecision (synced)
```

**Required changes:**

| Area | Change |
|---|---|
| Backend | Add `_post()` method to `GitHubClient` |
| Backend | Add `create_review()` method to `GitHubClient` |
| Backend | Handle `pull_request_review` webhook events |
| Backend | Add `github_username` field to `User` model for identity mapping |
| Backend | Add `source` and `github_review_id` fields to `HumanDecision` |
| Backend | Add review sync service |
| Frontend | No major changes (existing UI works) |
| GitHub permissions | **Write PAT required** — breaks security documentation |
| DB changes | User table migration, HumanDecision migration |
| Security | **Significant** — write access to repos, identity mapping challenges |
| Webhooks | Must handle `pull_request_review.submitted` |
| Risks | PAT identity problem (GitHub sees bot, not human), privilege escalation via GitHub |
| Scope compatibility | ❌ Violates current scope — _"Inline PR review comments posted back to GitHub"_ listed as Out of Scope |

### OPTION C — Full Merge Automation

```
RepoMind approval → GitHub approval → Auto-merge
```

**Required changes:**

| Area | Change |
|---|---|
| Backend | Everything from Option B + merge API |
| Backend | Add `merge_pull_request()` to `GitHubClient` |
| Backend | Add merge confirmation flow |
| Backend | Add merge strategy configuration |
| Frontend | Add merge button + strategy selector |
| GitHub permissions | Write PAT + merge permissions |
| DB changes | Everything from Option B + merge tracking |
| Security | **Critical** — automated merge requires strictest RBAC + confirmation |
| Risks | **Highest** — accidental merge, identity issues, cross-org risk |
| Scope compatibility | ❌ **EXPLICITLY EXCLUDED** — Anti-Goal #2: "Automated Merging" |

---

## 24. Minimal Recommendations Based on Existing Scope

### What should happen when RepoMind Approve is clicked?

**Current code:** Creates `HumanDecision(action="approve")` in DB. No GitHub effect.  
**Current spec:** Advisory approval — human accepts AI findings.  
**Recommendation:** Current behavior is correct. Fix UI copy to match.

### What should happen when RepoMind Reject is clicked?

**Current code:** Creates `HumanDecision(action="reject")` in DB. No GitHub effect.  
**Current spec:** Advisory rejection — human rejects/requests changes on AI findings.  
**Recommendation:** Current behavior is correct. Fix schema to accept `request_changes` as well.

### What should happen when GitHub Approve arrives?

**Current code:** `WebhookEvent(status="skipped")` — ignored.  
**Current spec:** `OUT OF SCOPE`.  
**Recommendation:** `PRODUCT DECISION REQUIRED` — synchronization is not in current scope. If desired, requires identity mapping infrastructure.

### What should happen when GitHub Request Changes arrives?

**Current code:** Ignored.  
**Current spec:** `OUT OF SCOPE`.  
**Recommendation:** `PRODUCT DECISION REQUIRED`.

### What should happen when GitHub Merge arrives?

**Current code:** Ignored.  
**Current spec:** Merge detection not explicitly addressed.  
**Recommendation:** Should update `PullRequest.state` and `merged_at` from webhook payload. This is a read-only state sync, not a merge action, and is compatible with current scope.

### What should happen when a new commit arrives after approval?

**Current code:** New `ReviewRun` created. Old `HumanDecision` preserved but superseded.  
**Current spec:** Re-analysis on new commits is in scope.  
**Recommendation:** Current behavior is correct. Optionally mark old decisions as `stale`.

---

## 25. Required Code Changes Summary

### Option A Changes (Recommended)

| Layer | File | Change |
|---|---|---|
| Webhook | `webhooks/routes.py` | Handle `pull_request.closed` to update PR state |
| Schema | `review/schemas.py` | Accept `request_changes` in addition to `reject` |
| Router | `review/router.py` | Use permissions framework, not raw role check |
| Frontend | `ReviewPage.jsx` | Fix ApprovalModal copy |

### Option B Changes (In Addition to A)

| Layer | File | Change |
|---|---|---|
| GitHub Client | `github/client.py` | Add `_post()`, `create_review()` |
| Models | `auth/models.py` | Add `github_username` to User |
| Models | `review/models.py` | Add `source`, `github_review_id` to HumanDecision |
| Webhook | `webhooks/routes.py` | Handle `pull_request_review` events |
| Service | New file | Review sync service |
| Migrations | Alembic | User + HumanDecision schema changes |
| Security | `security.md` | Document write access |
| Config | `.env` | Potentially separate write PAT |

### Option C Changes (In Addition to B)

| Layer | File | Change |
|---|---|---|
| GitHub Client | `github/client.py` | Add `merge_pull_request()` |
| Models | `review/models.py` | Add merge tracking fields |
| Frontend | `ReviewPage.jsx` | Add merge button + confirmation |
| Config | Settings | Merge strategy config |
| Security | Multiple | Comprehensive merge authorization |

---

## 26. Required DB Changes

### Option A: None required

### Option B:
- `user` table: add `github_username VARCHAR(255)` (nullable, indexed)
- `human_decision` table: add `source VARCHAR(50)`, `github_review_id INTEGER` (nullable)
- Alembic migration required

### Option C:
- Everything from Option B
- `pull_request` table: add `merge_status VARCHAR(50)`
- `review_run` or new table: merge tracking

---

## 27. Product Decisions Required

| # | Decision | Impact | Blocking? |
|---|---|---|---|
| 1 | Should GitHub review events create `HumanDecision` records? | Architecture + identity mapping | Yes — for Option B |
| 2 | Should RepoMind submit GitHub reviews when a user approves internally? | Security + PAT permissions | Yes — for Option B |
| 3 | Should old approvals be explicitly invalidated when new commits arrive? | UX + data model | No — enhancement |
| 4 | Should `pull_request.closed` webhooks update PR state? | Data freshness | No — clearly beneficial |
| 5 | Should the `scope.md` be updated to reflect webhook implementation? | Documentation accuracy | No — housekeeping |
| 6 | Should the frontend approval copy match the actual system behavior? | UX honesty | No — bug fix |
| 7 | Is merge automation ever intended for RepoMind? | Core product direction | Yes — fundamental |

---

## 28. Final Current-vs-Target Matrix

| Behavior | Current State | Target (Option A) | Target (Option B) | Target (Option C) |
|---|---|---|---|---|
| RepoMind Approve | Internal DB record | Same (fix UI copy) | + GitHub review | + GitHub review + merge |
| RepoMind Reject | Internal DB record | Same (fix schema) | + GitHub review | + GitHub review |
| GitHub Approve → RM | Ignored | Ignored | → HumanDecision | → HumanDecision |
| GitHub Request Changes → RM | Ignored | Ignored | → HumanDecision | → HumanDecision |
| GitHub Merge → RM | Ignored | PR state update | PR state update | PR state update |
| GitHub Close → RM | Ignored | PR state update | PR state update | PR state update |
| New Commit | New ReviewRun | Same + stale marking | Same + stale marking | Same + stale marking |
| PAT Scope | Read-only | Read-only | Read-write | Read-write + merge |
| Security Risk | Minimal | Minimal | Moderate | High |
| Scope Compatible | ✅ | ✅ | ❌ | ❌ (excluded) |

---

## MOST IMPORTANT QUESTION — Final Answer

> **Is RepoMind currently intended to be an internal human approval gate, a GitHub review synchronization system, a GitHub merge automation system, or some combination of these?**

### Determination

Based on all 10 sources:

| Source | Verdict |
|---|---|
| Product specification (`project-overview.md`) | **Internal approval gate** — "advisory gate only" |
| Scope documentation (`scope.md`) | **Internal only** — GitHub writes explicitly out of scope |
| HumanDecision model | **Internal record** — no GitHub fields |
| ReviewRun model | **Internal lifecycle** — no GitHub review linkage |
| PullRequest model | **Read-only sync** — no merge-triggering fields |
| Webhook implementation | **Partial read** — receives events, only processes PR triggers |
| GitHub client | **Read-only** — no write methods exist |
| Frontend approval flow | **Internal** — writes to RepoMind API only (but UI copy is misleading) |
| RBAC | **Internal** — no GitHub permission checking |
| Security documentation | **Explicit: never write to GitHub** |

### Answer

**RepoMind is currently intended to be an internal human approval gate.**

All 10 sources agree. The only inconsistency is the frontend `ApprovalModal` copy, which implies merge authorization that does not exist in the backend. This is a UI wording issue, not an architectural disagreement.

The webhook infrastructure represents a scope expansion beyond the original specification (which listed webhooks as Out of Scope), but even this expansion is strictly read-only: receive events, trigger internal review runs.

**No source conflicts were found on the fundamental question.** Every document, model, service, and UI component agrees: RepoMind advises, humans merge on GitHub. The system is an **internal human approval gate** with no GitHub write capabilities, no merge automation, and no bi-directional review synchronization.
