# RepoMind — Deployment Guide (No Docker)

**Status: Proposed** (the source materials specify Docker Compose for local/staging/production deployment; this guide documents the project-owner's explicit native, non-Docker alternative — see `01-project/scope.md`, ADR-014. The overall shape — one host, no Kubernetes — is Confirmed; the specific process-manager choices below are Proposed defaults, not verbatim source-material instructions.)

## Why No Docker

The source materials (Architecture Blueprint, Implementation Blueprint) recommend Docker Compose for reproducibility and as the deployment mechanism across local/staging/production. The project owner has explicitly excluded Docker from this project. This guide replaces every Docker-based instruction with the equivalent native setup, consistent with the "one deploy target, one team, no independent-scaling need" architecture already established (see `02-architecture/architecture-decisions.md`, ADR-001).

## Components to Deploy

1. PostgreSQL (with `pgvector` extension) — native install.
2. FastAPI backend — Python virtual environment, run via `uvicorn`/`gunicorn`.
3. Background worker — Python process, same virtual environment as the backend.
4. React frontend — built as static assets, served via a static file server or reverse proxy.

## Frontend Build

```bash
cd frontend
npm install
npm run build
```
Serve the resulting static build (e.g. via nginx, Caddy, or any static file server / reverse proxy configured to also route API requests to the backend).

## Backend Deployment (Python Environment)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
```
Run the API server with a production ASGI setup, e.g.:
```bash
gunicorn app.main:app -k uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:8000
```

## Worker Runtime

```bash
cd worker
source ../backend/.venv/bin/activate
python -m worker.main
```
Run as a long-lived background process (see "Process Management" below).

## PostgreSQL (Native)

Install PostgreSQL on the target host and enable `pgvector`:
```sql
CREATE DATABASE repomind;
\c repomind
CREATE EXTENSION IF NOT EXISTS vector;
```
The source materials note that managed PostgreSQL is optional, to be adopted "once uptime matters more than cost" — this remains an **Open Decision** for production; a natively-installed instance on the deployment host is the confirmed baseline.

## AI/ML Runtime

The `rag`/`review`/`ml` modules run inside the backend and worker Python environment — no separate serving system. Ensure the sentence-transformers model and any ML `.pkl` model artifacts are present on the host (or downloaded/loaded at startup) before the worker begins processing jobs.

## Environment Variables

See `07-deployment/environment-configuration.md` for the full variable table. On a native (non-Docker) host, these are supplied via the process manager's environment configuration (e.g. a systemd `EnvironmentFile=`, or equivalent for your chosen process manager) — never a committed file.

## Process Management

Not specified by name in the source materials beyond "single small VM." A reasonable, low-complexity native option (Proposed): `systemd` unit files for the backend and worker processes, each with automatic restart on failure, running under a non-root service user. Equivalent tools (e.g. `supervisord`) are acceptable substitutes — the requirement is only "runs continuously, restarts on failure, no container runtime."

## HTTPS / Reverse Proxy

If the deployment host is directly internet- or intranet-facing, a reverse proxy (e.g. nginx or Caddy) terminates TLS and routes `/api/*` (or equivalent) to the backend and everything else to the built frontend static assets. Not detailed further in the source materials — **Proposed**, standard practice.

## Deployment Environments

- **Local:** developer machine, native processes (see `04-development/development-guide.md`).
- **Staging:** the same native stack on a single small VM, seeded with demo data via `scripts/seed_demo_data.py`, clearly separated from any real organization data via a `demo=true` flag on the seed organization — **never mixed with real org data**.
- **Production:** the same native stack on a managed VM or a single small host. **No Kubernetes** — no component in this architecture has an independent-scaling profile that justifies it.

## Deployment Validation

After deploying:
1. `GET /health` returns `200`.
2. `alembic upgrade head` (or equivalent migration-status check) shows the database at the latest migration.
3. The worker process is running and polling the `job` table.
4. A test repository connection + review completes successfully end-to-end.

## Rollback Approach

Not detailed in the source materials beyond the general principle of "no independent-scaling need, one deploy target." A reasonable native default (**Proposed**): keep the previous release's build/venv available on the host and redeploy it if the new release fails validation; database migrations should be written to be reversible where practical (`alembic downgrade`), and any migration that is not safely reversible should be called out explicitly in its migration file.
