# 10 — Feature Flow: Human Review Approval Gate

## Feature Summary
RepoMind never auto-merges. After a review run completes, a human reviewer (role: `reviewer`, `tech_lead`, or `org_admin`) can approve, reject, or request changes. Their decision is persisted as a `HumanDecision` record and is visible in the review UI. This is an audit trail, not a GitHub merge action.

---

## End-to-End Flow

### 1. View Completed Review

| Step | Where | What Happens |
|---|---|---|
| User navigates to PR | `ReviewPage.jsx` | Route: `/repositories/:rid/pull-requests/:prid` |
| Poll review run | `reviewApi.getReviewRun(runId)` | `GET /review-runs/{runId}` |
| Display findings | `ReviewPage.jsx` | Renders `Finding` cards with severity/evidence status |
| Display risk | `ReviewPage.jsx` | Shows risk score + level + factors |
| Display conflicts | `ReviewPage.jsx` | Shows conflict cards |

---

### 2. Trigger Approve/Reject

| Step | Where | What Happens |
|---|---|---|
| User clicks "Approve" or "Request Changes" | `ReviewPage.jsx` | `reviewApi.approveReviewRun(runId, {action: "approve", note: "..."})` |
| API call | `lib/api.js:63` | `POST /review-runs/{runId}/approve` with `{action, note}` |
| Route | `backend/app/review/router.py` → `approve_review_run()` | |

---

### 3. Authorization Check

File: `backend/app/review/router.py` → `approve_review_run()`

```python
# Role-based auth (checked directly on User.role, not via permissions framework)
if current_user.role not in ("reviewer", "team_lead", "org_admin"):
    raise HTTPException(status_code=403, detail="Not authorized to approve reviews")

# Review must be completed
if run.status != "completed":
    raise HTTPException(status_code=400, detail="Cannot approve a review run that is not completed")

# Org membership verification
verify_org_member(db, current_user.id, org_id)
```

Note: This check uses `current_user.role` directly (the user's global role string) rather than the org-scoped permissions framework. This is a design inconsistency noted from the source code.

---

### 4. Persist Decision (Upsert)

```python
# Check for existing decision by this user on this run
existing = db.query(HumanDecision).filter_by(
    review_run_id=review_run_id,
    user_id=current_user.id
).first()

if existing:
    # Update existing decision (user can change their mind)
    existing.action = decision.action
    existing.note = decision.note
    existing.created_at = datetime.now(timezone.utc)
else:
    human_decision = HumanDecision(
        review_run_id=review_run_id,
        user_id=current_user.id,
        action=decision.action,        # "approve" | "request_changes" | "dismiss" | "resolve_finding"
        note=decision.note,
        created_at=datetime.now(timezone.utc)
    )
    db.add(human_decision)

db.commit()
db.refresh(human_decision)
```

---

## HumanDecision Model

File: `backend/app/review/models.py` → `HumanDecision`

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` | Which review run |
| `user_id` | FK → `user.id` (SET NULL) | Which user made the decision |
| `action` | String(50) | `approve` / `request_changes` / `dismiss` / `resolve_finding` |
| `target_type` | String(50) nullable | `finding` / `conflict` / `review` (for fine-grained decisions) |
| `target_id` | Integer nullable | ID of specific finding/conflict (for fine-grained decisions) |
| `note` | Text nullable | Human-provided justification |
| `created_at` | DateTime(tz) | Timestamp of decision |

The `review_run → human_decisions` relationship is a one-to-many (one run can have decisions from multiple reviewers).

---

## Request/Response Schemas

File: `backend/app/review/schemas.py`

```python
class HumanDecisionRequest(BaseModel):
    action: str   # "approve" | "request_changes" | "dismiss" | "resolve_finding"
    note: Optional[str] = None

class HumanDecisionResponse(BaseModel):
    id: int
    review_run_id: int
    user_id: Optional[int]
    action: str
    note: Optional[str]
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

---

## What the Decision Does (and Doesn't Do)

| Does | Doesn't |
|---|---|
| Creates an immutable audit record (upsert per user) | Auto-merge the PR on GitHub |
| Visible to all org members viewing the review | Change review_run.status |
| Linked to the reviewer's user_id | Trigger any automated actions |
| Allows note/justification text | Grant GitHub merge permissions |

RepoMind explicitly never auto-merges. The `HumanDecision` is purely a record in the RepoMind system.

---

## Permissions Required

| Action | Required Role |
|---|---|
| View review run | Any authenticated org member |
| Approve/Request Changes | `reviewer`, `team_lead`, `org_admin` |
| Dismiss findings | `reviewer`, `team_lead`, `org_admin` |
| Resolve findings | `reviewer`, `team_lead`, `org_admin` |

Front-end gate: `ReviewPage.jsx` shows the approve button only to users with `can(Permissions.PRS_APPROVE)`.

---

## Key Files

| File | Location | Role |
|---|---|---|
| `router.py` | `backend/app/review/router.py:129-181` | `POST /review-runs/{id}/approve` endpoint |
| `models.py` | `backend/app/review/models.py:256-289` | `HumanDecision` SQLAlchemy model |
| `schemas.py` | `backend/app/review/schemas.py` | `HumanDecisionRequest`, `HumanDecisionResponse` |
| `api.js` | `frontend/src/lib/api.js:63-67` | `reviewApi.approveReviewRun()` |
| `ReviewPage.jsx` | `frontend/src/pages/ReviewPage.jsx` | Decision UI + polling |
