# RepoMind Intelligence 2.0 — Complete API Audit

**Document Version:** 2.0-Audit  
**API Engine:** FastAPI 0.115.0  
**Authentication Scheme:** HttpOnly Cookie (`access_token`) containing signed JWT  
**RBAC Enforcement:** Server-side via `assert_org_permission` and `require_permission`  
**Directives Observed:** Inspected live route handlers and schemas without modifying endpoints.

---

## 1. Master API Route Catalog

The RepoMind backend registers **33 distinct REST endpoints** mounted across 10 functional router domains:

```
FastAPI Root Application
  ├── health_router (/health)
  ├── auth_router (/auth/*)
  ├── orgs_router (/organizations/*, /projects/*, /repositories/*)
  ├── github_router (/repositories/*, /pull-requests/*, /oauth/*)
  ├── review_router (/pull-requests/*/review*, /review-runs/*)
  ├── webhooks_router (/webhooks/*)
  ├── chat_router (/chat/*)
  ├── analytics_router (/analytics/*)
  ├── security_router (/security/*)
  └── onboarding_router (/repositories/*/onboarding/*)
```

---

## 2. Detailed Endpoint Inventory & Contract Audit

### 2.1 Health Domain

| Method | Path | Summary | Auth Required | RBAC Permission | Status |
|--------|------|---------|---------------|-----------------|--------|
| `GET` | `/health` | Application healthcheck | None | Public | Verified Real |

- **Response:** `{"status": "ok"}` (200 OK)

---

### 2.2 Authentication & Session Domain (`/auth`)

| Method | Path | Summary | Auth Required | Request Schema | Response Schema | Status |
|--------|------|---------|---------------|----------------|-----------------|--------|
| `POST` | `/auth/login` | Authenticate user & set cookie | None | `UserLogin` (email, password) | `AuthResponse` + Set-Cookie | Verified Real |
| `POST` | `/auth/bootstrap` | Initialize initial org & admin | None | `BootstrapRequest` (token, email, password, org) | `AuthResponse` (201 Created) | Verified Real |
| `POST` | `/auth/onboard` | Accept invite & set password | None | `OnboardRequest` (invite_token, password) | `AuthResponse` (200 OK) | Verified Real |
| `POST` | `/auth/change-password` | Update current user password | Current User | `PasswordChangeRequest` | `{"message": "..."}` | Verified Real |
| `POST` | `/auth/logout` | Invalidate cookie session | None | Empty | `{"message": "..."}` + Delete-Cookie | Verified Real |
| `GET` | `/auth/me` | Fetch active user profile | Current User | None | `AuthResponse` (200 OK) | Verified Real |

- **Security Note:** Session cookie enforces `HttpOnly=True` and `SameSite=lax`. `secure` flag is dynamically toggled based on `ENVIRONMENT`.

---

### 2.3 Organizations, Projects & Repositories Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Frontend Client | Status |
|--------|------|---------|------|------------------|-----------------|--------|
| `POST` | `/organizations` | Create an organization | User | Any authenticated user | `orgApi.createOrganization` | Verified Real |
| `GET` | `/organizations` | List user's organizations | User | Scoped to caller's memberships | Implicit in `/auth/me` | Verified Real |
| `GET` | `/organizations/{id}` | Get organization metadata | User | `verify_org_member` | `orgApi.getOrganization` | Verified Real |
| `GET` | `/organizations/{id}/projects` | List projects in org | User | `verify_org_member` | `orgApi.getProjects` | Verified Real |
| `POST` | `/organizations/{id}/projects` | Create project in org | User | `verify_org_admin` | `orgApi.createProject` | Verified Real |
| `GET` | `/projects/{id}/repositories` | List repositories in project | User | `verify_org_member` | `orgApi.getRepositories` | Verified Real |
| `POST` | `/projects/{id}/repositories` | Create repository record | User | `verify_org_admin` | None (Direct DB/Connect) | Verified Real |
| `GET` | `/repositories/{id}` | Get repository details | User | `verify_org_member` | `orgApi.getRepository` | Verified Real |
| `GET` | `/organizations/{id}/members` | List members and roles | User | `verify_org_member` | `MemberManagement.jsx` | Verified Real |
| `POST` | `/organizations/{id}/members` | Invite new member | User | `verify_org_admin` | `orgApi.inviteMember` | Verified Real |
| `PUT` | `/organizations/{id}/members/{uid}/role`| Change member role | User | `verify_org_admin` | `orgApi.updateMemberRole` | Verified Real |
| `DELETE`| `/organizations/{id}/members/{uid}` | Remove member from org | User | `verify_org_admin` | `orgApi.removeMember` | Verified Real |
| `POST` | `/organizations/{id}/teams` | Create team | User | `verify_org_admin` | `orgApi.createTeam` | Verified Real |
| `GET` | `/organizations/{id}/teams` | List teams in org | User | `verify_org_member` | `orgApi.getTeams` | Verified Real |

---

### 2.4 GitHub Integration & Pull Requests Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status | Discrepancy / Bug |
|--------|------|---------|------|------------------|--------|-------------------|
| `GET` | `/oauth/login` | Initiate GitHub OAuth | User | Authenticated | Verified Real | Returns OAuth redirect URL with CSRF state |
| `GET` | `/oauth/callback` | OAuth redirect callback | User | State cookie matching | Verified Real | Exchanges code for access token; encrypts with Fernet |
| `DELETE`| `/oauth/unlink` | Unlink GitHub account | User | Authenticated | Verified Real | Removes GitHubIdentity |
| `GET` | `/organizations/{id}/github/repos` | List available repos from GitHub | User | Caller's GitHub OAuth token | Verified Real | Discovers user's admin repos on GitHub |
| `POST` | `/repositories/connect` | Connect GitHub repo to project | User | `verify_org_admin` | Verified Real | **Discrepancy:** Accepts `organization_id` as Query param, but `project_id` in JSON body |
| `POST` | `/repositories/{id}/index` | Enqueue repo for indexing | User | `verify_org_admin` | Verified Real | Transitions `index_status` to `'unindexed'` for worker pickup |
| `GET` | `/repositories/{id}/pull-requests` | List PRs for repo (sync option) | User | `verify_org_member` | Verified Real | Syncs from GitHub on first call or `sync=True` |
| `GET` | `/pull-requests/{id}` | Get single PR details | User | `verify_org_member` | Verified Real | Fetches cached PR metadata |
| `POST` | `/pull-requests/{id}/sync` | Force deep sync of PR from GitHub | User | `verify_org_member` | Verified Real | Syncs commits, files, reviews, checks, comments |
| `GET` | `/pull-requests/{id}/events` | Activity log for PR | User | `verify_org_member` | Verified Real | Returns ordered timeline from `pull_request_event` |
| `GET` | `/pull-requests/{id}/files` | List changed files in PR | User | `verify_org_member` | **BROKEN / MOCK** | **Critical Defect:** Returns static hardcoded mock: `[{"filename": "example.py", "status": "modified", "additions": 10, "deletions": 2}]` |
| `POST` | `/pull-requests/{id}/reopen` | Reopen closed PR | User | `verify_org_member` | Verified Real | Updates `pull_request.state = 'open'` |
| `POST` | `/pull-requests/{id}/merge` | Queue PR merge automation | User | `Permission.PRS_MERGE` (Team Lead+) | Verified Real | Enqueues `AutomationAction(action_type="MERGE")` |
| `GET` | `/repositories/{id}/merge-policy` | Fetch project merge policy | User | `verify_org_member` | Verified Real | Reads `ProjectMergePolicy` |
| `PUT` | `/repositories/{id}/merge-policy` | Update project merge policy | User | `verify_org_admin` | Verified Real | Updates policy flags |
| `GET` | `/repositories/{id}/branches` | List remote Git branches | User | `verify_org_member` | Verified Real | Directly queries GitHub via PAT |
| `GET` | `/repositories/{id}/commits` | List remote Git commits | User | `verify_org_member` | Verified Real | Directly queries GitHub via PAT |
| `GET` | `/pull-requests/{id}/conflicts` | List detected conflicts | User | `verify_org_member` | Verified Real | Fetches from `conflict` table of latest completed review run |

---

### 2.5 Review & Decision Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status |
|--------|------|---------|------|------------------|--------|
| `POST` | `/pull-requests/{id}/review` | Trigger AI Review Run | User | `verify_org_member` | Verified Real (Enqueues pending ReviewRun) |
| `GET` | `/pull-requests/{id}/review-runs` | List review history for PR | User | `verify_org_member` | Verified Real |
| `GET` | `/review-runs/{id}` | Get review run findings & risk | User | `verify_org_member` | Verified Real |
| `POST` | `/review-runs/{id}/decide` | Human decision (Approve/Reject) | User | `PRS_APPROVE` / `PRS_REQUEST_CHANGES` | Verified Real (Creates `HumanDecision`, `HumanReview`, `AutomationAction`) |
| `GET` | `/review-runs/{id}/decide` | Get decisions for run | User | `verify_org_member` | Verified Real |

---

### 2.6 Webhook Receiver Domain

| Method | Path | Summary | Auth | Verification | Status |
|--------|------|---------|------|--------------|--------|
| `POST` | `/webhooks/github` | Ingest GitHub webhook events | None (Public) | HMAC-SHA256 with `GITHUB_WEBHOOK_SECRET` | Verified Real |

- **Security Note:** Excluded from OpenAPI schema (`include_in_schema=False`). Deduplicates requests on `X-GitHub-Delivery`.

---

### 2.7 Engineering Analytics Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status |
|--------|------|---------|------|------------------|--------|
| `GET` | `/analytics/organization/{id}` | Organization intelligence metrics | User | `Permission.ANALYTICS_READ` | Verified Real |

- **Metrics Returned:** PR review volume, average risk score, finding distributions by severity, category, and lifecycle.

---

### 2.8 Security Browser Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status |
|--------|------|---------|------|------------------|--------|
| `GET` | `/security/findings` | Org-wide security vulnerabilities | User | `verify_org_member` | Verified Real |
| `PUT` | `/security/findings/{id}/status` | Triage security finding status | User | `verify_org_member` | Verified Real |

---

### 2.9 AI Assistant / Chat Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status |
|--------|------|---------|------|------------------|--------|
| `POST` | `/chat/sessions` | Create context-scoped chat session | User | `Permission.CHAT_USE` + Org check | Verified Real |
| `GET` | `/chat/sessions` | List user chat sessions | User | Authenticated | Verified Real |
| `GET` | `/chat/sessions/{id}/messages` | Get session message history | User | Session ownership check | Verified Real |
| `POST` | `/chat/sessions/{id}/messages` | Send message & get RAG response | User | Session ownership + `CHAT_USE` | Verified Real |

---

### 2.10 Developer Onboarding Domain

| Method | Path | Summary | Auth | RBAC Enforcement | Status |
|--------|------|---------|------|------------------|--------|
| `GET` | `/repositories/{id}/onboarding/blueprint` | Get cached/generate blueprint | User | `Permission.REPOS_READ` | Verified Real |
| `POST` | `/repositories/{id}/onboarding/blueprint/refresh` | Force blueprint re-analysis | User | `Permission.REPOS_INDEX` + Team Lead | Verified Real |
| `GET` | `/repositories/{id}/onboarding/progress` | Get private user progress | User | Scoped strictly to `current_user.id` | Verified Real |
| `PUT` | `/repositories/{id}/onboarding/progress` | Update milestones & notes | User | Scoped strictly to `current_user.id` | Verified Real |

---

## 3. Frontend Client Mapping & API Discrepancies

### 3.1 Mapping Inconsistencies Between `api.js` and FastAPI Endpoints

1. **Broken Endpoint `/pull-requests/{id}/files`:**
   - **Frontend:** `ReviewPage.jsx` relies on file change counts and paths for review context.
   - **Backend:** [backend/app/github/routes.py:571](file:///d:/Repomind/Repo-Mind-/backend/app/github/routes.py#L571) returns hardcoded dummy data:
     ```json
     [{"filename": "example.py", "status": "modified", "additions": 10, "deletions": 2}]
     ```
   - **Fix Required:** Query the `pull_request_file` table (populated during PR sync) and return actual file diff metadata.

2. **Query Parameter vs Body Discrepancy on `/repositories/connect`:**
   - **Backend Definition:**
     ```python
     def connect_repository(
         payload: schemas.GitHubConnectRequest,
         organization_id: int = Query(...),
         ...
     ):
     ```
   - **Frontend Call (`frontend/src/lib/api.js:130`):**
     ```javascript
     connectRepository: (orgId, payload) =>
       apiRequest(`/repositories/connect?organization_id=${orgId}`, {
         method: 'POST',
         body: JSON.stringify(payload),
       }),
     ```
   - While functionally working due to the query string concatenation, mixing URL query parameters with JSON bodies for primary keys is poor REST practice and should be normalized.

3. **Missing Frontend Projects UI:**
   - The backend defines full CRUD for Projects (`POST/GET /organizations/{id}/projects`).
   - The frontend `lib/api.js` defines `getProjects` and `createProject`, but **no UI page or dropdown exists** in the frontend to switch or create projects. Repositories are displayed without explicit project categorization.

4. **Missing Inline Review Comment API:**
   - The backend provides no endpoint to query or post line-level review comments (`PullRequestReviewComment`) directly on GitHub's diff viewer.
