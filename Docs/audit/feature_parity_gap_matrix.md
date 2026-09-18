# Feature Parity & Gap Matrix

This matrix maps backend capabilities to their frontend representation and identifies functional, RBAC, or specification gaps.

| Capability / Feature | Backend Endpoint / Action | Frontend API Client | UI Exists / Route | Correct RBAC | Status / Gap Classification |
|----------------------|---------------------------|---------------------|-------------------|--------------|-----------------------------|
| **Authentication** | | | | | |
| Login | `/api/auth/login` | `authApi.login` | `/` (LoginPage) | N/A | VERIFIED PASS |
| Logout | `/api/auth/logout` | `authApi.logout` | `Sidebar.jsx` | N/A | VERIFIED PASS |
| Current User | `/api/auth/me` | `authApi.getMe()` | `App.jsx` init | N/A | VERIFIED PASS |
| **Organization Mgmt**| | | | | |
| View Organization | `GET /api/organizations/{id}` | Missing / Implicit | `/settings` | Yes | FRONTEND GAP |
| Update Organization | `PUT /api/organizations/{id}` | Missing | `/settings` (placeholder) | No | FRONTEND BUG |
| List Members | `GET /api/organizations/{id}/members`| `fetchMembers()` | `MemberManagement.jsx` | Yes | VERIFIED PASS |
| Invite Member | `POST /api/organizations/{id}/members`| `handleInvite()` | `MemberManagement.jsx` | Yes | VERIFIED PASS |
| Update Member Role | `PUT /api/organizations/{id}/members/{uid}/role` | `handleUpdateRole()` | `MemberManagement.jsx` | Yes | VERIFIED PASS |
| Remove Member | `DELETE .../members/{uid}` | `handleRemove()` | `MemberManagement.jsx` | Yes | VERIFIED PASS |
| **Projects** | | | | | |
| List Projects | `GET /api/projects` | Missing | None | No | FRONTEND GAP |
| Create Project | `POST /api/projects` | Missing | None | No | FRONTEND GAP |
| **Repositories** | | | | | |
| List Repositories | `GET /api/github/repositories` | `repositoriesApi` | `/repositories` | Yes | VERIFIED PASS |
| Connect/Disconnect | `POST/DELETE /api/github/repos` | Missing/Partial | `/settings` (placeholder) | No | FRONTEND GAP |
| Trigger Indexing | `POST /api/repositories/{id}/index`| Missing/Partial | `/repositories` actions | Yes | FRONTEND BUG |
| **Pull Requests** | | | | | |
| List PRs | `GET /api/github/repositories/{id}/prs`| `prApi` | `/repositories/:rid/pull-requests`| Yes | VERIFIED PASS |
| **Reviews & Risk** | | | | | |
| Generate AI Review | `POST /api/review/run` | `reviewApi.run` | `/repositories/:rid/pull-requests/:prid` | Yes | VERIFIED PASS |
| View AI Review/Risk| `GET /api/review/{id}` | `reviewApi.get` | `/repositories/:rid/pull-requests/:prid` | Yes | VERIFIED PASS |
| **Security & Analytics**| | | | | |
| View Security Issues | `GET /api/security/issues` | `securityApi` | `/security` | Yes | VERIFIED PASS |
| View Analytics | `GET /api/analytics` | `analyticsApi` | `/analytics` | Yes | VERIFIED PASS |
| **Chat/Assistant** | | | | | |
| Chat with RAG | `POST /api/chat` | `chatApi.sendMessage` | `/chat` | Yes | VERIFIED PASS |
| **Approval** | | | | | |
| Human Approval | `POST /api/review/approve` | Missing | None | No | FRONTEND GAP |

## Parity Summary
- **Organization UI**: `MemberManagement` is fully implemented and mapped. However, updating Organization details and managing Github webhook connections are currently UI placeholders without backend integration. -> **FRONTEND BUG**
- **Projects**: The backend specification lists `PROJECTS_CREATE`, `PROJECTS_READ`, `PROJECTS_UPDATE`, `PROJECTS_DELETE`. The frontend lacks any `ProjectsPage` or navigation item for projects. -> **FRONTEND GAP**
- **Human Approval**: The backend RBAC has `PRS_APPROVE` (given to LEAD) but there is no explicit button in the frontend PR Review page to issue a human approval status to GitHub. -> **FRONTEND GAP**
