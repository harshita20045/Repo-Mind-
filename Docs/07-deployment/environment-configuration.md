# RepoMind — Environment Configuration

**Status: Confirmed** (variables implied directly by the confirmed architecture); exact variable names are **Proposed** conventions since the source materials describe the secrets conceptually (PAT, LLM key, DB credentials) without dictating literal environment-variable names.

## Variables

| Variable | Purpose | Required | Example / Format | Secret |
|---|---|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgresql://user:pass@localhost:5432/repomind` | Yes |
| `SESSION_SECRET` | Signs/validates session tokens | Yes | random 32+ byte string | Yes |
| `GITHUB_TOKEN` | Default/dev read-only PAT (per-organization tokens are stored encrypted in `github_connection` for the running application; a local dev token may be used for scripts/tests) | Yes (local dev), N/A in production (stored per-org in DB) | `ghp_xxxxxxxxxxxx` | Yes |
| `LLM_PROVIDER` | Selects the configured LLM provider | Yes | `anthropic` | No |
| `LLM_API_KEY` | Credential for the configured LLM provider (Claude API by default) | Yes | `sk-ant-...` | Yes |
| `LLM_MODEL` | Model identifier used for review calls | Yes | `claude-sonnet-4-6` | No |
| `EMBEDDING_MODEL` | sentence-transformers model name for local embeddings | Yes | `all-MiniLM-L6-v2` | No |
| `APP_ENV` | Current environment | Yes | `development` / `staging` / `production` | No |
| `LOG_LEVEL` | Logging verbosity | No | `info` | No |
| `WORKER_POLL_INTERVAL_SECONDS` | How often the worker polls the `job` table | No | `5` | No |
| `JOB_TIMEOUT_SECONDS` | Timeout before a stuck `RUNNING` job is swept to `FAILED` | No | `600` | No |
| `FRONTEND_API_BASE_URL` | Base URL the frontend calls for the backend API | Yes | `http://localhost:8000` (dev) / production domain | No |
| `SECRET_ENCRYPTION_KEY` | Encrypts `github_connection.encrypted_token` at rest | Yes | random 32-byte key | Yes |

No real secret values are shown above — this table exists to document required variables, matching `.env.example` (see `05-security/secrets-management.md`).

## Development

- Loaded from a local `.env` file (never committed).
- `APP_ENV=development`.
- `GITHUB_TOKEN` may point at a personal test-repository PAT.

## Testing / CI

- A dedicated test database (separate from development/production) via a CI-specific `DATABASE_URL`.
- `LLM_API_KEY` in CI should point to a test/mock configuration for most suites; the AI-evaluation regression suite (see `06-testing/testing-strategy.md`) may require a real (rate-limited/budgeted) LLM credential — treat this key as CI-secret-store managed, not committed.

## Production

- Supplied via the host's process-manager environment configuration (see `07-deployment/deployment-guide.md`), not a committed file.
- `APP_ENV=production`.
- `SECRET_ENCRYPTION_KEY` and `SESSION_SECRET` must be distinct, high-entropy values, different from any development/staging value.
- Per-organization GitHub PATs are entered via the application UI (`POST /repositories/connect`) and stored encrypted in the database — `GITHUB_TOKEN` as an environment variable is a development/scripting convenience only, not the production credential path.
