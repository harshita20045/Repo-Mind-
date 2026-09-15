# RepoMind 2.0 — Deployment Guide (No Docker)

**Status: Completed**

## Why No Docker

RepoMind 2.0 is designed to run natively on bare-metal or VMs. The project strictly excludes Docker to simplify the operational footprint for internal engineering teams that want to host the tool directly on an internal VM.

## Components to Deploy

1. **PostgreSQL (with `pgvector` extension)** — native install.
2. **FastAPI backend** — Python virtual environment, run via `uvicorn`/`gunicorn`.
3. **Background worker** — Python process, same virtual environment as the backend.
4. **React frontend** — built as static assets, served via a static file server or reverse proxy.

## Frontend Build

```bash
cd frontend
npm install
npm run build
```
Serve the resulting static build via Nginx, Caddy, or any static file server configured to proxy `/api` requests to the backend.

## Backend Deployment (Python Environment)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
alembic upgrade head
```
Run the API server with a production ASGI setup, e.g.:
```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
```

## Worker Runtime

Run the asynchronous task queue worker as a long-lived background process:
```bash
source .venv/bin/activate
python -m backend.app.worker.main
```

## PostgreSQL (Native)

Install PostgreSQL on the target host and install the `pgvector` extension.
```sql
CREATE DATABASE repomind;
\c repomind
CREATE EXTENSION IF NOT EXISTS vector;
```

## Environment Variables

Provide the following environment variables (e.g. via systemd `EnvironmentFile` or an `.env` file):
- `POSTGRES_URL`: Connection string for PostgreSQL
- `GEMINI_API_KEY`: API key for Google Gemini
- `LLM_PROVIDER`: `gemini`
- `JWT_SECRET`: Secret for session tokens

## Process Management

A reasonable native option: `systemd` unit files for the backend and worker processes, each with automatic restart on failure, running under a non-root service user.

## HTTPS / Reverse Proxy

If the deployment host is directly internet- or intranet-facing, a reverse proxy (e.g. nginx or Caddy) should terminate TLS and route `/api/*` to the backend and everything else to the built frontend static assets.

## Deployment Validation

After deploying:
1. `GET /api/health` (or equivalent) returns `200`.
2. `alembic upgrade head` shows the database at the latest migration.
3. The worker process is running and polling the `job` table.
4. A test repository connection + review completes successfully end-to-end.
