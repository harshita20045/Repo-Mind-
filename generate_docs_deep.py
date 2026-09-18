import os

out_dir = 'docs/code-flow'
os.makedirs(out_dir, exist_ok=True)

files_content = {
    '00_project_map.md': '''# Project Map
| Directory | Purpose | Important Files | Called By |
| --- | --- | --- | --- |
| `backend/app/auth` | Authentication & RBAC | `routes.py`, `service.py`, `models.py` | Frontend via API |
| `backend/app/rag` | Repository Indexing & Querying | `retriever.py`, `chunker.py`, `embedder.py` | Chat, Review, Worker |
| `backend/app/review` | Core AI Review Pipeline | `router.py`, `provider.py`, `evidence.py` | Worker, Frontend |
| `worker` | Background Processing | `worker.py` | Triggered by DB jobs |
| `frontend/src` | React UI | `App.jsx`, `api.js` | User Browser |
''',

    '01_application_startup.md': '''# Application Startup
1. **Where does it START?** `start_backend.bat` -> `uvicorn backend.app.main:app`
2. **Which function is called FIRST?** `main.py` -> `FastAPI(...)` app initialization.
3. **What does that function call NEXT?** `app.add_middleware(CORSMiddleware)` and `app.include_router(auth_router)`.
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Binds `Depends(get_db)` to routes which yields SQLAlchemy session.
5. **Where does the RESULT go?** Opens port 8000.
''',

    '02_configuration_flow.md': '''# Configuration Flow
1. **Where does it START?** `.env`
2. **Which function is called FIRST?** `backend/app/core/config.py:Settings` loads Pydantic `BaseSettings`.
3. **What does that function call NEXT?** Services import `settings` (e.g. `settings.JWT_SECRET`).
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Configures `POSTGRES_URL`, `GEMINI_API_KEY`.
5. **Where does the RESULT go?** Stored in memory as `settings` singleton.
''',

    '03_database_flow.md': '''# Database Initialization
1. **Where does it START?** `backend/app/db.py`
2. **Which function is called FIRST?** `create_engine(settings.POSTGRES_URL)`
3. **What does that function call NEXT?** `sessionmaker(bind=engine)`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** PostgreSQL.
5. **Where does the RESULT go?** `get_db()` yields session to FastAPI dependencies.
''',

    '04_model_cheat_sheet.md': '''# Model Cheat Sheet
- **User**: Identity. Read by auth routes. Created by bootstrap.
- **Organization**: Top tenant.
- **Repository**: Stores GitHub link. Read by Indexer.
- **DocumentChunk**: Stores RAG text & `VECTOR(384)`.
- **ReviewRun**: State machine for PR reviews.
''',

    '05_backend_request_flow.md': '''# Backend Request Flow
1. **Where does it START?** Browser HTTP POST.
2. **Which function is called FIRST?** FastAPI router.
3. **What does that function call NEXT?** `Depends(get_current_user)` -> Service Function.
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Query DB model.
5. **Where does the RESULT go?** Pydantic response -> JSON to Browser.
''',

    '06_authentication_code_flow.md': '''# Authentication Flow
1. **Where does it START?** `frontend/src/components/LoginForm.jsx`
2. **Which function is called FIRST?** `backend/app/auth/routes.py:login()`
3. **What does that function call NEXT?** `service.py:authenticate_user()` -> `verify_password()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** PostgreSQL `User` model.
5. **Where does the RESULT go?** `set_session_cookie()` sets 12-hour HttpOnly JWT cookie.
''',

    '08_github_flow.md': '''# GitHub Connection
1. **Where does it START?** `RepositoriesPage.jsx`
2. **Which function is called FIRST?** `github/routes.py:connect_repository()`
3. **What does that function call NEXT?** `github/service.py:connect_repository()` -> `get_decrypted_pat_for_org()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** GitHub API -> DB `Repository`.
5. **Where does the RESULT go?** Triggers `INDEX_REPOSITORY` job.
''',

    '09_repository_indexing_flow.md': '''# Indexing Flow
1. **Where does it START?** `worker.py` picks `INDEX_REPOSITORY` job.
2. **Which function is called FIRST?** `rag/repository.py:index_repository()`
3. **What does that function call NEXT?** `rag/chunker.py:chunk_text()` -> `rag/embedder.py:embed_chunks()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** SentenceTransformers (local) -> pgvector `DocumentChunk`.
5. **Where does the RESULT go?** Updates `index_status` to COMPLETED.
''',

    '11_rag_code_flow.md': '''# RAG Retrieval
1. **Where does it START?** `chat/service.py` or `review/provider.py`.
2. **Which function is called FIRST?** `rag/retriever.py:search()`
3. **What does that function call NEXT?** `embedder.py:embed_chunks()` for query.
4. **What DATABASE/EXTERNAL SERVICE does it touch?** pgvector `<->` operator `WHERE repository_id = X`.
5. **Where does the RESULT go?** Returns text chunks to Gemini prompt.
''',

    '12_chat_complete_flow.md': '''# Chat Flow
1. **Where does it START?** `ChatAssistant.jsx` -> `POST /chat`
2. **Which function is called FIRST?** `chat/routes.py:post_chat_message()`
3. **What does that function call NEXT?** `chat/service.py:send_message()` -> `retriever.py:search()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Gemini API, DB `ChatMessage`.
5. **Where does the RESULT go?** React UI Chat history.
''',

    '14_ai_pr_review_flow.md': '''# PR Review Pipeline
1. **Where does it START?** `worker.py` picks `REVIEW_PR` job.
2. **Which function is called FIRST?** `review/provider.py:execute_review()`
3. **What does that function call NEXT?** `retriever.py:search()` (RAG), `conflicts/engine.py:detect()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Gemini API.
5. **Where does the RESULT go?** `evidence.py` validation -> `Finding` models -> UI.
''',

    '18_evidence_validation_flow.md': '''# Evidence Validation
1. **Where does it START?** `review/provider.py` post-Gemini processing.
2. **Which function is called FIRST?** `review/evidence.py:validate_finding()`
3. **What does that function call NEXT?** Regex source extraction against `retriever.py` results.
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Local RAG text chunks.
5. **Where does the RESULT go?** Tags `Finding` as SUPPORTED/UNVERIFIED/CONTRADICTED.
''',

    '19_risk_analysis_flow.md': '''# Risk Analysis
1. **Where does it START?** End of `execute_review()`.
2. **Which function is called FIRST?** `risk/engine.py:calculate_risk()`
3. **What does that function call NEXT?** Aggregates severities from `Finding` array.
4. **What DATABASE/EXTERNAL SERVICE does it touch?** DB `RiskAssessment`.
5. **Where does the RESULT go?** Review UI Dashboard.
''',

    '23_worker_job_flow.md': '''# Worker System
1. **Where does it START?** `worker/worker.py` infinite loop.
2. **Which function is called FIRST?** `SELECT * FROM jobs WHERE status='PENDING' FOR UPDATE SKIP LOCKED`
3. **What does that function call NEXT?** `process_job()`
4. **What DATABASE/EXTERNAL SERVICE does it touch?** Runs AI/RAG/GitHub logic.
5. **Where does the RESULT go?** `UPDATE jobs SET status='COMPLETED'`.
''',

    '27_security_code_flow.md': '''# Security Flow
- **Authentication**: `auth/service.py:verify_password()` (bcrypt).
- **Session**: `JWT_EXPIRATION_HOURS=12`. Stored in HttpOnly cookie.
- **RBAC**: `require_role(RoleEnum)` dependency checks `OrganizationMembership`.
- **RAG Isolation**: Strict `repository_id` WHERE clause in pgvector SQL queries.
''',

    '30_where_everything_happens.md': '''# Where Everything Happens
| Feature | Entry Point | Main Files | Main Functions |
| --- | --- | --- | --- |
| Auth | `/auth/login` | `auth/routes.py` | `login()` |
| Indexing | Worker | `rag/repository.py` | `index_repository()` |
| Chat | `/chat` | `chat/service.py` | `send_message()` |
| PR Review | Worker | `review/provider.py` | `execute_review()` |
''',

    '34_feature_status.md': '''# Feature Status
- **Auth**: RUNTIME VERIFIED
- **RAG Indexing**: RUNTIME VERIFIED
- **Chat**: RUNTIME VERIFIED
- **Worker**: RUNTIME VERIFIED
- **ML Training**: NOT IMPLEMENTED
''',

    '35_manager_explanation.md': '''# Manager Explanation
RepoMind 2.0 uses a Fast/Slow architecture. Fast API routes handle the UI, but heavy tasks (AI, Indexing) are offloaded to a background worker.
It chunks GitHub code into a pgvector database to perform RAG. This context is fed to Gemini to find PR risks and semantic conflicts, while an Evidence Engine prevents AI hallucinations.
''',

    '36_developer_learning_guide.md': '''# Developer Learning Guide
1. Start with `start_backend.bat` and `main.py` to see FastAPI initialization.
2. Read `auth/routes.py` to see how JWTs are issued.
3. Read `worker/worker.py` to see how jobs are picked.
4. Read `review/provider.py` to see the core PR pipeline.
'''
}

for filename, content in files_content.items():
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

print(f"Generated {len(files_content)} specific code-flow files.")
