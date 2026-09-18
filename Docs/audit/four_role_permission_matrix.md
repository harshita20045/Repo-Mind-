# Four-Role Permission Matrix

This document maps the target 4-role frontend model to the actual permissions discovered in the backend (`backend/app/auth/permissions.py`).

## Role Mapping

| Frontend Target Role | Mapped Backend Role | Justification |
|----------------------|---------------------|---------------|
| `DEVELOPER`          | `developer`         | Direct match. Base engineering role in backend. |
| `REVIEWER`           | `reviewer`          | Direct match. Adds PR review and finding dismissal capabilities. |
| `LEAD`               | `tech_lead`         | `tech_lead` (and legacy alias `team_lead`) exists in the backend and provides `PRS_APPROVE` and `REPOS_INDEX` over a standard reviewer. |
| `ORG_ADMIN`          | `org_admin`         | Direct match. Inherits through `eng_manager` and provides full organization management capabilities. |

*Note: Frontend UI handling for `security_reviewer`, `eng_manager`, and `org_owner` will be removed. Users with these roles in the backend will still possess their backend permissions, but the UI will not provide bespoke interfaces for them beyond what their base permissions grant in the 4-role UI.*

## Capability & Permission Mapping

Legend:
- `✓`: Permission granted in backend.
- `—`: Permission denied in backend.

| Feature / Capability | Required Backend Permission | ORG_ADMIN | LEAD (`tech_lead`) | REVIEWER | DEVELOPER |
|----------------------|-----------------------------|-----------|--------------------|----------|-----------|
| **Organization** | | | | | |
| View Organization | `organization.read` | ✓ | ✓ | ✓ | ✓ |
| Edit Organization | `organization.update` | ✓ | — | — | — |
| View Members | `members.read` | ✓ | ✓ | ✓ | ✓ |
| Invite Members | `members.invite` | ✓ | — | — | — |
| Update Members (Role)| `members.update` | ✓ | — | — | — |
| Remove Members | `members.remove` | ✓ | — | — | — |
| **Projects** | | | | | |
| View Projects | `projects.read` | ✓ | ✓ | ✓ | ✓ |
| Create Projects | `projects.create` | ✓ | — | — | — |
| Update Projects | `projects.update` | ✓ | — | — | — |
| Delete Projects | `projects.delete` | ✓ | — | — | — |
| **Repositories** | | | | | |
| View Repositories | `repositories.read` | ✓ | ✓ | ✓ | ✓ |
| Connect Repos | `repositories.connect`| ✓ | — | — | — |
| Update Repos | `repositories.update` | ✓ | — | — | — |
| Delete Repos | `repositories.delete` | ✓ | — | — | — |
| Trigger Indexing | `repositories.index` | ✓ | ✓ | — | — |
| **Pull Requests** | | | | | |
| View PRs | `prs.read` | ✓ | ✓ | ✓ | ✓ |
| Trigger AI Review | `reviews.run` | ✓ | ✓ | ✓ | ✓ |
| Request Changes | `prs.request_changes` | ✓ | ✓ | ✓ | — |
| Review PRs | `prs.review` | ✓ | ✓ | ✓ | — |
| Approve PRs | `prs.approve` | ✓ | ✓ | — | — |
| **Findings & Analysis**| | | | | |
| View Findings | `findings.read` | ✓ | ✓ | ✓ | ✓ |
| Dismiss Findings | `findings.dismiss` | ✓ | ✓ | ✓ | — |
| Provide Feedback | `findings.feedback` | ✓ | ✓ | ✓ | ✓ |
| View AI Review | `reviews.read` | ✓ | ✓ | ✓ | ✓ |
| **Security & Analytics**| | | | | |
| View Security | `security.read` | ✓ | ✓ | ✓ | ✓ |
| Security Review | `security.review` | —* | — | — | — |
| View Analytics | `analytics.read` | ✓ | ✓ | ✓ | ✓ |
| View Audit Logs | `audit.read` | ✓ | — | — | — |
| **Developer Assistant**| | | | | |
| Use Chat | `chat.use` | ✓ | ✓ | ✓ | ✓ |

*\* Note: `security.review` is exclusive to `security_reviewer` in the backend, which is outside the 4-role target. ORG_ADMIN doesn't inherit it via the normal chain in `permissions.py` (which goes tech_lead -> eng_manager -> org_admin).*

## Frontend Navigation Model

Based strictly on the permissions above:

- **ORG_ADMIN**: Dashboard, Projects, Repositories, PRs, Reviews, Analytics, Security, Chat, Organization Settings (Members, Org Details, Repo Connections).
- **LEAD**: Dashboard, Projects, Repositories (can index), PRs, Reviews (can approve), Analytics, Security, Chat.
- **REVIEWER**: Dashboard, Projects, Repositories, PRs, Reviews (can review/request changes), Analytics, Security, Chat.
- **DEVELOPER**: Dashboard, Projects, Repositories, PRs, Reviews (read-only), Analytics, Security, Chat.
