# RepoMind — Authentication & Authorization

**Status: Confirmed**

## Authentication Approach

Session-based authentication. `POST /auth/login` authenticates a user (`user.email` + `password_hash` check) and returns a session token/cookie used on subsequent requests (see `03-design/api-design.md`). No enterprise SSO in the current scope (deferred, P3 — see `01-project/scope.md`).

See the end-to-end login/session sequence in `02-architecture/system-architecture.md`.

## GitHub Authentication / Integration

GitHub access is separate from RepoMind user authentication: a read-only Personal Access Token is stored per organization in `github_connection`, encrypted at rest, and used by the `github` module to call the GitHub REST API on the organization's behalf. Individual RepoMind users do not each authenticate to GitHub directly in the current phase (no per-user GitHub OAuth) — this is deferred, consistent with the "PAT + REST API for MVP" decision (ADR-008).

## Sessions / Tokens

Session-based (not a long-lived API token issued to end users). Exact session mechanism (server-side session store vs. signed token) is an implementation detail not specified in the source materials — **Proposed**: a standard signed session token, expiring per normal web-session practice, is a reasonable default consistent with "session-based auth" as stated in the Implementation Blueprint.

## User Identity

A `user` row (`id`, `email`, `password_hash`, `created_at`) is the identity anchor. GitHub identity (PR author) is tracked separately on `pull_request.author` and is not necessarily linked 1:1 to a RepoMind `user` — this reflects the source materials' explicit point that a developer does not need to "enter their name/identity" into RepoMind since GitHub's PR author field already has this.

## Organization / Team / Project Access

Access is governed by `organization_membership` (`user_id`, `organization_id`, `role`). A user's visibility into projects/repositories/PRs is scoped to organizations they are a member of.

## Repository Access

Repository-level data (PRs, findings, documentation chunks) is reached only through the Project → Repository hierarchy inside an organization the user belongs to — there is no separate, repository-level ACL beyond organization membership in the current scope.

## Authorization Boundaries / Roles

**4 confirmed roles**, stored as `organization_membership.role`:

| Role | Represents | Example Authorization |
|---|---|---|
| `developer` | Opens PRs, views findings | Read access to their org's projects/repos/PRs/findings |
| `reviewer` | Reviews findings, accepts/rejects | Same read access + `POST /findings/{id}/feedback` |
| `team_lead` | Reviewer capabilities + can run evaluations | + `POST /evaluations/run` |
| `org_admin` | Full org administration | + `POST /repositories/connect`, membership management |

This is a deliberately small, flat role set — **not** a complex RBAC system. The source materials are explicit that RepoMind should not build complicated RBAC beyond what's required: GitHub's own author/reviewer/admin roles were sufficient for the research-MVP scope, and the 4-role table above is the confirmed extension for the shared company scope, not a larger permission matrix.

## Endpoint-Level Authorization (from `03-design/api-design.md`)

| Endpoint | Minimum Role |
|---|---|
| `POST /repositories/connect` | `org_admin` |
| `POST /evaluations/run` | `team_lead` |
| All other authenticated endpoints | any org member (`developer` and above) |

## What Is Explicitly Not Built

- No enterprise SSO (deferred, P3).
- No advanced RBAC beyond the 4 roles above (deferred, P3).
- No per-repository ACL distinct from organization membership.
- No individual developer permission tiers based on performance/scoring — role is the only authorization axis, and role is never derived from AI findings, feedback history, or ML predictions.
