# Code Connection Map

This document traces the exact file and function connections for the major subsystems in RepoMind 2.0.
Evidence classification: `SOURCE CODE`

## 1. Login & Authentication Flow

**Frontend Trigger**
`frontend/src/pages/LoginPage.jsx` 
  -> `LoginForm.jsx` 
  -> `frontend/src/lib/api.js (login)`

**Backend Router**
`backend/app/auth/routes.py:login()`

**Service Layer**
`backend/app/auth/service.py:authenticate_user()`
  -> Reads `User` model (PostgreSQL) using `get_user_by_email`
  -> Verifies password via `verify_password()` (bcrypt)

**Output**
Returns `AuthResponse` and sets `access_token` JWT via `set_session_cookie()` in HttpOnly cookie.


## 2. RBAC Enforcement Flow

**Frontend Verification**
`frontend/src/hooks/usePermissions.js` checks decoded token or React Context state.

**Backend Protection**
FastAPI route dependency: `backend/app/auth/permissions.py:require_role(allowed_roles)`
  -> Depends on `get_current_user`
  -> Reads `OrganizationMembership` model
  -> Compares requested repo/project scope against `RoleEnum` (`ORG_ADMIN`, `LEAD`, `REVIEWER`, `DEVELOPER`)


## 3. Repository Indexing Flow

**Frontend Trigger**
`frontend/src/pages/RepositoriesPage.jsx`
  -> API call to `/github/repositories/{id}/index`

**Backend Router**
`backend/app/github/routes.py:trigger_indexing()`

**Service Layer**
`backend/app/github/service.py:queue_indexing_job()`
  -> Writes `Job` model (type=`INDEX_REPOSITORY`) to pending status.

**Worker Execution**
`worker/worker.py:process_job()`
  -> Calls `backend/app/rag/repository.py:index_repository()`
  -> External API: Fetches repo contents via GitHub API client.
  -> `backend/app/rag/chunker.py`: Splits files into text chunks.
  -> `backend/app/rag/embedder.py`: Converts text to vectors (384-dim).
  -> Writes `Document`, `Chunk`, `Embedding` to PostgreSQL (pgvector).


## 4. Chat & RAG Query Flow

**Frontend Trigger**
`frontend/src/components/Review/ChatAssistant.jsx`
  -> API call to `/chat`

**Backend Router**
`backend/app/chat/routes.py:send_message()`

**Service Layer**
`backend/app/chat/service.py:process_chat()`
  -> Resolves `ChatSession` context.
  -> Calls `backend/app/rag/retriever.py:retrieve_context()`
  -> Vector Search via pgvector `<->` operator on `Chunk` embeddings, scoped by `repository_id`.

**AI Call**
  -> Formats retrieved context into Gemini prompt.
  -> External API: Gemini API request.
  -> Writes `ChatMessage` to DB.


## 5. PR Review Pipeline

**Backend Trigger**
`backend/app/review/router.py:trigger_review()`
  -> `backend/app/review/service.py:create_review_run()`
  -> Writes `ReviewRun` and pending `Job`.

**Worker Execution**
`worker/worker.py` polling -> `backend/app/review/provider.py:execute_review()`

**Analysis Engines**
1. **RAG Context**: `backend/app/rag/retriever.py`
2. **Static Analysis**: `backend/app/linter/service.py` 
3. **Semantic Conflicts**: `backend/app/conflicts/engine.py`

**AI Evaluation**
  -> `backend/app/review/prompts.py` builds system instruction.
  -> Gemini API called with diff, context, and linter findings.

**Post-Processing**
  -> `backend/app/review/evidence.py`: Validates claims against repository context.
  -> `backend/app/risk/engine.py`: Computes risk score.
  -> Writes `ReviewResult` and `Finding` to DB.
