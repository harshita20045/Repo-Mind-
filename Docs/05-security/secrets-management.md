# RepoMind — Secrets Management

**Status: Confirmed**

## Secrets Inventory

| Secret | Purpose | Storage |
|---|---|---|
| GitHub Personal Access Token | Read-only access to connected repositories | `github_connection.encrypted_token`, encrypted at rest, per organization |
| LLM API key(s) | Calling the configured LLM provider (Claude API by default) | Environment variable (backend/worker process) |
| Database credentials | PostgreSQL connection | Environment variable |
| Session secret | Signing/validating session tokens | Environment variable |

## Environment Variables

All secrets are supplied via environment variables, never hardcoded in source. A `.env.example` file (see `04-development/development-guide.md` folder structure) documents required variable names **without real values**. See `07-deployment/environment-configuration.md` for the full variable table.

## GitHub Credentials / Tokens

- Generated as a **fine-grained, read-only** Personal Access Token, scoped to the specific repositories being analyzed.
- Stored server-side, encrypted at rest, in `github_connection` — one token per organization (or per repository, if scoping needs require it). Never returned to the frontend in plaintext after initial entry, and never logged.

## LLM / API Keys

- Supplied via environment variable to the backend/worker process.
- The LLM client is a configurable provider (Claude API default), so the specific key(s) required depend on which provider is configured — documented in `.env.example`, never committed with real values.

## Database Credentials

- Standard PostgreSQL connection string via environment variable (`DATABASE_URL` or equivalent — exact variable name is an implementation detail, see `07-deployment/environment-configuration.md`).

## Secret Storage — Local Development

- `.env` file, listed in `.gitignore`, populated from `.env.example` by each developer locally. Never committed.

## Secret Storage — Production

- Same environment-variable mechanism, populated via the host's process-manager/environment configuration (see `07-deployment/deployment-guide.md`) rather than a committed file. No secrets-manager service (e.g. Vault, AWS Secrets Manager) is named in the source materials — **Open Decision / TBD** if one is introduced; until then, host-level environment configuration, kept out of version control, is the confirmed mechanism.

## `.env.example`

Must exist at the repository root (see the folder structure in `04-development/development-guide.md`) and list every required variable name with a placeholder, never a real value. See `07-deployment/environment-configuration.md` for the concrete variable table to base it on.

## What Must Never Be Committed

- `.env` files with real values.
- The GitHub PAT, in any form (plaintext, logs, error messages).
- LLM API keys.
- Database credentials.
- Any raw session secret / signing key.

Secrets must not be hardcoded or committed to Git under any circumstances. If a secret is accidentally committed, it must be rotated immediately (revoked and reissued), not merely removed from the current file version, since Git history retains prior commits.
