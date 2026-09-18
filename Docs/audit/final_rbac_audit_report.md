# Final RBAC Parity & Feature Audit Report

## A. Exact backend roles discovered
The exact roles enumerated in `backend/app/auth/models.py` and handled by `backend/app/auth/permissions.py` are:
`read_only`, `developer`, `reviewer`, `security_reviewer`, `team_lead`, `tech_lead`, `eng_manager`, `org_admin`, `org_owner`.

## B. Four-role mapping
Target Role -> Actual Backend Role Used:
- `ORG_ADMIN` -> `org_admin`
- `LEAD` -> `tech_lead` (and legacy alias `team_lead`)
- `REVIEWER` -> `reviewer`
- `DEVELOPER` -> `developer`

(Legacy roles like `security_reviewer`, `eng_manager`, and `org_owner` are still valid in the backend, but their bespoke frontend UI views have been removed. These users will rely on their base capabilities in the 4-role UI).

## C. Backend permission matrix
Detailed in `docs/audit/four_role_permission_matrix.md`. The backend strictly enforces capabilities through `assert_org_permission(..., Permission.XYZ)` across all roles.

## D. Frontend permission matrix
Detailed in `docs/audit/four_role_permission_matrix.md`. The frontend now dynamically interrogates `usePermissions(memberships)` to reveal routes, actions, and features explicitly granted by the backend. Hardcoded string checks (e.g., `role === 'org_admin'`) have been eliminated.

## E. Feature parity matrix
Detailed in `docs/audit/feature_parity_gap_matrix.md`.

## F. Organization Admin coverage
- Org Settings, Member List, Invite Member, Update Role, Remove Member UI exist and are integrated into `/settings`.
- **Gaps:** Create/Delete Project operations are missing from the UI, and actual GitHub Webhook connection logic is just a placeholder, even though the backend possesses endpoints for repositories connections.

## G. LEAD coverage
- Access to Repositories, triggering PR Reviews, and Analytics.
- **Gaps:** The backend grants `PRS_APPROVE` to `tech_lead`, but the frontend `ReviewPage` does not currently feature a "Submit Human Approval" action.

## H. REVIEWER coverage
- Access to PRs, Risk, Findings, and Chat.
- Correctly blocked from Organization Settings.

## I. DEVELOPER coverage
- Access to PRs, Chat, Repositories (read-only).
- Correctly blocked from executing PR approvals or viewing Org Settings.

## J. Security/direct-access results
Direct-URL routing manipulation is now blocked by `ProtectedRoute` in `App.jsx`, verifying permissions via the central `usePermissions` hook.
API interceptors now catch 403 Forbidden responses to standardize failure states (alerting the user instead of silent console failures).

## K. Remaining gaps and blockers
1. Missing UI for Projects CRUD operations.
2. Missing UI for submitting Human PR Approvals.
3. Missing GitHub app installation workflow in Settings.
4. E2E browser verification hasn't been executed with seeded users.

---

## Final Status

- **ORG_ADMIN**: PARTIAL (Member mgmt implemented, but missing projects/webhook UI)
- **LEAD**: PARTIAL (Missing Approval UI)
- **REVIEWER**: PASS (Subject to runtime execution)
- **DEVELOPER**: PASS (Subject to runtime execution)

- **RBAC**: PASS (Centralized logic implemented)
- **Feature Parity**: PARTIAL (Gaps identified in F, G, K)
- **Route Protection**: PASS (`ProtectedRoute` covers all routes)
- **API Security**: PASS (403 intercepts handled; backend was already secure)
- **E2E**: BLOCKED (Pending actual user generation and browser test run)
- **Visual/UI**: NOT TESTED (Focus was on parity; visual redesign is pending)
