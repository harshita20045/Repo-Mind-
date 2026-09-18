# RepoMind 2.0 Complete Project Map

This document outlines the complete directory structure and architectural responsibilities of the RepoMind 2.0 project, based on actual repository inspection.

## Repository Hierarchy

```text
RepoMind 2.0
│
├── backend/                  # FastAPI Application
│   ├── alembic/              # Database Migrations
│   ├── app/                  # Main Backend Code
│   │   ├── analytics/        # Analytics & Metrics
│   │   ├── audit/            # Audit Logging Models
│   │   ├── auth/             # Authentication & RBAC
│   │   ├── chat/             # Developer Assistant (Gemini)
│   │   ├── conflicts/        # Semantic Conflict Engine
│   │   ├── core/             # Configuration & Settings
│   │   ├── github/           # GitHub API Integration
│   │   ├── linter/           # Static Analysis Integration
│   │   ├── ml/               # Machine Learning pipelines
│   │   ├── organizations/    # Organization & Project Management
│   │   ├── rag/              # Ingestion, Chunking, Embeddings, Retrieval
│   │   ├── review/           # PR Review Pipeline & Evidence Validation
│   │   ├── risk/             # Risk Assessment Engine
│   │   ├── routes/           # Miscellaneous/Health Routes
│   │   └── webhooks/         # Webhook Handling
│   ├── scripts/              # Setup, Seed, Verify scripts
│   └── tests/                # Backend Pytest Suite
│
├── frontend/                 # React SPA (Vite)
│   ├── src/                  # Main Frontend Code
│   │   ├── components/       # Reusable React UI Components
│   │   ├── hooks/            # Custom React Hooks (usePermissions)
│   │   ├── lib/              # API Client setup (api.js)
│   │   ├── pages/            # Top-level Route Components
│   │   └── styles/           # Global CSS and Design Tokens
│   └── tests/                # Frontend Test Suite
│
├── worker/                   # Background Job Processor
│   └── worker.py             # Main asynchronous polling worker
│
└── Docs/                     # Documentation (Legacy & Current)
    ├── 01-project/           # Project specifications
    ├── 02-architecture/      # Architecture designs and diagrams
    ├── 05-security/          # Security documentation
    ├── audit/                # Gap matrices and role audit reports
    └── architecture/         # Current RepoMind 2.0 documentation output
```

## Directory Deep Dive

### 1. `backend/app/`
- **Purpose**: Houses the FastAPI web server logic, services, database models, and API routers.
- **Important files**: `main.py` (entrypoint), `db.py` (database connection).
- **Responsibility**: Serves REST API requests from the frontend and manages synchronous data operations (DB reads/writes).
- **Dependencies**: PostgreSQL, GitHub API, Gemini API.
- **Consumers**: React Frontend, Worker (via DB state).
- **Runtime role**: Synchronous HTTP request processing, Authentication, Authorization enforcement.

### 2. `backend/app/auth/`
- **Purpose**: Handles user identity, JWT session management, and RBAC enforcement.
- **Important files**: `routes.py`, `service.py`, `models.py`, `dependencies.py`, `permissions.py`.
- **Responsibility**: Password verification, token issuance, route-level permission checking (`ORG_ADMIN`, `LEAD`, `REVIEWER`, `DEVELOPER`).
- **Dependencies**: Database `User` model, JWT Secret.
- **Consumers**: All protected FastAPI endpoints.

### 3. `backend/app/rag/`
- **Purpose**: The Retrieval-Augmented Generation core for repository context.
- **Important files**: `chunker.py`, `embedder.py`, `loader.py`, `retriever.py`, `models.py`.
- **Responsibility**: Fetching GitHub files, chunking them, generating embeddings (384-dim), and querying pgvector for relevant context.
- **Dependencies**: `github/` module, SentenceTransformers/Gemini embeddings, pgvector.
- **Consumers**: `review/` pipeline, `chat/` API.

### 4. `backend/app/review/`
- **Purpose**: The core AI Pull Request Review engine.
- **Important files**: `provider.py`, `service.py`, `evidence.py`, `context.py`, `router.py`.
- **Responsibility**: Coordinates PR context gathering, prompting Gemini, validating AI claims, and saving the review report.
- **Dependencies**: `rag/` (context), `github/` (diffs), `conflicts/`, `risk/`.
- **Consumers**: Frontend Review UI, Background Worker.

### 5. `backend/alembic/`
- **Purpose**: SQLAlchemy database migration system.
- **Important files**: `env.py`, `versions/*.py`.
- **Responsibility**: Managing incremental database schema changes, adding pgvector, applying role enums.
- **Dependencies**: SQLAlchemy, psycopg2.
- **Runtime role**: Executes sequentially during backend startup or deployment (`alembic upgrade head`).

### 6. `frontend/src/`
- **Purpose**: React + Vite single-page application.
- **Important files**: `App.jsx`, `main.jsx`, `lib/api.js`.
- **Responsibility**: Providing the user interface for repo management, chat, and PR review visualization.
- **Dependencies**: React, Vite, React Router, TailwindCSS.
- **Consumers**: End Users.
- **Runtime role**: Runs in the user's browser, communicates asynchronously with `backend/`.

### 7. `worker/`
- **Purpose**: Asynchronous background task execution.
- **Important files**: `worker.py`.
- **Responsibility**: Polling the database for pending jobs (Indexing, PR Review), locking them, executing long-running tasks, and updating statuses.
- **Dependencies**: Database (Job, ReviewRun models), `backend/app` services.
- **Consumers**: `backend/` creates jobs for it.
- **Runtime role**: Runs as a separate daemon/process (`start_worker.bat`), ensuring the API remains non-blocking during 10+ second Gemini calls or massive repo indexing.

### 8. `backend/scripts/` & `backend/tests/`
- **Purpose**: Tooling and Quality Assurance.
- **Important files**: `seed_dev_db.py`, `verify_db.py`, `test_rag.py`, `test_review.py`.
- **Responsibility**: Validating component behavior, seeding local dev environments.
- **Runtime role**: Executed manually or in CI; not active in the production runtime path.
