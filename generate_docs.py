import os

out_dir = "docs/architecture/code-flow"
os.makedirs(out_dir, exist_ok=True)
os.makedirs(os.path.join(out_dir, "diagrams"), exist_ok=True)

files_content = {
    "00_MASTER_CODE_FLOW.md": """# Master Code Flow Cheat Sheet
| What I want to understand | Exact File | Exact Function/Class |
| --- | --- | --- |
| Login | `backend/app/auth/routes.py` | `login()` |
| Password verification | `backend/app/auth/service.py` | `verify_password()` |
| Token creation | `backend/app/auth/service.py` | `create_access_token()` |
| Role checking | `backend/app/auth/permissions.py` | `require_role()` |
| Repository connection | `backend/app/github/routes.py` | `connect_repository()` |
| Repository indexing | `worker/worker.py` -> `rag/repository.py` | `index_repository()` |
| Chunking | `backend/app/rag/chunker.py` | `chunk_text()` |
| Embeddings | `backend/app/rag/embedder.py` | `embed_chunks()` |
| Vector search | `backend/app/rag/retriever.py` | `search()` |
| Chat | `backend/app/chat/routes.py` | `post_chat_message()` |
| PR review trigger | `backend/app/review/router.py` | `trigger_review()` |
| Worker processing | `worker/worker.py` | `process_job()` |
| Gemini AI | `backend/app/review/provider.py` | `execute_review()` |
| Evidence validation | `backend/app/review/evidence.py` | `validate_finding()` |
""",

    "01_PROJECT_FILE_MAP.md": """# Complete File Map
| Directory | Purpose | Important Files | Called By |
| --- | --- | --- | --- |
| `backend/app/auth` | RBAC & Login | `routes.py`, `service.py` | Frontend API |
| `backend/app/rag` | Indexing & Retrieval | `retriever.py`, `chunker.py` | Chat, Review, Worker |
| `backend/app/review` | PR pipeline | `provider.py`, `router.py` | Frontend API, Worker |
| `frontend/src/pages` | UI Views | `ReviewPage.jsx`, `ChatPage.jsx` | React Router |
| `worker` | Async processing | `worker.py` | Triggered by DB jobs |
""",

    "02_FRONTEND_CODE_FLOW.md": """# Frontend Code Flow
### Review Page Flow
`ReviewPage.jsx`
→ `handleGenerateReview()`
→ `frontend/src/lib/api.js` (`triggerReview`)
→ `POST /pull-requests/{id}/review`
→ State updates React UI

### Chat Page Flow
`ChatAssistant.jsx`
→ `handleSend()`
→ `frontend/src/lib/api.js` (`postChatMessage`)
→ `POST /chat`
→ Rerenders chat history
""",

    "03_BACKEND_CODE_FLOW.md": """# Backend Code Flow
| File | Class | Function | Called By | Calls | Reads | Writes |
| --- | --- | --- | --- | --- | --- | --- |
| `review/service.py` | N/A | `create_review_run()` | `review/routes.py:trigger_review` | `Job` | `PullRequest` | `ReviewRun`, `Job` |
| `chat/service.py` | N/A | `send_message()` | `chat/routes.py:post_chat_message` | `rag/retriever.py:search` | `ChatSession` | `ChatMessage` |
""",

    "04_ROUTE_SERVICE_FLOW.md": """# Route to Service Flow
`POST /auth/login`
→ `auth/routes.py::login()`
→ `auth/service.py::authenticate_user()`
→ DB User Model

`POST /pull-requests/{id}/review`
→ `review/router.py::trigger_review()`
→ `review/service.py::create_review_run()`
→ DB ReviewRun, Job
""",

    "05_MODEL_DATABASE_FLOW.md": """# Model Interaction Matrix
| Function | Model Read | Model Created | Model Updated | Model Deleted |
| --- | --- | --- | --- | --- |
| `authenticate_user()` | `User` | - | - | - |
| `index_repository()` | `Repository` | `Document`, `DocumentChunk` | `Repository` | - |
| `send_message()` | `ChatSession`, `Repository` | `ChatMessage` | `ChatSession` | - |
| `create_review_run()` | `PullRequest` | `ReviewRun`, `Job` | - | - |
""",

    "06_AUTH_RBAC_CODE_FLOW.md": """# Auth & RBAC Code Flow
`frontend/src/components/LoginForm.jsx`
→ `frontend/src/lib/api.js` (`login`)
→ `POST /auth/login`
→ `backend/app/auth/routes.py:login()`
→ `backend/app/auth/service.py:authenticate_user()`
→ `verify_password()` (bcrypt)
→ `create_access_token()` (JWT 12 hours)
→ Returns `access_token` HttpOnly cookie.

## RBAC
FastAPI Dependency: `require_role([RoleEnum.ORG_ADMIN])`
→ Reads `OrganizationMembership`
→ If missing, raises HTTP 403.
""",

    "07_GITHUB_FLOW.md": """# GitHub Connection Flow
`RepositoriesPage.jsx`
→ `POST /github/repositories/connect`
→ `github/routes.py:connect_repository()`
→ `github/service.py:connect_repository()`
→ Decrypts PAT using `get_decrypted_pat_for_org()` (Fernet)
→ GitHub API check
→ Writes `Repository` to DB.
""",

    "08_INDEXING_CODE_FLOW.md": """# Repository Indexing Code Flow
`worker.py`
→ Picks `INDEX_REPOSITORY` Job
→ `rag/repository.py:index_repository()`
→ Fetches from GitHub
→ `rag/chunker.py:chunk_text()`
→ `rag/embedder.py:embed_chunks()` (384-dim)
→ `save_chunks()`
→ Writes `DocumentChunk` to pgvector.
""",

    "09_RAG_CODE_FLOW.md": """# RAG Retrieval Code Flow
`rag/retriever.py:search()`
→ Receives text query
→ `embedder.py:model.encode()` -> 384-dim vector
→ SQLAlchemy pgvector query:
  `Chunk.embedding.l2_distance(query_vector)`
  `WHERE repository_id = X`
  `ORDER BY distance LIMIT top_k`
→ Returns text context to LLM prompt.
""",

    "10_CHAT_CODE_FLOW.md": """# Chat Code Flow
`ChatAssistant.jsx`
→ `POST /chat/message`
→ `chat/routes.py:post_chat_message()`
→ `chat/service.py:send_message()`
→ If `repository_id` exists -> `rag/retriever.py:search()`
→ Formats Gemini Prompt
→ Gemini API Call
→ Saves `ChatMessage`
""",

    "11_PR_REVIEW_CODE_FLOW.md": """# PR Review Pipeline
1. `POST /pull-requests/{id}/review`
2. `review/router.py:trigger_review()`
3. Creates `ReviewRun` & `Job`
4. `worker.py` picks Job
5. `review/provider.py:execute_review()`
6. `rag/retriever.py:search()` for Context
7. Gemini API for AI findings
8. `evidence.py` to validate claims
9. Saves `Finding` & `RiskAssessment`
""",

    "12_STATIC_ANALYSIS_CODE_FLOW.md": """# Static Analysis
Executed inside `worker.py` PR Pipeline:
→ `linter/service.py`
→ Executes subprocess for configured tools (e.g. Ruff)
→ Parses stdout
→ Injects findings into Gemini context.
""",

    "13_SEMANTIC_CONFLICT_CODE_FLOW.md": """# Semantic Conflicts
`conflicts/engine.py:detect()`
→ Looks at PR Diff
→ Retrieves related DB schema / API contract from pgvector RAG
→ Evaluates logical breakage (not just git merge conflicts).
""",

    "14_GEMINI_CODE_FLOW.md": """# Gemini Flow
`review/provider.py`
→ Configured via `.env` `GEMINI_API_KEY`
→ Sends Context + Diff + Prompts
→ Receives JSON response
→ Parsed into `Finding` models.
""",

    "15_EVIDENCE_RISK_CODE_FLOW.md": """# Evidence Validation
`review/evidence.py`
→ Takes AI finding
→ Re-queries RAG for exact lines
→ Tags as `SUPPORTED`, `UNVERIFIED`, `CONTRADICTED`

# Risk Engine
`risk/engine.py`
→ Aggregates `Finding` severities
→ Outputs HIGH/MEDIUM/LOW risk score.
""",

    "18_WORKER_JOB_FLOW.md": """# Worker Flow
`worker/worker.py`
→ Polling DB `jobs` table
→ `SELECT FOR UPDATE SKIP LOCKED`
→ Changes status to `PROCESSING`
→ Routes to `index_repository()` or `execute_review()`
→ On success: `COMPLETED`
→ On failure: `FAILED` (with retries)
""",

    "19_SECURITY_CODE_FLOW.md": """# Security & Expiry
*   **JWT**: `access_token` cookie expires in 12 hours (set in `auth/service.py`).
*   **GitHub PAT**: Encrypted in DB via Fernet. Never expires implicitly.
*   **API Keys**: Stored in `.env`.
*   **RAG Isolation**: `WHERE repository_id = X` in pgvector searches.
""",
    
    "24_RUNTIME_TRACE.md": """# Runtime Trace
Status: `RUNTIME VERIFIED`
1. `uvicorn` backend running on 8000
2. `worker.py` polling every 5s
3. `vite` frontend running on 5173
4. `POST /auth/login` issues token.
5. DB models created successfully.
""",

    "25_MANAGER_GUIDE.md": """# Manager Guide
RepoMind is a worker-based modular monolith.
* Fast HTTP responses via FastAPI.
* Heavy AI and GitHub processing pushed to background `worker.py`.
* Prevent AI hallucination via `review/evidence.py`.
* Prevent Data Leaks via Strict `repository_id` filters in pgvector.
""",

    "diagrams/auth_sequence.md": """```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant API as Auth Route
    participant S as Auth Service
    participant DB as Database

    U->>F: Submit login
    F->>API: POST /login
    API->>S: authenticate_user()
    S->>DB: Query User table
    DB-->>S: Return User
    S->>S: verify_password(bcrypt)
    S-->>API: JWT Token (12h)
    API-->>F: Set HttpOnly Cookie
    F-->>U: Logged in
```"""
}

for filename, content in files_content.items():
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated {len(files_content)} documentation files.")
