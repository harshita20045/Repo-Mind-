# RepoMind 2.0 Feature Code Flow Walkthroughs

This document traces the exact step-by-step code execution flow for major features, highlighting the relevant files, classes, and functions involved. 

## 1. Authentication & Bootstrapping Flow

### 1a. System Bootstrap (First-time setup)
When a user provisions the system for the first time:
1. **Frontend Call**: User submits org name, email, password, and the secret bootstrap token.
2. **Route Entry**: `backend/app/auth/routes.py:bootstrap()` receives `BootstrapRequest`.
3. **Logic Flow**: `backend/app/auth/service.py:bootstrap_system()` is invoked.
    * Validates `bootstrap_token` against `settings.BOOTSTRAP_TOKEN` (configured in `.env`).
    * Ensures the DB has 0 `User` records.
    * Hashes password via `hash_password()` using `bcrypt.hashpw`.
    * Creates `User` and `Organization`.
    * Creates `OrganizationMembership` linking the user to the organization with `RoleEnum.ORG_ADMIN`.
4. **Token Generation**: `create_access_token()` creates a JWT (HS256) valid for 12 hours.
5. **Response**: `set_session_cookie()` sets an `HttpOnly` cookie with the token. Returns `AuthResponse`.

### 1b. Standard Login
1. **Route Entry**: `backend/app/auth/routes.py:login()` receives `UserLogin`.
2. **Logic Flow**: `backend/app/auth/service.py:authenticate_user()`
    * Calls `get_user_by_email()`.
    * Verifies password using `verify_password()` and bcrypt.
3. **Session**: Generates JWT, sets `HttpOnly` cookie via `set_session_cookie()`.

---

## 2. GitHub Integration Flow (Repository Connection)

When a developer connects a GitHub repository:
1. **Frontend Call**: User provides Repository ID and GitHub Owner/Name.
2. **Route Entry**: `backend/app/github/routes.py:connect_repository()`.
    * Validates user has `ORG_ADMIN` or `LEAD` permission via `require_role`.
3. **Logic Flow**: `backend/app/github/service.py:connect_repository()`.
    * Fetches GitHub Personal Access Token (PAT) for the organization via `get_decrypted_pat_for_org()` (uses Fernet symmetric encryption from `github/encryption.py`).
    * Validates repository existence using the official GitHub REST API (using the decrypted token).
    * Saves `Repository` record to the database (attached to the `Project`).
4. **Next Step**: The UI typically prompts the user to trigger Indexing.

---

## 3. RAG Pipeline Flow (Repository Indexing, Chunking, Embedding)

When the RAG engine ingests a repository to understand context:

### 3a. Ingestion Trigger & Job Queue
1. **Trigger**: `backend/app/github/routes.py:trigger_indexing()` -> `service.py:queue_indexing_job()`.
2. **Job Queue**: A `Job` model is written to the DB with `type=INDEX_REPOSITORY`.
3. **Worker Processing**: The asynchronous `worker.py` daemon polls and locks this job.

### 3b. Fetch & Chunking
1. **Data Fetch**: Worker calls `backend/app/rag/repository.py:index_repository()`. It fetches all non-ignored text files from the GitHub API using the connected PAT.
2. **Document Save**: For each file, `backend/app/rag/repository.py:save_document()` creates a `Document` record.
3. **Chunking**: `backend/app/rag/chunker.py:chunk_text()` uses a sliding window text splitter to cut large code files into semantically meaningful chunks (e.g., 500 tokens with 50-token overlap).

### 3c. Embedding & Vector Storage
1. **Vectorization**: `backend/app/rag/embedder.py:embed_chunks()` passes the text chunks to a local `SentenceTransformers` model (`all-MiniLM-L6-v2`) which outputs a 384-dimensional float array.
2. **Vector DB Write**: `backend/app/rag/repository.py:save_chunks()` writes the text and the 384-dim vector to `DocumentChunk.embedding` (stored natively using PostgreSQL `pgvector`).

---

## 4. Chat Assistant Flow (RAG Query Time)

When a developer asks the AI a question about their code:
1. **Frontend Call**: Developer types a query in the Chat UI.
2. **Route Entry**: `backend/app/chat/routes.py:post_chat_message()`.
3. **Session Check**: `backend/app/chat/service.py:create_session()` if a session doesn't exist, followed by `send_message()`.
4. **Context Retrieval (RAG)**:
    * If `repository_id` is provided, `service.py` calls `backend/app/rag/retriever.py:search()`.
    * `search()` converts the user's question into a 384-dim query embedding using `rag/embedder.py`.
    * It executes a pgvector similarity search: `SELECT ... ORDER BY embedding <-> :query_embedding LIMIT 5`.
    * **Crucial Security**: The SQL query is explicitly filtered by `WHERE repository_id = :repo_id` to prevent cross-tenant data leakage.
5. **AI Generation**: The retrieved text chunks are formatted into the system prompt. The backend calls the LLM provider (Gemini or Groq, per `.env`).
6. **Storage & Response**: The prompt and AI response are saved as `ChatMessage` records and returned to the UI.
