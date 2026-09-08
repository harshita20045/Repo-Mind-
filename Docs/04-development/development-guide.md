# RepoMind — Development Guide

**Status: Confirmed** (native, non-Docker setup — see `01-project/scope.md`, ADR-014)

This guide describes how to run RepoMind locally **without Docker**. Where the source materials specified Docker Compose commands, the equivalent native command is used instead.

## Required Software

- Node.js (LTS) + npm, for the React frontend.
- Python 3.11+, for the FastAPI backend, background worker, and ML scripts.
- PostgreSQL (with the ability to install the `pgvector` extension), installed natively on the development machine.
- `git`.

## Repository Layout

See `04-development/coding-standards.md` and the folder structure below (adapted from the Implementation Blueprint, Part 22, with `infrastructure/docker-compose.yml` removed per the no-Docker decision):

```
repomind/
├── frontend/
│   ├── src/{pages,components,lib,hooks,types}/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── main.py, config.py, dependencies.py
│   │   └── auth/  organizations/  github/  rag/  review/  linter/  ml/  evaluation/  feedback/  audit/  common/
│   └── tests/
├── worker/
│   └── jobs/{index_repository.py, review_pr.py, run_evaluation.py}
├── database/
│   └── migrations/  (001_...  through  010_...)
├── docs/
│   ├── architecture.md  setup.md  api.md  ai-pipeline.md  rag.md  evaluation.md  deployment.md  security.md
│   └── adr/
├── scripts/
│   ├── seed_demo_data.py
│   ├── run_evaluation.py
│   └── train_ml_models.py
├── .env.example
├── .gitignore
└── README.md
```

## PostgreSQL Setup (Native)

1. Install PostgreSQL locally (e.g. via your OS package manager).
2. Create a database and enable the `pgvector` extension:
   ```sql
   CREATE DATABASE repomind;
   \c repomind
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
3. Note the connection string for use in `.env` (see `07-deployment/environment-configuration.md`).

## Backend Setup (Python / FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Environment Variables

Copy `.env.example` to `.env` and fill in required values (database URL, `GITHUB_TOKEN`, LLM API key, session secret). See `07-deployment/environment-configuration.md` for the full variable table. Never commit `.env`.

## Database Initialization and Migrations

```bash
cd backend
alembic upgrade head
```
See `07-deployment/database-migrations.md` for the full migration workflow.

## Running the Backend

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```
Verify with: `curl http://localhost:8000/health` → expects `200`.

## Running the Background Worker

```bash
cd worker
source ../backend/.venv/bin/activate   # reuse the backend venv, or create a dedicated one
python -m worker.main
```
The worker polls the `job` table (see `03-design/database-design.md`) and executes repository indexing, PR review, and evaluation jobs.

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
The dev server proxies API requests to the backend at `http://localhost:8000` (configure the proxy target via the frontend's own `.env`/config, per `07-deployment/environment-configuration.md`).

## Running ML Training Scripts

```bash
cd backend
source .venv/bin/activate
python ../scripts/train_ml_models.py
```
Produces versioned `.pkl` model files consumed synchronously by the `ml` module (see `02-architecture/diagrams/ml-pipeline.md`).

## Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest

# Frontend
cd frontend && npm test
```
See `06-testing/testing-strategy.md` for the full test pyramid, including the AI-evaluation regression suite.

## Linting and Formatting

- **Backend:** `ruff check backend/` and `ruff format backend/` (the same tool used for repository static analysis in the product itself — see `04-development/coding-standards.md`).
- **Frontend:** the project's configured ESLint/Prettier setup (exact configuration is an implementation detail not specified in the source materials — **Proposed**, follow standard React + TypeScript conventions until a project-specific config is confirmed).

## Running the Evaluation Script

```bash
cd backend
source .venv/bin/activate
python ../scripts/run_evaluation.py
```
Runs the 3-way comparison (generic LLM / LLM+linter / LLM+linter+RAG) against the labeled answer-key test set and stores results in `evaluation_run`. See `02-architecture/diagrams/ai-review-pipeline.md`.

## No Docker

This project intentionally does not use Docker or Docker Compose for local development, per an explicit project-owner decision (see `01-project/scope.md`). All setup above uses native Python virtual environments, npm, and a natively-installed PostgreSQL instance.
