# RepoMind — Troubleshooting

**Status: Confirmed** (issues drawn directly from the error-handling matrix and architecture; native, no-Docker context)

## Frontend

| Symptom | Likely Cause | Resolution |
|---|---|---|
| PR review page stuck on "loading" | Review job still `RUNNING`, or the frontend is failing to poll `GET /review-runs/{id}` | Confirm the job's status directly via the API/DB; check the worker process is running (see below) |
| Blank/error page after login | `FRONTEND_API_BASE_URL` misconfigured, or backend not reachable | Verify the environment variable (`07-deployment/environment-configuration.md`) and that the backend process is up |

## Backend

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `GET /health` not returning 200 | Backend process not running, or failed to start | Check process manager status/logs (`07-deployment/deployment-guide.md`); confirm `DATABASE_URL` is reachable |
| 500 errors across most endpoints | Database connection failure | Check PostgreSQL is running and `DATABASE_URL` is correct; per the error-handling matrix, DB failures fail fast with a generic 500 — check logs for the underlying connection error |
| Endpoint returns 403 unexpectedly | Role/authorization boundary correctly enforced, or session misconfigured | Confirm the calling user's role against `05-security/authentication-authorization.md`; check `SESSION_SECRET` consistency across processes |

## PostgreSQL

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `CREATE EXTENSION vector` fails | `pgvector` not installed on the PostgreSQL instance | Install the `pgvector` extension package for your PostgreSQL version natively (no Docker image to fall back on — see `01-project/scope.md` for why) before re-running the migration |
| Migrations fail to apply | Schema drift, or a prior migration only partially applied | Inspect Alembic's version table; do not hand-edit the schema — fix forward with a new migration (`07-deployment/database-migrations.md`) |
| Vector similarity queries slow at scale | Missing or inappropriate vector index on `document_chunk.embedding` | Review indexing strategy in `03-design/database-design.md`; this is called out there as an implementation-time decision |

## GitHub API

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Review job fails with a GitHub error | Rate limit (403/429) or transient 5xx | Per the error-handling matrix (`06-testing/testing-strategy.md`), the `github` module retries once on transient 5xx; rate-limit errors surface as a job failure with a clear message — wait and retry, or check the PAT's rate-limit usage |
| "Check repository permissions" message | PAT lacks read access to the repository, or is not scoped correctly | Re-issue a read-only PAT scoped to the target repository/organization; reconnect via `POST /repositories/connect` |

## Authentication

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Users cannot log in | `password_hash` mismatch, or session secret misconfigured across processes | Confirm `SESSION_SECRET` is identical across all backend/worker instances if more than one process instance is running |
| Session lost between requests | Reverse proxy not preserving cookies/headers correctly | Check reverse-proxy configuration (`07-deployment/deployment-guide.md`) |

## AI / LLM

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Review job fails with "invalid JSON" after retry | LLM output does not conform to the finding schema even after the stricter retry prompt | Inspect the logged raw output (retained specifically for this case per `05-security/security.md`); consider a prompt-template issue — see `04-development/git-workflow.md` for how prompt changes are versioned and tested |
| Review job fails with a timeout | LLM provider latency/outage | Retried once automatically; if persistent, check the configured provider's status and `LLM_API_KEY` validity |
| Findings show "unverified citation" | The LLM's `standards_violation` finding lacked verifiable evidence in the retrieved context | This is working as intended — a trust control, not a bug (see `05-security/security.md`) |

## Embeddings

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Review proceeds with "no repo context available" | Embedding step failed (exception during `EmbeddingService` call) | Per the error-handling matrix, this is retried once and the review proceeds without RAG rather than blocking; check that the sentence-transformers model is available on the worker host |

## RAG Retrieval

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Retrieved chunks look irrelevant | Repository not yet (re-)indexed after a documentation change | Check `repository.index_status`/`last_indexed_at`; re-indexing triggers on content-hash change, not on every PR |
| Suspected cross-repository leakage | A missing `repository_id` filter in a retrieval code path | This must never happen — run `test_repository_isolation.py` (TC-011) immediately and treat any failure as a critical, not cosmetic, bug |

## Linter Execution

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Review proceeds without linter findings | Linter process exited non-zero unexpectedly | Per the error-handling matrix, review proceeds without static-analysis evidence and this is noted in the report; check the linter tool's availability/version on the worker host |

## ML Inference

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Risk panel missing predictions | `.pkl` model files not present/loadable on the host | Confirm `scripts/train_ml_models.py` has been run and its output artifacts are deployed alongside the backend/worker (`04-development/development-guide.md`) |

## Migrations

| Symptom | Likely Cause | Resolution |
|---|---|---|
| `alembic upgrade head` hangs or errors | Long-running lock, or a migration attempting an unsafe operation on a large table | See `07-deployment/database-migrations.md`, "Production Migration Precautions" |
