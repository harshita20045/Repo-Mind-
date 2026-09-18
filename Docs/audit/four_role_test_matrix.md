# Four-Role E2E Test Matrix

| Role | Login | Dashboard | Navigation | Projects | Repos | Pull Requests | Reviews & Risk | Human Approval | Developer Assistant | Org Admin | Direct Restricted URL | API Security (403) | Logout | Status |
|------|-------|-----------|------------|----------|-------|---------------|----------------|----------------|---------------------|-----------|-----------------------|--------------------|--------|--------|
| **ORG_ADMIN** | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | **BLOCKED** (Pending Runtime Execution) |
| **LEAD** | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | **BLOCKED** (Pending Runtime Execution) |
| **REVIEWER** | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | **BLOCKED** (Pending Runtime Execution) |
| **DEVELOPER** | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | NOT TESTED | **BLOCKED** (Pending Runtime Execution) |

## Test Scenarios to Verify:
1. **Login & Dashboard**: All 4 roles must successfully authenticate and view the basic dashboard.
2. **Navigation Visibility**: The Sidebar should dynamically hide items based on `usePermissions`. E.g., Developers should not see Settings.
3. **Restricted Actions**: Try creating a project or updating member roles as a `developer` to ensure the frontend hides the button and the API rejects the request (403) if forced.
4. **Direct URL Manipulation**: Paste `/settings` as a `developer`. The `ProtectedRoute` must show the "Access Denied" screen.
5. **API Security Enforcement**: A cURL request to `POST /api/organizations/{id}/members` as a `developer` must return `HTTP_403_FORBIDDEN`.

*Note: E2E runtime execution requires actual seeded users representing these 4 roles. The automation script must execute these cases.*
