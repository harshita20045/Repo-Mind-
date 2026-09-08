# RepoMind — API Design

**Status: Confirmed** (endpoint list per the Implementation Blueprint, Part 8)

## API Conventions

- REST over HTTPS, JSON request/response bodies.
- Backend: FastAPI + Pydantic for request/response schema validation.
- No endpoint exists for anything not tied to a confirmed requirement in `01-project/requirements.md` — e.g. there is no `/notifications`, `/tasks`, or `/developer-scores` endpoint.

## Authentication

Session-based authentication (`POST /auth/login`). Subsequent requests carry a session token; the backend derives `organization_id`/`repository_id`/user role from the session — these are never trusted from client-supplied request parameters. See `05-security/authentication-authorization.md`.

The full login/session authorization flow is shown in `02-architecture/system-architecture.md`, along with the repository onboarding and feedback sequences that rely on the same session scope.

## Request/Response Patterns

- List endpoints return arrays of resource summaries; detail endpoints return the full resource.
- Mutating endpoints that trigger asynchronous work (e.g. triggering a review) return a `job` reference immediately; the client polls (or, in a future iteration, subscribes via websocket) for job completion rather than the endpoint blocking on the AI pipeline.

Repository connection, review, feedback, and evaluation flows all follow this same async-job pattern where applicable, as documented in `02-architecture/system-architecture.md`.

## Error Handling

Errors follow standard HTTP status codes. See the error-handling matrix in `06-testing/testing-strategy.md` for how specific pipeline failures (GitHub unavailable, LLM timeout, invalid LLM JSON, etc.) map to user-facing responses and retry behavior.

## Validation

All request bodies are validated via Pydantic models on the FastAPI backend before reaching business logic. Authorization checks (role, org/repo membership) are applied per-endpoint as noted below.

## Versioning Strategy

Not specified in the source materials beyond the `review_run.repomind_version`/`prompt_version` fields used for evaluation reproducibility (see `03-design/database-design.md`). No API path versioning (e.g. `/v1/`) is described in the source materials — **Open Decision / Proposed** if introduced later.

## Current APIs

| Method | Path | Purpose | Auth | Module |
|---|---|---|---|---|
| POST | `/auth/login` | Authenticate | — | auth |
| GET | `/organizations/{id}/projects` | List projects | session | organizations |
| GET | `/projects/{id}/repositories` | List repositories | session | organizations |
| POST | `/repositories/connect` | Connect a GitHub repository | session, `org_admin` | github |
| GET | `/repositories/{id}` | Repository detail + index status | session | organizations |
| GET | `/repositories/{id}/pull-requests` | List PRs for a repository | session | github |
| GET | `/pull-requests/{id}` | PR detail | session | github |
| POST | `/pull-requests/{id}/review` | Trigger a review (creates a `job`) | session | review |
| GET | `/review-runs/{id}` | Review run detail + findings | session | review |
| POST | `/findings/{id}/feedback` | Accept / reject / ignore a finding | session | feedback |
| GET | `/evaluations` | List evaluation runs | session | evaluation |
| POST | `/evaluations/run` | Kick off a comparison experiment | session, `team_lead`+ | evaluation |

## Planned APIs (Future, Not Yet Implemented)

| Method | Path | Purpose | Notes |
|---|---|---|---|
| POST | `/webhooks/github` | GitHub webhook receiver | Production-phase only (GitHub App, P3) — signature verification required when introduced |

## Future APIs (Deferred, No Current Design)

Team/repository analytics endpoints (P2) and any enterprise-SSO-related auth endpoints are deferred; no endpoint shape has been designed for them, and none should be assumed to exist until explicitly scoped. This documentation makes no claim that these APIs exist today.

## Example — Trigger a Review

```
POST /pull-requests/{id}/review
Authorization: session cookie/token
```
Response (202-style pattern, job accepted):
```json
{
  "job_id": "...",
  "status": "pending"
}
```

## Example — Review Run / Findings Response Shape

Matches the LLM output schema in `02-architecture/diagrams/ai-review-pipeline.md` and `04-development/coding-standards.md`:
```json
{
  "review_run_id": "...",
  "status": "completed",
  "findings": [
    {
      "severity": "high",
      "category": "standards_violation",
      "file": "src/example.py",
      "line": 42,
      "title": "...",
      "problem": "...",
      "evidence": "...",
      "repository_rule": "...",
      "recommendation": "...",
      "confidence": 0.91
    }
  ]
}
```
