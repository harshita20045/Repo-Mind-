# 12 — Feature Flow: GitHub Webhook Automation

## Feature Summary
GitHub sends webhook events to RepoMind's `/webhooks/github` endpoint when PRs are opened, synchronized, or reopened. Every incoming request is verified via **HMAC-SHA256** using `GITHUB_WEBHOOK_SECRET`. Verified events are persisted and trigger automatic `ReviewRun` creation. Duplicate events (by `X-GitHub-Delivery`) are idempotently skipped.

---

## End-to-End Flow

### Step 1: GitHub Sends Webhook

GitHub delivers a POST request to `https://{your-domain}/webhooks/github` when:
- `pull_request.opened` — a new PR is created
- `pull_request.synchronize` — new commits pushed to an open PR
- `pull_request.reopened` — a previously closed PR is reopened
- `ping` — GitHub tests the webhook endpoint

Headers included by GitHub:
- `X-GitHub-Event: pull_request` (or `ping`)
- `X-Hub-Signature-256: sha256=<hex>` — HMAC-SHA256 of request body
- `X-GitHub-Delivery: <uuid>` — unique delivery ID for deduplication

---

### Step 2: Raw Body Read (Before JSON Parsing)

File: `backend/app/webhooks/routes.py` → `github_webhook()`

```python
raw_body = await request.body()
```

Critical: the raw body must be read BEFORE JSON parsing because HMAC is computed over the exact bytes GitHub sent, not over re-serialized JSON.

---

### Step 3: HMAC-SHA256 Signature Verification

```python
def _verify_github_signature(raw_body: bytes, signature: Optional[str]) -> bool:
    if not signature:
        return False
    
    secret = settings.GITHUB_WEBHOOK_SECRET
    if not secret:
        return False   # Webhook disabled if no secret configured
    
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected, signature)
```

`hmac.compare_digest()` is used to prevent timing attacks. If signature fails: HTTP 401 immediately.

---

### Step 4: Parse JSON Payload

```python
payload = json.loads(raw_body)
action = payload.get("action")       # e.g., "opened", "synchronize"
event_type = x_github_event          # e.g., "pull_request"
```

---

### Step 5: Deduplication by Delivery ID

```python
if x_github_delivery:
    existing_event = db.query(WebhookEvent).filter_by(
        github_delivery_id=x_github_delivery
    ).first()
    
    if existing_event:
        return {"status": "duplicate", "event_id": existing_event.id}
```

GitHub retries webhooks on timeout. The `github_delivery_id` uniqueness check prevents double-processing.

---

### Step 6: Resolve Repository

```python
def _resolve_repository(db, payload) -> Optional[Repository]:
    repo_data = payload.get("repository", {})
    github_owner = repo_data.get("owner", {}).get("login", "")
    github_name = repo_data.get("name", "")
    
    return db.query(Repository).filter(
        Repository.github_owner == github_owner,
        Repository.github_name == github_name,
    ).first()
```

Looks up the repository by owner + name. If not found in RepoMind DB: event is stored as `"skipped"` with reason `"repository_not_found"`.

---

### Step 7: Persist Webhook Event

```python
event = WebhookEvent(
    github_delivery_id=x_github_delivery,
    event_type=event_type,
    action=action,
    repository_id=repository_id,   # None if repo not found
    payload=payload,               # Full JSON stored as JSONB
    status="received",
    received_at=datetime.now(timezone.utc),
)
db.add(event)
db.flush()   # Get event.id (no commit yet)
```

---

### Step 8: Handle ping

```python
if event_type == "ping":
    event.status = "skipped"
    db.commit()
    return {"status": "pong"}
```

GitHub sends `ping` when you first configure a webhook. Returns `pong`.

---

### Step 9: Enqueue Review for pull_request Events

```python
if event_type == "pull_request" and action in REVIEW_TRIGGER_ACTIONS:  # {"opened", "synchronize", "reopened"}
    pr_number = payload["pull_request"]["number"]
    review_run = _enqueue_review(db, repository_id, pr_number)
```

`_enqueue_review()`:
```python
pr = db.query(PullRequest).filter(
    PullRequest.repository_id == repository_id,
    PullRequest.github_number == pr_github_number,
).first()

if not pr:
    return None   # PR not synced yet — skip with warning

# Idempotency: skip if already pending/running
existing = db.query(ReviewRun).filter(
    ReviewRun.pull_request_id == pr.id,
    ReviewRun.status.in_(["pending", "running"]),
).first()
if existing:
    return existing   # Already queued

# Create new pending ReviewRun
run = ReviewRun(
    pull_request_id=pr.id,
    commit_sha=pr.head_sha,
    status="pending",
    progress_message="Queued via GitHub webhook",
)
db.add(run)
db.flush()
return run
```

---

### Step 10: Commit and Return

```python
event.status = "processed" if review_run else "skipped"
event.processed_at = datetime.now(timezone.utc)
db.commit()
return {"status": "processed", "review_run_id": review_run.id}
```

GitHub expects a response within 10 seconds. The webhook handler returns immediately — the actual review processing happens asynchronously in the worker.

---

## Webhook Event Model

File: `backend/app/webhooks/models.py` → `WebhookEvent`

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | |
| `github_delivery_id` | String unique | From `X-GitHub-Delivery` header |
| `event_type` | String | `pull_request` / `ping` / etc. |
| `action` | String nullable | `opened` / `synchronize` / etc. |
| `repository_id` | FK → `repository.id` nullable | Resolved from payload |
| `payload` | JSONB | Full GitHub payload |
| `status` | String | `received` / `processed` / `skipped` |
| `processed_at` | DateTime nullable | When processing completed |
| `error_message` | Text nullable | If skipped with reason |
| `received_at` | DateTime | When webhook arrived |

---

## Configuration Required

| Environment Variable | Purpose |
|---|---|
| `GITHUB_WEBHOOK_SECRET` | Shared secret for HMAC verification (set in GitHub repo settings) |

If `GITHUB_WEBHOOK_SECRET` is not set: all webhook signatures fail, webhook endpoint returns 401.

---

## Trigger Actions

```python
REVIEW_TRIGGER_ACTIONS = frozenset(["opened", "synchronize", "reopened"])
```

All other `pull_request` actions (e.g., `closed`, `labeled`, `assigned`, `review_requested`) are stored but not acted upon.

---

## Key Files

| File | Location | Role |
|---|---|---|
| `routes.py` | `backend/app/webhooks/routes.py` | `github_webhook()` endpoint + HMAC + enqueue |
| `models.py` | `backend/app/webhooks/models.py` | `WebhookEvent` SQLAlchemy model |
| `main.py` | `backend/app/main.py` | Router inclusion: `app.include_router(webhooks_router, prefix="")` |

---

## Security Properties

| Property | Implementation |
|---|---|
| Authentication | HMAC-SHA256 with shared secret |
| Timing attack prevention | `hmac.compare_digest()` (constant-time comparison) |
| Replay prevention | `github_delivery_id` uniqueness in DB |
| No raw body modification | Body read before JSON parsing |
| Prompt injection isolation | Webhook payload stored in DB, not directly fed to LLM |
| Repository isolation | `_resolve_repository()` matches only repositories known to RepoMind |
