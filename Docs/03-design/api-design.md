# RepoMind 2.0 — API Design

**Status: Completed**

## API Conventions

- REST over HTTPS, JSON request/response bodies.
- Backend: FastAPI + Pydantic for request/response schema validation.
- All requests are authorized using standard Bearer Token / Cookie session auth.

## Authentication

Session-based authentication (`POST /auth/login`). Subsequent requests carry a session token; the backend derives `organization_id` and user role from the session. Queries are strictly scoped so no user can access data outside their organization.

## Current APIs

| Method | Path | Purpose | Auth | Module |
|---|---|---|---|---|
| POST | `/auth/login` | Authenticate | — | auth |
| GET | `/auth/me` | Get current session and roles | session | auth |
| GET | `/organizations/{id}/projects` | List projects | session | organizations |
| GET | `/projects/{id}/repositories` | List repositories | session | organizations |
| POST | `/repositories/connect` | Connect a GitHub repository | session, `org_admin` | github |
| GET | `/repositories/{id}` | Repository detail + index status | session | organizations |
| GET | `/pull-requests/active` | Get active PRs for the developer | session | github |
| GET | `/repositories/{id}/pull-requests/{pr_id}/review` | Get PR review (Findings, Risks, Conflicts) | session | review |
| POST | `/repositories/{id}/pull-requests/{pr_id}/review` | Trigger a review | session | review |
| GET | `/chat/sessions` | List chat sessions | session | chat |
| GET | `/chat/sessions/{id}/messages` | Get chat history | session | chat |
| POST | `/chat/sessions/{id}/messages` | Send message to AI Assistant | session | chat |
| POST | `/webhooks/github` | Receive GitHub PR events | webhook secret | webhooks |

## Example — Review Run Response Shape

```json
{
  "findings": [
    {
      "severity": "high",
      "category": "standards_violation",
      "file": "src/example.py",
      "line": 42,
      "title": "...",
      "problem": "...",
      "evidence": "...",
      "recommendation": "..."
    }
  ],
  "risk_assessment": {
    "score": 85,
    "factors": ["touches core auth", "high cyclomatic complexity"]
  },
  "conflicts": [
    {
      "pr_id": 102,
      "description": "Concurrent edit to auth logic in PR 102"
    }
  ]
}
```
