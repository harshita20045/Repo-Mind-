# RepoMind — Operational Runbook

**Status: Confirmed** for the operations covered; procedures reflect the native (non-Docker) deployment in `07-deployment/deployment-guide.md`

## Start the Application

1. Confirm PostgreSQL is running and reachable (`DATABASE_URL`).
2. Start the backend: `uvicorn app.main:app` (dev) or via the configured process manager (production) — see `07-deployment/deployment-guide.md`.
3. Start the background worker: `python -m worker.main`, same environment.
4. Serve the built frontend (or run `npm run dev` locally).
5. Verify: `GET /health` returns `200`.

## Stop the Application

Stop the backend, worker, and frontend-serving processes via your process manager (e.g. `systemctl stop repomind-backend repomind-worker`, per the `07-deployment/deployment-guide.md` "Process Management" section — exact unit names are environment-specific).

## Restart Services

Restart the backend and/or worker independently — they are separate processes by design (see `02-architecture/system-architecture.md`), so restarting one does not require restarting the other. After restarting the worker, confirm it resumes polling the `job` table and picks up any `pending` jobs.

## Check Backend Health

```bash
curl http://<host>:8000/health
```
Expect `200`. If not, check backend process logs and `DATABASE_URL` connectivity (see `08-operations/troubleshooting.md`).

## Check Database

```bash
psql "$DATABASE_URL" -c "SELECT 1;"
psql "$DATABASE_URL" -c "SELECT extname FROM pg_extension WHERE extname = 'vector';"
```
Confirms connectivity and that `pgvector` is enabled.

## Run Migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```
See `07-deployment/database-migrations.md` for full detail, including rollback (`alembic downgrade`).

## Troubleshoot GitHub Integration

1. Check the most recent failed `job` of type related to GitHub fetch/indexing.
2. Confirm the organization's PAT is valid and correctly scoped (read-only, includes the target repository).
3. Check for rate-limit (403/429) vs. transient (5xx) vs. permission (403/404) errors in logs, per `08-operations/troubleshooting.md`.
4. Reconnect via `POST /repositories/connect` if the token needs to be reissued.

## Re-run a Review

Trigger `POST /pull-requests/{id}/review` again (via the UI's "Analyze"/re-analysis action, or directly against the API). This creates a new `job` and, if the PR was previously reviewed, produces a new `review_run` whose findings are reconciled (NEW/PERSISTENT/RESOLVED) against the prior run.

## Inspect Failed AI Processing

1. Find the failed `job` (status `failed`) and its associated `review_run` (status reflects the failure stage per the job state machine in `02-architecture/diagrams/pr-review-sequence.md`).
2. If the failure was "invalid JSON after retry," the raw LLM output is logged (time-boxed retention, see `05-security/security.md`) — inspect it to determine whether the issue is a prompt/schema problem.
3. If the failure was a GitHub or LLM timeout/error, confirm whether it was transient (retry the review) or persistent (check provider status/credentials).

## Recover from Failed Jobs

- A job stuck in `RUNNING` past its timeout is automatically swept to `FAILED` (see the error-handling matrix in `06-testing/testing-strategy.md`).
- Failed jobs are retried manually by the user (via the "retry" action in the UI, which re-triggers the same operation) — RepoMind does not silently auto-retry indefinitely for any failure category.

## Verify Deployment

After deploying a new version (see `07-deployment/deployment-guide.md`, "Deployment Validation"):
1. `GET /health` returns `200`.
2. Database is at the latest migration (`alembic current` matches `alembic heads`).
3. Worker process is running and its poll loop is active (check recent log timestamps).
4. A test repository connection + review completes successfully end-to-end (staging only — never run this against a real organization's data casually).

## Run an Evaluation

```bash
cd backend
source .venv/bin/activate
python ../scripts/run_evaluation.py
```
Or via the UI: `/evaluation` page → "Run Evaluation" (requires `team_lead` role or above, per `05-security/authentication-authorization.md`). Results are stored in `evaluation_run` and displayed in the Evaluation Results table.

## Retrain ML Models

```bash
cd backend
source .venv/bin/activate
python ../scripts/train_ml_models.py
```
Produces new versioned `.pkl` model files; compare the new version's metrics against the previous version's baseline before adopting it in production (see `04-development/coding-standards.md`).
