# 16 — API Endpoint Reference

## All Registered API Endpoints

File: `backend/app/main.py` — Router registration:

```python
app.include_router(auth_router)         # No prefix
app.include_router(org_router)          # No prefix
app.include_router(github_router)       # No prefix
app.include_router(review_router)       # No prefix
app.include_router(webhooks_router)     # No prefix
app.include_router(chat_router)         # No prefix
app.include_router(analytics_router)    # No prefix
app.include_router(ml_router)           # No prefix
```

---

## Authentication Endpoints

| Method | Path | Handler | Auth Required | Permission |
|---|---|---|---|---|
| `POST` | `/auth/register` | `register()` | No | — |
| `POST` | `/auth/login` | `login()` | No | — |
| `POST` | `/auth/logout` | `logout()` | No (clears cookie) | — |
| `GET` | `/auth/me` | `get_me()` | Yes (cookie) | — |

### `POST /auth/register`
**Request**: `{email, password, organization_name}`  
**Response**: `{user: {...}, memberships: [...]}` + sets HttpOnly cookie  
**Notes**: Creates User + Organization + OrgMembership(role='org_admin')

### `POST /auth/login`
**Request**: `{email, password}`  
**Response**: `{user: {...}, memberships: [...]}` + sets HttpOnly cookie

### `GET /auth/me`
**Request**: (HttpOnly cookie)  
**Response**: `{user: {...}, memberships: [...]}`

---

## Organization & Project Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `GET` | `/organizations/{org_id}/projects` | `get_projects()` | `PROJECTS_READ` |
| `POST` | `/organizations/{org_id}/projects` | `create_project()` | `PROJECTS_CREATE` |
| `GET` | `/organizations/{org_id}/members` | `get_members()` | `MEMBERS_READ` |
| `POST` | `/organizations/{org_id}/members` | `invite_member()` | `MEMBERS_INVITE` |

---

## Repository Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `POST` | `/repositories/connect?organization_id=` | `connect_repository()` | `REPOS_CONNECT` |
| `GET` | `/projects/{project_id}/repositories` | `get_repositories()` | `REPOS_READ` |
| `GET` | `/repositories/{repo_id}` | `get_repository()` | `REPOS_READ` |
| `POST` | `/repositories/{repo_id}/index` | `trigger_index()` | `REPOS_INDEX` |

### `POST /repositories/connect`
**Request**: `{github_owner, github_name, github_pat, default_branch, project_id}`  
**Side effects**: Encrypts PAT, creates `GithubConnection` + `Repository` (index_status='unindexed'), triggers sync  
**Permission**: `org_admin` only

### `POST /repositories/{id}/index`
**Request**: empty  
**Side effects**: Sets `repository.index_status = 'unindexed'` → worker picks up  
**Permission**: `tech_lead` or `org_admin`

---

## Pull Request Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `GET` | `/repositories/{repo_id}/pull-requests` | `list_pull_requests()` | `PRS_READ` |
| `GET` | `/pull-requests/{pr_id}` | `get_pull_request()` | `PRS_READ` |

### `GET /repositories/{id}/pull-requests`
**Side effects**: Calls `sync_pull_requests()` inline before returning (refreshes from GitHub)  
**Response**: Array of `PullRequest` objects

---

## Review Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `POST` | `/pull-requests/{pr_id}/review` | `trigger_review()` | Authenticated (any org member) |
| `GET` | `/review-runs/{run_id}` | `get_review_run()` | Authenticated (org member) |
| `POST` | `/review-runs/{run_id}/approve` | `approve_review_run()` | `reviewer`/`team_lead`/`org_admin` |

### `POST /pull-requests/{id}/review`
**Response**: `{job_id: <review_run_id>, status: "pending"}`  
**Status**: HTTP 202 Accepted  
**Notes**: Idempotent — returns existing run if same PR+SHA combination already exists  
**Worker**: Picks up the `pending` ReviewRun within 5 seconds

### `GET /review-runs/{id}`
**Response**: Full `ReviewRunResponse` including findings, conflicts, risk assessment, human decisions  
**Used for**: Frontend polling every 2 seconds until status = `completed` / `failed`

### `POST /review-runs/{id}/approve`
**Request**: `{action: "approve"|"request_changes"|"dismiss", note: "..."}`  
**Response**: `HumanDecision` object  
**Notes**: Upserts — one decision per user per review run

---

## Webhook Endpoint

| Method | Path | Handler | Auth |
|---|---|---|---|
| `POST` | `/webhooks/github` | `github_webhook()` | HMAC-SHA256 signature |

**Not in API docs** (include_in_schema=False)  
**Headers required**: `X-GitHub-Event`, `X-Hub-Signature-256`, `X-GitHub-Delivery`

---

## Chat Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `POST` | `/chat/sessions` | `create_session()` | `CHAT_USE` |
| `GET` | `/chat/sessions` | `get_sessions()` | `CHAT_USE` |
| `GET` | `/chat/sessions/{id}/messages` | `get_messages()` | `CHAT_USE` |
| `POST` | `/chat/sessions/{id}/messages` | `send_message()` | `CHAT_USE` |

Query params: `organization_id` required for scoping.

### `POST /chat/sessions/{id}/messages`
**Request**: `{message: "...", repository_id: <int>}`  
**Side effects**: RAG retrieval → LLM call → persist user + assistant messages  
**Response**: `ChatMessage` (assistant's response with `sources` and `is_grounded`)

---

## Analytics Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `GET` | `/analytics/organization/{org_id}` | `get_org_analytics()` | `ANALYTICS_READ` |

**Query params**: `?days=30` (default 30)  
**Response**: `{period_days, total_reviews, average_risk_score, findings_by_severity, findings_by_category, findings_by_lifecycle}`

---

## ML Endpoints

| Method | Path | Handler | Permission |
|---|---|---|---|
| `GET` | `/ml/prediction/pr/{pr_id}` | `get_pr_prediction()` | Authenticated |

**Response**: `{predicted_delay_category: "ON_TIME"|"SLOW", confidence_score: 0.5, prediction_model_version: "baseline-v1"}`  
**Note**: Always returns rule-based baseline (insufficient training data guard requires 50+ closed PRs)

---

## Common Response Codes

| Code | Meaning |
|---|---|
| `200 OK` | Success |
| `201 Created` | Resource created |
| `202 Accepted` | Job accepted (review trigger) |
| `400 Bad Request` | Validation error / invalid state |
| `401 Unauthorized` | Missing/invalid auth cookie |
| `403 Forbidden` | Authenticated but insufficient permission |
| `404 Not Found` | Resource not found (or access denied for security) |
| `422 Unprocessable Entity` | Pydantic validation failure |
| `502 Bad Gateway` | GitHub API unreachable |

---

## CORS Configuration

File: `backend/app/main.py`

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],   # Vite dev server only
    allow_credentials=True,                    # Required for cookie auth
    allow_methods=["*"],
    allow_headers=["*"],
)
```

`allow_credentials=True` is required for the browser to send and receive the HttpOnly cookie.

---

## Global API Base URL

File: `frontend/src/lib/api.js:1`

```javascript
const API_BASE = 'http://localhost:8000';
```

All requests use `credentials: 'include'` to send the HttpOnly cookie.
