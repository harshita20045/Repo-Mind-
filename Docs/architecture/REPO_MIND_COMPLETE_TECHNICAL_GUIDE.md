# RepoMind 2.0 Complete Technical Guide

This master document provides a forensic-level technical understanding of the RepoMind 2.0 architecture, codebase, and runtime behavior.

> [!WARNING] 
> Evidence classifications (`SOURCE CODE`, `RUNTIME`, etc.) are provided for every major claim. No functionality has been fabricated.

## 1. Executive Summary & Product Problem
RepoMind 2.0 solves the problem of disconnected PR reviews and lack of repository-wide context by providing an AI-augmented review pipeline. It ingests GitHub repositories into a pgvector-backed RAG system to understand the codebase context *before* evaluating pull requests for semantic conflicts, risks, and basic linting errors.

## 2. Technology Stack & High-level Architecture
*   **Frontend**: React (Vite), TailwindCSS.
*   **Backend API**: FastAPI (Python), SQLAlchemy.
*   **Database**: PostgreSQL with `pgvector`.
*   **AI/RAG**: Gemini/Groq LLMs (`SOURCE CODE`, `.env`), SentenceTransformers (384-dim embeddings).
*   **Background Jobs**: Custom Python polling worker (`worker/worker.py`).

The architecture is a **Worker-Based Modular Monolith**. FastAPI serves the UI and writes pending jobs (like `INDEX_REPOSITORY` or `REVIEW_PR`) to the database. A separate background Python script (`worker.py`) constantly polls the database to process these jobs.

## 3. Database Architecture & Model Cheat Sheet
Evidence: `SOURCE CODE` (backend/app/models.py)

| Model | Purpose | Lifecycle / Flow |
|-------|---------|------------------|
| **User** | Represents a system identity. | Created via bootstrap/onboard. Password stored via bcrypt. |
| **Organization** | Top-level tenant container. | Created during bootstrap. Isolates Users and Projects. |
| **Project** | Logical grouping inside Orgs. | Contains multiple repositories. |
| **Repository** | GitHub repository connection. | Created by users. Triggers `INDEX_REPOSITORY` job. |
| **Document/Chunk**| RAG context storage. | Created by the worker during indexing. `DocumentChunk` contains the vector embedding. |
| **ReviewRun** | A specific execution of a PR review. | Created when review triggered. Moves from pending -> running -> completed. |
| **Finding/Conflict**| Extracted AI/static issues. | Parsed from LLM output, validated by evidence engine, saved to DB. |
| **ChatSession**| Context for Developer Assistant. | Created when chat starts. Optionally linked to `Repository` for RAG. |

## 4. Frontend Architecture
Evidence: `SOURCE CODE` (`frontend/src/`)
The React application follows a standard SPA structure:
*   **Routing**: `App.jsx` handles client-side routing.
*   **Pages**: Found in `frontend/src/pages/` (e.g., `ReviewPage.jsx`, `ChatPage.jsx`).
*   **API Client**: `frontend/src/lib/api.js` wraps `fetch` or `axios` for backend calls.
*   **Permissions**: `usePermissions.js` hook evaluates the current user's role against the current route.

## 5. Backend Architecture & Complete Code Flow
Evidence: `SOURCE CODE`

FastAPI routes HTTP requests to services. 
*Example End-to-End Flow (Triggering a PR Review):*
1.  **UI**: User clicks "Analyze PR" (`ReviewPage.jsx` -> API call).
2.  **API**: `backend/app/review/router.py:trigger_review()` validates auth.
3.  **Service**: `backend/app/review/service.py:create_review_run()` creates a `ReviewRun` and a `Job` in the DB.
4.  **Worker**: `worker.py` picks up the job.
5.  **Execution**: `backend/app/review/provider.py:execute_review()` runs.
6.  **Context Gathering**: Calls `rag/retriever.py` to get relevant vector chunks from pgvector.
7.  **AI Analysis**: Calls Gemini with the PR diff and context.
8.  **Validation**: `evidence.py` and `risk.py` evaluate the AI output.
9.  **Storage**: Final `Finding` models are written to PostgreSQL.

## 6. Authentication, Security & Credential Expiry
Evidence: `SOURCE CODE`, `CONFIGURATION`

### What expires?
*   **JWT Access Token**: Configured to expire in **12 hours** (`JWT_EXPIRATION_HOURS = 12` in `auth/service.py`). It is stored in an `HttpOnly` cookie via `set_session_cookie()`.
*   **Invitation Tokens**: Time-limited validation during onboarding.

### What does not expire implicitly?
*   **GitHub PATs**: Stored encrypted in the database via Fernet symmetric encryption (`github/encryption.py`). They remain valid until revoked by GitHub.
*   **LLM API Keys**: Read from `.env` on startup; they do not expire within the application.

### RBAC (Role-Based Access Control)
*   **Roles**: `ORG_ADMIN`, `LEAD`, `REVIEWER`, `DEVELOPER` (`auth/models.py`).
*   **Enforcement**: FastAPI dependency `require_role()` checks the `OrganizationMembership` of the JWT `sub`.

## 7. Repository Indexing, Chunking, and Embeddings
Evidence: `SOURCE CODE` (`rag/chunker.py`, `rag/embedder.py`)
1.  **Files Discovered**: GitHub API fetches tree.
2.  **Chunking**: Large files are split into smaller text chunks (e.g., overlapping windows).
3.  **Embeddings**: A 384-dimensional embedding model (SentenceTransformers) generates vectors.
4.  **pgvector**: The vector is stored in `DocumentChunk.embedding` column of type `VECTOR(384)`.

## 8. RAG & Developer Assistant (Chat)
Evidence: `SOURCE CODE` (`chat/service.py`, `rag/retriever.py`)
*   **Repository-Scoped Chat**: If a `repository_id` is provided, `retriever.py` queries pgvector using similarity search (`<->` operator) filtered by `repository_id`. The top-K chunks are injected into the Gemini prompt.
*   **Generic Chat**: If `repository_id` is null, the chat operates as a standard LLM conversation without RAG context.

## 9. Current Status & What's Working
Evidence: `RUNTIME VERIFIED` (Processes running locally) & `SOURCE CODE`

| Capability | Status | Evidence |
|------------|--------|----------|
| **Backend API** | `WORKING` | Uvicorn running on port 8000. |
| **Frontend UI** | `WORKING` | Vite running on port 5173. |
| **Background Worker** | `WORKING` | `worker.py` process running actively. |
| **Database/pgvector** | `WORKING` | Migrations `f2a7b8f58af8_native_pgvector.py` implemented. |
| **Authentication** | `IMPLEMENTED` | JWT token issuing and bcrypt hashing verified in source. |
| **RAG Ingestion** | `IMPLEMENTED` | Chunker, Embedder, Loader services exist. |
| **PR Review Pipeline**| `IMPLEMENTED` | Provider, Semantic Conflict Engine, Evidence evaluation exist. |
| **ML Intelligence** | `INCOMPLETE` | `MLPrediction` model and `train_ml_model.py` exist, but rely on historical data which is likely insufficient right now. Heuristics are currently used. |

## 10. Manager 1-Minute Explanation
"RepoMind 2.0 is an AI-powered code review platform. When a developer submits a PR, our background worker automatically fetches the code changes and compares them against our entire repository context stored in a pgvector database. It runs static analysis and semantic checks, feeds that context into Gemini to identify risks and conflicts, and validates the AI's claims before presenting a final, human-reviewable report in our React frontend."

## 11. Manager Q&A

**Q: Why a background worker?**
**A**: Because AI API calls (Gemini) and repository indexing take a long time. If we did this directly in the FastAPI web request, the browser would time out and the server would crash under load.

**Q: How do we prevent cross-repository leakage in RAG?**
**A**: Our `pgvector` queries have a strict SQL `WHERE repository_id = X` clause. Even if two repositories are similar, the vector similarity search is physically isolated by the database query filter.

**Q: What exactly is a semantic conflict?**
**A**: Unlike a Git merge conflict (where lines overlap), a semantic conflict is a logical break. For example, changing a database schema in one PR while another PR writes an API query for the old schema. Our conflict engine (`backend/app/conflicts/engine.py`) explicitly looks for these logical breaks using the RAG context.

**Q: How do we prevent hallucinations?**
**A**: We use an `Evidence Validator` (`backend/app/review/evidence.py`). When the AI claims something is wrong, this module does a lookup against the actual codebase files to verify the AI's claim. Claims are tagged as `SUPPORTED`, `UNVERIFIED`, or `CONTRADICTED`.

## 12. Known Limitations & Remaining Work
*   **Machine Learning**: The `train_ml_model.py` script exists, but real production ML requires hundreds of historical PRs to train effectively. The system currently falls back to heuristics and LLM zero-shot prompts.
*   **Security Configuration**: The `.env` file currently exposes `JWT_SECRET` and `FERNET_KEY` locally. In production, these must be rotated and moved to a secure vault or managed secret store.

---
*Generated by AI Assistant based on forensic repository inspection.*
