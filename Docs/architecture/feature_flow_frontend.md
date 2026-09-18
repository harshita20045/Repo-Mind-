# 19 — Feature Flow: Frontend Application

## Feature Summary
The RepoMind frontend is a **React 18 SPA** built with Vite. It uses React Router DOM v6 for client-side routing, TanStack Query for server state management, and a custom `usePermissions` hook for client-side RBAC. Authentication state is managed in `App.jsx` via an HttpOnly cookie session. All API calls go through a centralized `fetch` wrapper in `lib/api.js`.

---

## Application Entry Point

File: `frontend/src/main.jsx`

```jsx
ReactDOM.createRoot(document.getElementById('root')).render(<App />)
```

---

## `App.jsx` — Root Component

File: `frontend/src/App.jsx`

### State
```jsx
const [currentUser, setCurrentUser] = useState(null)
const [memberships, setMemberships] = useState([])
const [loading, setLoading] = useState(true)
```

### Session Check on Mount
```jsx
useEffect(() => { checkSession() }, [])

async function checkSession() {
    try {
        const data = await authApi.getMe()   // GET /auth/me (cookie auto-sent)
        if (data?.user) {
            setCurrentUser(data.user)
            setMemberships(data.memberships || [])
        }
    } catch (err) {
        setCurrentUser(null)
    } finally {
        setLoading(false)
    }
}
```

### Render Logic
```
loading=true  -> Spinner ("Loading RepoMind session...")
!currentUser  -> <LoginPage onLoginSuccess={handleLoginSuccess} />
currentUser   -> <QueryClientProvider> <BrowserRouter> <Routes> ...
```

---

## Routing Structure

```
<Routes>
  <Route element={<AppLayout user={currentUser} memberships={memberships} onLogout={handleLogout}>}}>
    <Route path="/"                                      element={<DashboardPage>} />
    
    <Route element={<ProtectedRoute requiredPermission={Permissions.REPOS_READ} />}>
      <Route path="/repositories"                        element={<RepositoriesPage>} />
      <Route path="/repositories/:rid/pull-requests"     element={<PullRequestsPage>} />
      <Route path="/repositories/:rid/pull-requests/:prid" element={<ReviewPage>} />
    </Route>
    
    <Route element={<ProtectedRoute requiredPermission={Permissions.SECURITY_READ} />}>
      <Route path="/security"                            element={<SecurityBrowserPage>} />
    </Route>
    
    <Route element={<ProtectedRoute requiredPermission={Permissions.ANALYTICS_READ} />}>
      <Route path="/analytics"                           element={<AnalyticsPage>} />
    </Route>
    
    <Route element={<ProtectedRoute requiredPermission={Permissions.CHAT_USE} />}>
      <Route path="/chat"                                element={<ChatPage>} />
    </Route>
    
    <Route element={<ProtectedRoute requiredPermission={Permissions.ORG_UPDATE} />}>
      <Route path="/settings"                            element={<SettingsPage>} />
    </Route>
  </Route>
  
  <Route path="*" element={<Navigate to="/" />} />
</Routes>
```

---

## `ProtectedRoute` Component

```jsx
function ProtectedRoute({ memberships, requiredPermission }) {
    const { can } = usePermissions(memberships)
    
    if (requiredPermission && !can(requiredPermission)) {
        return (
            <div>
                <h2>Access Denied</h2>
                <p>You don't have permission to access this page.</p>
                <a href="/">Return to Dashboard</a>
            </div>
        )
    }
    
    const context = useOutletContext()
    return <Outlet context={context} />
}
```

Uses `useOutletContext()` to pass layout context (user, memberships) to child routes.

---

## `usePermissions` Hook

File: `frontend/src/hooks/usePermissions.js`

```javascript
export function usePermissions(memberships = [], orgId = null) {
    return useMemo(() => {
        const activeMemberships = orgId 
            ? memberships.filter(m => m.organization_id == orgId)
            : memberships
        
        const grantedPermissions = new Set()
        const activeRoles = new Set()
        
        activeMemberships.forEach(m => {
            const role = m.role?.toLowerCase() || 'read_only'
            activeRoles.add(role)
            const perms = ROLE_PERMISSIONS[role] || []
            perms.forEach(p => grantedPermissions.add(p))
        })
        
        return {
            can: (permission) => grantedPermissions.has(permission),
            hasRole: (role) => activeRoles.has(role.toLowerCase()),
            isOrgAdmin: hasRole('org_admin') || hasRole('org_owner'),
            isLead: hasRole('tech_lead') || hasRole('team_lead') || hasRole('eng_manager'),
            isReviewer: hasRole('reviewer') || hasRole('security_reviewer'),
            isDeveloper: hasRole('developer') || activeRoles.size === 0,
        }
    }, [memberships, orgId])
}
```

---

## `lib/api.js` — API Wrapper

File: `frontend/src/lib/api.js`

All API calls route through `apiRequest()`:
```javascript
async function apiRequest(endpoint, options = {}) {
    const url = `http://localhost:8000${endpoint}`
    const response = await fetch(url, {
        ...options,
        headers: {'Content-Type': 'application/json', ...options.headers},
        credentials: 'include',   // HttpOnly cookie sent automatically
    })
    
    const data = await response.json().catch(() => null)
    
    if (!response.ok) {
        const err = new Error(data?.detail || `Status ${response.status}`)
        err.status = response.status
        throw err
    }
    return data
}
```

API namespaces:
- `authApi` — login, register, logout, getMe
- `reviewApi` — triggerReview, getReviewRun, approveReviewRun
- `orgApi` — getProjects, getRepositories, getRepository, createProject, connectRepository, triggerIndex
- `githubApi` — getPullRequests, getPullRequest
- `analyticsApi` — getOrgAnalytics
- `chatApi` — createSession, getSessions, getHistory, sendMessage
- `mlApi` — getPrPrediction

---

## Page Components

| Page | Path | File | Purpose |
|---|---|---|---|
| `LoginPage` | (no route — rendered when no user) | `pages/LoginPage.jsx` | Register + Login forms |
| `DashboardPage` | `/` | `pages/DashboardPage.jsx` | Overview, quick stats |
| `RepositoriesPage` | `/repositories` | `pages/RepositoriesPage.jsx` | List repos, connect repo, trigger index |
| `PullRequestsPage` | `/repositories/:rid/pull-requests` | `pages/PullRequestsPage.jsx` | List PRs for a repo |
| `ReviewPage` | `/repositories/:rid/pull-requests/:prid` | `pages/ReviewPage.jsx` | Full review UI: trigger review, poll status, show findings/risk/conflicts/decisions |
| `SecurityBrowserPage` | `/security` | `pages/SecurityBrowserPage.jsx` | Security findings browser across all repos |
| `AnalyticsPage` | `/analytics` | `pages/AnalyticsPage.jsx` | Org-level metrics: risk, findings distribution |
| `ChatPage` | `/chat` | `pages/ChatPage.jsx` | RAG-grounded AI chat interface |
| `SettingsPage` | `/settings` | `pages/SettingsPage.jsx` | Org settings, member management |

---

## `ReviewPage` — Core User Flow

1. Load PR data: `githubApi.getPullRequest(prid)`
2. Show "Review" button
3. Click: `reviewApi.triggerReview(prid)` → gets `job_id`
4. Start polling: `reviewApi.getReviewRun(job_id)` every 2 seconds
5. Show `progress_message` while `status = 'running'`
6. When `status = 'completed'`: render FindingsList, RiskCard, ConflictsList, HumanDecisionPanel
7. Approve: `reviewApi.approveReviewRun(runId, {action, note})`

---

## TanStack Query Usage

`QueryClientProvider` wraps the entire authenticated app:
```jsx
const queryClient = new QueryClient()
<QueryClientProvider client={queryClient}>
    <BrowserRouter>...
```

Used in pages for server state caching and automatic refetching:
```javascript
const { data: reviewRun, isLoading } = useQuery({
    queryKey: ['review-run', runId],
    queryFn: () => reviewApi.getReviewRun(runId),
    refetchInterval: (data) =>
        data?.status === 'completed' || data?.status === 'failed' ? false : 2000
})
```

---

## Layout Structure

File: `frontend/src/components/Layout/AppLayout.jsx`

```
AppLayout
  +-- Sidebar (navigation links, user info, logout button)
  +-- Main Content Area
       +-- Outlet (renders current page component)
```

Navigation items rendered based on `usePermissions()`:
- Dashboard (all)
- Repositories (REPOS_READ)
- Security Browser (SECURITY_READ)
- Analytics (ANALYTICS_READ)
- Chat (CHAT_USE)
- Settings (ORG_UPDATE)

---

## Key Files Summary

| File | Location | Purpose |
|---|---|---|
| `App.jsx` | `frontend/src/App.jsx` | Root, auth state, routing, ProtectedRoute |
| `main.jsx` | `frontend/src/main.jsx` | React DOM mount |
| `api.js` | `frontend/src/lib/api.js` | All API call functions (fetch wrapper) |
| `usePermissions.js` | `frontend/src/hooks/usePermissions.js` | Client-side RBAC hook + permission constants |
| `AppLayout.jsx` | `frontend/src/components/Layout/AppLayout.jsx` | Sidebar + outlet layout |
| `LoginPage.jsx` | `frontend/src/pages/LoginPage.jsx` | Auth forms |
| `ReviewPage.jsx` | `frontend/src/pages/ReviewPage.jsx` | Core review experience |
| `RepositoriesPage.jsx` | `frontend/src/pages/RepositoriesPage.jsx` | Repo management |
| `ChatPage.jsx` | `frontend/src/pages/ChatPage.jsx` | AI chat interface |
| `AnalyticsPage.jsx` | `frontend/src/pages/AnalyticsPage.jsx` | Metrics dashboard |
