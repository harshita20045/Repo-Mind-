# RepoMind 2.0 Complete System Architecture

==================================================
## PART 1 — EXECUTIVE EXPLANATION
=================================

### 30-Second Manager Explanation
**What is RepoMind?** RepoMind is an automated pull request review system that sits between your developers and GitHub. 
**What problem does it solve?** It reduces the time senior engineers spend doing basic code review by having an AI automatically catch bugs, security issues, and style violations as soon as a PR is opened.
**Who uses it?** Development teams.
**Automated vs Human:** RepoMind automatically reads the PR, fetches relevant context from your existing codebase (RAG), and produces actionable findings. However, a human (Reviewer or Team Lead) retains full control over the final decision to Request Changes or Approve the PR. 
**Differentiation:** Unlike standard PR bots, RepoMind understands your whole repository architecture (via RAG) and enforces strict RBAC separation between AI findings and human decisions.

### 2-Minute Engineering Manager Explanation
RepoMind operates as a DB-backed, multi-tenant FastAPI backend that orchestrates an AI review pipeline. When a developer pushes code, GitHub sends a webhook to RepoMind. This enqueues a `ReviewRun` job in our PostgreSQL database. A standalone Python worker process (`worker.py`) picks up the job via `SELECT FOR UPDATE SKIP LOCKED` (ensuring safe concurrency without needing Redis/Celery).
The worker fetches the PR diff, retrieves relevant existing code using our custom RAG pipeline (pgvector), and runs static analysis. It packages all this into a system prompt for the LLM (Gemini/Claude). The LLM's structured output is validated, and findings/risk scores are persisted to the database. Finally, a Team Lead logs into the React frontend, reviews the findings, and clicks "Approve" or "Request Changes". This human decision is recorded as a `HumanDecision` and dispatched to GitHub as a real review comment using the Lead's linked GitHub OAuth credential.

### 5-Minute Senior Developer Explanation
RepoMind is designed around a strictly structured data model in PostgreSQL. It defines a rigid 4-role RBAC system (`org_admin`, `team_lead`, `reviewer`, `developer`) where authorization is checked server-side via dependency injection (e.g., `require_permission(Permission.PRS_REVIEW)`).
We use GitHub OAuth solely for identity linking and API operations (fetching diffs, posting reviews, merging), while core authentication remains a separate Email/Password system using HTTP-only JWT cookies.
The pipeline is entirely async-decoupled from webhooks. The `POST /webhooks/github` endpoint only validates the HMAC SHA-256 signature, deduplicates via `X-GitHub-Delivery`, saves the payload to `webhook_event`, and creates a `pending` `ReviewRun`.
The background worker executes `run_review()`. It queries pgvector for codebase context matching the PR diff, calls the LLM, validates the JSON output, and saves `Finding`, `RiskAssessment`, and `Conflict` rows.
Crucially, the AI does *not* post directly to GitHub. Instead, a human creates a `HumanDecision`. A secondary automation worker processes `AutomationAction` queues to actually make the GitHub API calls (using the human's decrypted OAuth token), ensuring that GitHub always reflects the human's authenticated action.

==================================================
## PART 2 — COMPLETE SYSTEM ARCHITECTURE
========================================

**Frontend (React/Vite)**
- *What:* The user interface where users log in, view PRs, and make review decisions.
- *Reads/Writes:* Calls FastAPI backend endpoints. Uses React Query for state management.

**FastAPI Backend (`backend/app/main.py`)**
- *What:* Core API server.
- *Responsibility:* Handles Auth, RBAC, REST endpoints, and Webhook ingestion.
- *Trigger:* HTTP Requests.

**Authentication / Authorization (`backend/app/auth/`)**
- *What:* Email/password login and strict 4-role RBAC middleware.
- *Files:* `auth/routes.py`, `auth/permissions.py`.
- *Fails:* Returns 401/403.

**PostgreSQL + pgvector (`backend/app/db.py`)**
- *What:* Primary data store and vector database.
- *Responsibility:* Stores Users, Repos, ReviewRuns, Findings, and RAG chunk embeddings.

**GitHub Integration (`backend/app/github/`)**
- *What:* OAuth linking and GitHub API client.
- *Files:* `github/client.py`, `github/encryption.py`, `github/automation.py`.
- *Responsibility:* Exchanges OAuth codes, encrypts tokens, fetches PR diffs, posts reviews.

**Webhook Processing (`backend/app/webhooks/routes.py`)**
- *What:* Receives GitHub events.
- *Trigger:* GitHub HTTP POST.
- *Fails:* If HMAC invalid, returns 401. If PR missing, marks event `skipped`.

**DB-backed Review Worker (`worker/worker.py`)**
- *What:* Infinite loop polling PostgreSQL for `pending` ReviewRuns using `SKIP LOCKED`.
- *Responsibility:* Executes the AI review pipeline.
- *Fails:* Marks ReviewRun `failed`, saves `error_message`, moves to next job. Crash recovery resets `running` jobs to `pending` on startup.

**RAG (`backend/app/rag/`)**
- *What:* Retrieves context based on PR diff.
- *Files:* `rag/service.py`, `rag/loader.py`, `rag/retriever.py`.
- *Responsibility:* Chunks repository, embeds text, queries pgvector.

**Static Analysis / Linting (`backend/app/linter/`)**
- *What:* Runs Ruff/Bandit. Output is fed to LLM.

**LLM (`backend/app/review/provider.py`)**
- *What:* Generates findings.
- *Trigger:* Worker execution.
- *Fails:* Retries once on parsing error, then fails the run.

**Review Findings / Risk (`backend/app/review/models.py`)**
- *What:* Persisted structured output (`Finding`, `RiskAssessment`).

**Human Decision (`backend/app/review/models.py`)**
- *What:* `HumanDecision` table records Approve/Request Changes.

**GitHub Action (`backend/app/github/automation.py`)**
- *What:* Consumes `AutomationAction` rows to post reviews/merges to GitHub using the human's OAuth token.

==================================================
## PART 3 — REPOSITORY STRUCTURE
================================
- `backend/app/auth/`: Email/password, JWT, strict 4-role RBAC (`permissions.py`).
- `backend/app/organizations/`: Multi-tenant hierarchy models (Organization, Project, Repository).
- `backend/app/github/`: OAuth credential management, GitHub API client, and background automation actions.
- `backend/app/webhooks/`: Webhook receiver, HMAC validation, deduplication.
- `backend/app/review/`: Core AI orchestration (`service.py`), LLM prompts, findings, risk assessment.
- `backend/app/rag/`: Document loading, chunking, embedding, pgvector retrieval.
- `worker/worker.py`: The DB-backed polling daemon.
- `frontend/`: React UI.

**If you are new to RepoMind, read these files first:**
1. `backend/app/review/models.py` - Understand the core domain (ReviewRun, Finding, RiskAssessment).
2. `backend/app/github/models.py` - Understand PRs, Webhooks, AutomationActions.
3. `backend/app/auth/permissions.py` - Understand the hardcoded 4-role RBAC.
4. `backend/app/webhooks/routes.py` - See how GitHub webhooks enqueue jobs.
5. `worker/worker.py` - See how jobs are executed concurrently.
6. `backend/app/review/service.py` (`run_review`) - The exact step-by-step AI pipeline.
7. `backend/app/github/automation.py` - How human decisions actually reach GitHub.

==================================================
## PART 4 — USER AND ORGANIZATION HIERARCHY
===========================================
**Hierarchy:** User → OrganizationMembership → Organization → Project → Repository → Pull Request → Review Run → Finding → Human Review → Automation Action

- **Multiple Orgs?** Yes, a User can belong to multiple Orgs via `OrganizationMembership`.
- **Active Org?** Frontend passes `organization_id` context in URL/payloads.
- **Backend Access?** Evaluated via `require_org_permission` which checks if the `current_user` has the required role in `organization_id`.
- **Projects:** Group repositories within an organization.
- **Repositories:** Linked to a Project. Contains Pull Requests.

**Important Distinctions:**
- **RepoMind User Identity:** Email/Password based login.
- **Organization Role:** `developer`, `reviewer`, `team_lead`, `org_admin`.
- **GitHub Identity:** Linked via OAuth (`github_identity` table).
- **GitHub Credential:** Encrypted OAuth PAT used to act on GitHub's API.

==================================================
## PART 5 — AUTHENTICATION
==========================
- Email/Password login. No native social login for the app itself.
- **JWT / Session:** JWT tokens are issued and stored in HTTP-Only cookies (`access_token`).
- `/auth/me`: Returns the current user and all their organization memberships.
- **Onboarding:** Org Admin generates an `invitation_token_hash`. User uses `/onboard` to set their password, which consumes the token and activates their `OrganizationMembership`. No automated email sending is currently in source.

==================================================
## PART 6 — GITHUB OAUTH
========================
RepoMind account ≠ GitHub account.
A user logs into RepoMind using Email. Then, they optionally navigate to `/oauth/login` to link their GitHub account.
- **Flow:** Redirect to GitHub → Callback with `code` → Exchange for token.
- **State Protection:** CSRF protected using an `oauth_state` cookie.
- **Credentials:** The token is encrypted using Fernet and stored in `github_credential`.
- **Usage:** If an action (like Merging) requires GitHub API access, the backend looks up the `GitHubIdentity` for the user and decrypts their token to perform the action.

==================================================
## PART 7 — FOUR ROLE RBAC MODEL
================================
Strictly 4 roles (defined in `backend/app/auth/permissions.py`):
1. **developer:** Read-only access to repos, PRs, findings, chat.
2. **reviewer:** + Can Review PRs, Request Changes, Dismiss Findings. Cannot approve.
3. **team_lead:** + Can Approve PRs, Merge PRs, Trigger repository indexing.
4. **org_admin:** + Can manage org, invite members, connect GitHub repos.

Backend authorization is the *actual* security boundary. UI hiding buttons is just UX.

==================================================
## PART 8 — ORGANIZATION INVITATIONS
====================================
1. `org_admin` generates an invitation.
2. Backend creates a pending `User` with an `invitation_token_hash`.
3. The admin manually copies the invitation link to the user (no emails sent by the system).
4. User clicks link, submits `/onboard` with a new password.
5. User is now an active member with their assigned role.

==================================================
## PART 9 — GITHUB REPOSITORY CONNECTION
========================================
1. `org_admin` calls `/repositories/connect`.
2. RepoMind uses the admin's GitHub token to fetch the repo details.
3. A `Repository` row is created, assigned to a `Project` (which isolates it to the `Organization`).
4. **Isolation:** A user can only access a `Repository` if their `OrganizationMembership` grants them access to the parent Organization.

==================================================
## PART 10 — WEBHOOK ARCHITECTURE
=================================
1. GitHub POSTs to `/webhooks/github`.
2. Raw body is hashed via HMAC-SHA256 with `GITHUB_WEBHOOK_SECRET` to verify authenticity.
3. `X-GitHub-Delivery` header is checked against the `webhook_event` table for deduplication.
4. Payload is persisted to the DB *before* processing.
5. If `pull_request` (opened, synchronize, reopened) or `pull_request_review_comment` (created), RepoMind queries the DB for the `Repository`.
6. If found, an `upsert_pr` runs, and a `ReviewRun` is created with status `pending`.

==================================================
## PART 11 — PULL REQUEST LIFECYCLE
===================================
1. Commit pushed → PR opened.
2. Webhook arrives → Validated and stored.
3. `ReviewRun` created (`pending`).
4. Worker claims run (`running`).
5. PR diff fetched from GitHub API.
6. Context retrieved via `RAGRetriever`.
7. Static analysis (`run_linters`) executed.
8. Semantic conflicts detected.
9. Prompt sent to LLM.
10. JSON response parsed → `Finding` & `RiskAssessment` persisted.
11. Run marked `completed`.
12. `team_lead` views UI, clicks "Approve".
13. `HumanDecision` saved. `AutomationAction` (MERGE/APPROVE) queued.
14. Worker processes `AutomationAction` → calls GitHub API.

==================================================
## PART 12 — REVIEW WORKER
==========================
- **No Redis/Celery/Kafka:** The queue is simply the `ReviewRun` and `AutomationAction` PostgreSQL tables.
- **Concurrency:** `SELECT ... FOR UPDATE SKIP LOCKED` ensures multiple `worker.py` processes can safely pull jobs without race conditions.
- **Stale Recovery:** On startup, the worker resets any `running` jobs back to `pending`. This gracefully recovers from OOM kills or crashes.

==================================================
## PART 13 — RAG PIPELINE
=========================
- **Indexing:** `index_repository` loads documents, hashes content for idempotency, chunks via `TextChunker`, embeds via `LocalEmbedder`, and saves to pgvector.
- **Retrieval:** During `run_review`, the PR diff generates a query. `RAGRetriever` fetches the top K most similar chunks.
- **Isolation:** `retrieve_context` strictly filters by `repository_id` ensuring no cross-tenant data leakage.
- *Example:* If `auth.py` changes, RAG will pull in `auth/models.py` and documentation about JWT to ensure the LLM understands the existing architecture before hallucinating new dependencies.

==================================================
## PART 14 — LLM REVIEW PIPELINE
================================
- **Isolation:** The diff, RAG context, and linter results are placed strictly into the `user_content` payload. `system_prompt` is static. This mitigates Prompt Injection.
- **Limits:** Diff size and linter output are aggressively truncated to prevent token limit blowouts.
- **Retries:** If the LLM returns invalid JSON, `run_review` catches `LLMOutputParseError` and retries *once* with a `RETRY_SYSTEM_PROMPT` before failing the run.

==================================================
## PART 15 — REVIEW FINDINGS AND RISK
=====================================
- LLM outputs `FindingSchema` elements.
- These are validated and saved as `Finding` rows (`severity`, `type`, `confidence`).
- `FindingEvidence` rows link findings back to RAG chunks (Grounding).
- `RiskAssessment` calculates an overall 0-100 score, complete with JSON explainability `factors` and `blast_radius`.
- Findings have a `lifecycle_status` (new, persistent, resolved) tracked across multiple PR commits.

==================================================
## PART 16 — HUMAN REVIEW DECISIONS
===================================
- **AI ≠ Human:** The LLM *never* directly posts reviews to GitHub.
- Humans submit a `HumanDecision`.
- If a `team_lead` approves, an `AutomationAction` is queued. The worker executes it via GitHub API using the `team_lead`'s token.
- If the token is expired, the `AutomationAction` will fail with an HTTP 401 error code, visible in the DB.

==================================================
## PART 17 — REQUEST CHANGES
============================
- UI → API → `require_permission(Permission.PRS_REQUEST_CHANGES)`.
- Saves `HumanDecision` (action=request_changes, note="...").
- Queues `AutomationAction` (REQUEST_CHANGES).
- `process_automation_actions` worker picks it up.
- **Gap Notice:** The implementation *does* send the human note to GitHub. It also automatically appends a markdown list of open AI findings to the GitHub review body.

==================================================
## PART 18 — APPROVAL
=====================
- **Who:** `team_lead` or `org_admin`. (`reviewer` is explicitly blocked from approval by RBAC).
- `HumanDecision` saved.
- Evaluate merge policy (`evaluate_merge_policy()`). If require_human_approval passes, it might trigger an auto-merge.
- The approval itself is sent to GitHub via `AutomationAction(APPROVE)`.

==================================================
## PART 19 — MERGE
==================
- **Authorization:** `PRS_MERGE` permission.
- **Protection:** API accepts `expected_head_sha`. The `AutomationAction` stores this. The worker passes the SHA to GitHub. If the branch has been updated in the meantime, GitHub rejects the merge. This is critical stale-commit protection.

==================================================
## PART 20 — FRONTEND ARCHITECTURE
==================================
- Standard Vite/React stack.
- Global Context knows the `organization_id`.
- Relies entirely on the backend for enforcement. Hides "Approve" buttons if user is a `developer` or `reviewer`, but backend verifies anyway.

==================================================
## PART 21 — API MAP
====================
**Auth:**
`POST /auth/login` - No Auth - Return JWT cookie
`GET /auth/me` - Valid Session - Return User & Memberships

**GitHub OAuth:**
`GET /oauth/login` - Valid Session - Initiates GitHub OAuth
`GET /oauth/callback` - Valid Session - Exchanges code for PAT

**Repositories:**
`POST /repositories/connect` - `ORG_ADMIN` - Connects repo to Project
`GET /repositories/{id}/pull-requests` - `REPOS_READ` - Lists PRs

**Webhooks:**
`POST /webhooks/github` - No Auth (uses HMAC) - Ingest event

==================================================
## PART 22 — DATABASE MODEL
===========================
`User` --< `OrganizationMembership` >-- `Organization` --< `Project` --< `Repository` --< `PullRequest` --< `ReviewRun` --< `Finding`

Key Models:
- `ReviewRun`: Tracks `pending`, `running`, `completed`.
- `Finding`: LLM output.
- `WebhookEvent`: Raw GitHub payload.
- `GitHubIdentity`: Links `User` to GitHub ID.
- `GitHubCredential`: Encrypted OAuth PAT.
- `AutomationAction`: Queue for GitHub API calls.

==================================================
## PART 23 — SECURITY MODEL
===========================
- **Authentication:** HTTP-only cookies.
- **Authorization:** Server-side `require_org_permission` blocks BOLA/IDOR.
- **Webhooks:** HMAC SHA-256 validation before parsing JSON.
- **Credentials:** Fernet encryption for PATs.
- **Concurrency:** `SKIP LOCKED` prevents duplicate job execution.
- **Prompt Injection:** Strict separation of static `system_prompt` and untrusted `user_content`.

==================================================
## PART 24 — FAILURE AND ERROR HANDLING
=======================================
- **Webhook HMAC Invalid:** Backend returns 401. DB state unchanged.
- **Worker Crash:** On restart, `worker.py` updates `running` jobs to `pending`.
- **LLM Parse Failure:** Retries once, then marks `ReviewRun.status = "failed"`, UI shows failure.
- **GitHub API 401 (Expired token):** `AutomationAction.status` becomes `FAILED`, `error_code` = 401.

==================================================
## PART 25 — TESTING
====================
- Tests exist in `backend/tests/` and various `test_*.py` files in root.
- Includes automated endpoint tests, repo discovery tests, and End-to-End phase tests.
- Contains explicit scripts (`simulate_oauth.py`, `verify_encryption.py`) for manual local validation.

==================================================
## PART 26 — REAL PRODUCTION-LIKE FLOW
======================================
1. Admin uses `/auth/bootstrap` to create Org.
2. Admin generates invite token.
3. Team Lead uses `/onboard` to set password.
4. Team Lead logs in → connects GitHub via `/oauth/login`.
5. Repo is connected.
6. Webhook arrives (`pull_request.opened`).
7. Worker fetches job, runs RAG, calls Gemini, saves Findings.
8. Team Lead opens React UI, views Findings.
9. Team Lead clicks "Request Changes".
10. Worker processes `AutomationAction` and posts Team Lead's review to GitHub.

==================================================
## PART 27 — "HOW EVERYTHING CONNECTS"
======================================
User logs in (Auth) → Belongs to Org (Membership) → Has Role (RBAC).
User links GitHub (OAuth) → Encrypted Token stored (GitHubCredential).
GitHub sends Webhook → Backend validates HMAC → Creates `ReviewRun` (Database).
Worker polls DB (`SKIP LOCKED`) → Reads PR diff via GitHub API using Token → Queries pgvector (RAG) → Calls LLM (Provider) → Saves `Finding` and `RiskAssessment`.
Human reviews UI → Submits `HumanDecision` → Creates `AutomationAction` → Worker polls DB → Calls GitHub API using human's Token to Merge.

==================================================
## PART 28 — MANAGER-FRIENDLY EXPLANATION
=========================================
**The Problem:** Senior engineers waste hours reviewing trivial code issues.
**The Solution:** RepoMind automatically reviews PRs using AI that understands your specific repository.
**Safety First:** The AI *never* approves or merges code itself. It only highlights risks and findings. A human Team Lead must always review the AI's findings and click the final "Approve" button.
**Architecture:** It’s built on standard, scalable technology (PostgreSQL, Python) without complex infrastructure requirements like Redis. Security is paramount: we use strict roles, encrypt all GitHub tokens, and validate every incoming webhook to ensure data integrity.

==================================================
## PART 29 — SENIOR DEVELOPER EXPLANATION
=========================================
RepoMind is a FastAPI backend with a PostgreSQL DB utilizing pgvector for RAG. We employ a DB-backed worker model utilizing `SELECT FOR UPDATE SKIP LOCKED` for rock-solid concurrency without adding infrastructure overhead.
Auth is decoupled from GitHub: Users authenticate via standard JWT HTTP-Only cookies, and use GitHub OAuth *only* to grant us a PAT.
The AI pipeline in `review/service.py` (`run_review`) is strictly isolated. We fetch diffs and RAG chunks, but inject them into the `user_content` of the LLM prompt to prevent prompt injection. LLM output is heavily validated against a schema, and `lifecycle_status` (new/persistent/resolved) is calculated against previous `ReviewRuns`. Actions that mutate GitHub state are queued as `AutomationAction` rows and executed asynchronously using the initiating user's decrypted PAT.

==================================================
## PART 30 — NEW DEVELOPER ONBOARDING
=====================================
1. Read `backend/app/review/models.py`.
2. Read `backend/app/github/models.py`.
3. Trace `backend/app/webhooks/routes.py` to see how PRs enter the system.
4. Trace `worker/worker.py` to see the polling loop.
5. Trace `backend/app/review/service.py:run_review()` to see the entire LLM pipeline.
6. Trace `backend/app/auth/permissions.py` to understand RBAC.
7. Understand that `AutomationAction` is our out-bound queue to GitHub.

==================================================
## PART 31 — CURRENT STATE
==========================
**CONFIRMED IMPLEMENTED:**
- 4-role strict RBAC.
- GitHub OAuth linking and Fernet token encryption.
- HMAC Webhook ingestion and deduplication.
- DB-backed worker with `SKIP LOCKED`.
- RAG pipeline (Chunking, Embedding, pgvector).
- LLM findings, Risk calculation, and Conflict detection.
- Automation queue for out-bound GitHub Actions.

**IMPLEMENTED BUT WITH LIMITATIONS:**
- LLM output parsing only retries once.
- RAG context limit is hardcoded.
- Diff truncation is hardcoded, which might cut off large PRs.

**NOT IMPLEMENTED / NOT CONFIRMED:**
- Email sending for invitations (Admin must manually copy the token link).
- Redis / Celery / Kafka (By design, not needed).
- Support for GitLab / Bitbucket.

==================================================
## PART 32 — IMPORTANT TECHNICAL RISKS
======================================
1. **Diff Truncation:** Large PRs truncate the diff to fit LLM context. *Mitigation:* `MAX_DIFF_CHARS` bounds it, but the AI misses the end of the PR.
2. **Worker Polling Load:** DB polling every 5s is fine for small scale, but unscalable to thousands of orgs. *Mitigation:* PostgreSQL is fast, but eventually requires listen/notify or a real queue.
3. **LLM Hallucinations:** AI might invent rules. *Mitigation:* Evidence validation (`validate_findings`) grounds findings to RAG chunks.

==================================================
## PART 33 — FINAL ONE-PAGE CHEAT SHEET
=======================================
**PRODUCT:** AI PR Reviewer with Human-in-the-loop approval.
**FRONTEND:** React/Vite.
**BACKEND:** FastAPI, strictly REST.
**DATABASE:** PostgreSQL + pgvector.
**WORKER:** DB-backed Python polling script (`worker.py`).
**GITHUB:** OAuth PATs used for API. Webhooks used for triggers.
**AUTH:** Email/password + JWT HTTP-only cookies.
**RBAC:** `org_admin`, `team_lead`, `reviewer`, `developer`.
**RAG:** Local chunker + embeddings + pgvector.
**LLM:** Prompt-isolated calls producing structured JSON.
**HUMAN REVIEW:** AI finds issues; Human approves/requests changes.

**10 Questions a Senior Developer Will Ask:**
1. *How does the worker scale?* `SELECT FOR UPDATE SKIP LOCKED`.
2. *Is AI prompt injection possible?* Mitigated by keeping PR content strictly in `user_content`.
3. *Where are tokens stored?* `github_credential` table, encrypted via Fernet.
4. *How are webhooks secured?* HMAC SHA-256 against `GITHUB_WEBHOOK_SECRET`.
5. *Can I auto-merge?* Yes, if the `ProjectMergePolicy` allows it and `expected_head_sha` matches.
6. *Why no Celery?* To keep deployment simple; Postgres handles queues well at this scale.
7. *How are findings tracked across commits?* `_persist_validated_findings` calculates `lifecycle_status` (new/persistent/resolved).
8. *What if the LLM fails?* Retries once, then fails the `ReviewRun`.
9. *How does RBAC work?* Server-side `require_org_permission` middleware.
10. *Can one org see another's code?* No, `repository_id` is strictly scoped to the `Project` -> `Organization` hierarchy.

**10 Questions a Manager Will Ask:**
1. *Does it replace reviewers?* No, it augments them. Humans still click "Approve".
2. *Can it merge code automatically?* Only if you explicitly enable auto-merge policies and human approvals are met.
3. *Is our code safe?* Yes, tokens are encrypted and tenant data is logically isolated.
4. *What happens if GitHub goes down?* Automation actions fail and stay `PENDING`/`FAILED` for later retry.
5. *How do users log in?* Email/password.
6. *Does it work with GitLab?* No, GitHub only.
7. *What if a PR is huge?* It is safely truncated to avoid breaking the AI limit.
8. *How do I invite users?* Generate a token and send them a link manually.
9. *What roles exist?* Developer, Reviewer, Team Lead, Org Admin.
10. *Why is it better than standard linters?* It uses RAG to understand your whole architecture, not just syntax.

### Interview/Meeting Pitch (2-3 mins)
"RepoMind is an automated pull request reviewer that sits between your developers and GitHub. When a developer opens a PR, GitHub sends us a webhook. Our DB-backed worker picks it up, uses RAG to fetch relevant context from your existing codebase, and asks an LLM to find bugs, security risks, and architectural conflicts. It saves these findings to our database. Crucially, the AI *never* posts directly to GitHub or merges code. Instead, a Team Lead logs into our React UI, reviews the AI findings, and clicks 'Approve' or 'Request Changes'. Our backend then uses that Team Lead's own linked GitHub credential to post the real review back to GitHub. This guarantees a human is always in the loop, while saving them hours of reading boilerplate code. We built it purely on FastAPI and PostgreSQL, keeping deployment incredibly simple and secure."
