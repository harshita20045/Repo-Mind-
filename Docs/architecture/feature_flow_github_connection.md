# 03 — Feature Flow: GitHub Repository Connection & Sync

## Feature Summary
An `org_admin` user connects a GitHub repository by providing a Personal Access Token (PAT) and repository coordinates. The PAT is encrypted with Fernet before DB storage. On connection, an immediate sync fetches all open pull requests and commits from the GitHub API. The repository is then queued for RAG indexing.

---

## End-to-End Flow

### 1. Connect a GitHub Repository

| Step | Where | What Happens |
|---|---|---|
| User fills GitHub form (owner, repo name, PAT, default branch, project) | `RepositoriesPage.jsx` | Calls `orgApi.connectRepository(orgId, payload)` |
| API call | `frontend/src/lib/api.js:88` | `POST /repositories/connect?organization_id={orgId}` with `{github_owner, github_name, github_pat, default_branch, project_id}` |
| Route handler | `backend/app/organizations/router.py` → `POST /repositories/connect` | Requires `Permission.REPOS_CONNECT` (org_admin only). Calls `connect_repository()` |
| `connect_repository()` | `backend/app/github/service.py` | 1. Validates project belongs to org. 2. Encrypts PAT via `encrypt_token()`. 3. Upserts `GithubConnection` row. 4. Creates `Repository` row with `index_status='unindexed'`. |
| PAT encryption | `backend/app/github/encryption.py` → `encrypt_token()` | `Fernet(FERNET_KEY).encrypt(pat_bytes)` → URL-safe base64 ciphertext stored in `github_connection.encrypted_token` |
| DB writes | `github_connection`, `repository` tables | via SQLAlchemy |
| Trigger sync | `backend/app/github/service.py` → `sync_pull_requests()` | Immediately called after connection |

### 2. PR Sync (called after connect and on-demand)

| Step | Where | What Happens |
|---|---|---|
| `sync_pull_requests(db, repository_id)` | `backend/app/github/service.py` | Entry point for sync |
| Get decrypted PAT | `get_decrypted_pat_for_org(db, org_id)` | Fetches `GithubConnection`, calls `decrypt_token(encrypted_token)` |
| Decrypt PAT | `backend/app/github/encryption.py` → `decrypt_token()` | `Fernet.decrypt(ciphertext)` → plaintext PAT. Used in-memory only. |
| Create GitHub client | `backend/app/github/client.py` → `GitHubClient(pat)` | httpx-based client with 30s timeout, Bearer token header |
| Fetch PRs from GitHub | `client.get_pull_requests(owner, repo)` | `GET /repos/{owner}/{repo}/pulls?state=open&per_page=100` |
| Upsert PRs | `backend/app/github/service.py` | For each PR dict: find or create `PullRequest` row, update fields (title, state, head_sha, etc.) |
| Fetch commits | `client.get_commits(owner, repo, branch)` | `GET /repos/{owner}/{repo}/commits?sha={default_branch}&per_page=50` |
| Upsert commits | `backend/app/github/service.py` | Create `Commit` rows for commits not yet in DB |
| DB commit | `db.commit()` | All changes persisted |
| Index trigger | Worker polls `Repository.index_status == 'unindexed'` | Repository is automatically picked up by `_process_one_indexing_job()` |

### 3. PAT Decryption on Demand

Every time the system needs to call GitHub on behalf of an org:
```
get_decrypted_pat_for_org(db, organization_id)
  -> SELECT github_connection WHERE organization_id=? 
  -> decrypt_token(conn.encrypted_token)
  -> return plaintext_pat (in-memory only, never logged or returned to client)
```

---

## GitHub Client API Calls

File: `backend/app/github/client.py` (httpx-based)

| Method | GitHub Endpoint | Used In |
|---|---|---|
| `get_pull_requests(owner, repo)` | `GET /repos/{owner}/{repo}/pulls?state=open` | Sync |
| `get_pull_request(owner, repo, number)` | `GET /repos/{owner}/{repo}/pulls/{number}` | Review trigger |
| `get_pull_request_diff(owner, repo, number)` | `GET /repos/{owner}/{repo}/pulls/{number}` (Accept: text/x-patch) | Review pipeline |
| `get_pull_request_files(owner, repo, number)` | `GET /repos/{owner}/{repo}/pulls/{number}/files` | Review + linter |
| `get_commits(owner, repo, branch)` | `GET /repos/{owner}/{repo}/commits?sha={branch}` | Sync |
| `get_repository_tree(owner, repo, branch)` | `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` | RAG indexing |
| `get_file_content(owner, repo, path, ref)` | `GET /repos/{owner}/{repo}/contents/{path}?ref={ref}` | RAG document loading |
| `get_blob_content(owner, repo, sha)` | `GET /repos/{owner}/{repo}/git/blobs/{sha}` | Linter file download |
| `get_repository_contents(owner, repo, path)` | `GET /repos/{owner}/{repo}/contents/{path}` | Linter config fetching |

All requests:
- Header: `Authorization: Bearer {pat}` (PAT decrypted in-process)
- Header: `Accept: application/vnd.github+json`
- Timeout: 30 seconds
- Error handling: Raises `GitHubAPIError` on 4xx/5xx

---

## Manual Sync / Re-Sync

| Step | Where | What Happens |
|---|---|---|
| User clicks "Sync" in UI | `RepositoriesPage.jsx` | Calls `orgApi.triggerSync(repoId)` (if implemented) or re-triggers on pull request list page |
| `GET /repositories/{repoId}/pull-requests` | `backend/app/github/router.py` | Calls `sync_pull_requests()` inline, then returns refreshed PR list |

---

## Index Trigger

| Step | Where | What Happens |
|---|---|---|
| Repository created | `Repository.index_status = 'unindexed'` | Set during `connect_repository()` |
| Worker loop | `worker.py` → `_process_one_indexing_job()` | `SELECT repository WHERE index_status='unindexed' FOR UPDATE SKIP LOCKED` |
| Claim job | `repo.index_status = 'indexing'` | Committed immediately |
| Execute | `index_repository(db, repo_id)` | Calls RAG pipeline (see RAG Indexing feature flow) |
| Success | `repo.index_status = 'indexed'` | Committed |
| Failure | `repo.index_status = 'failed'` | Committed with error |

---

## Key Files

| File | Location | Role |
|---|---|---|
| `encryption.py` | `backend/app/github/encryption.py` | `encrypt_token()`, `decrypt_token()` using Fernet |
| `client.py` | `backend/app/github/client.py` | `GitHubClient` class (httpx, all GitHub API methods) |
| `service.py` | `backend/app/github/service.py` | `connect_repository()`, `sync_pull_requests()`, `get_decrypted_pat_for_org()`, `get_pull_request_diff()` |
| `models.py` | `backend/app/github/models.py` | `PullRequest`, `Commit`, `GithubConnection` SQLAlchemy models |
| `router.py` | `backend/app/github/router.py` | Routes for PR listing, sync |
| `service.py` (orgs) | `backend/app/organizations/service.py` | Organization, Project, Repository CRUD |
| `router.py` (orgs) | `backend/app/organizations/router.py` | `POST /repositories/connect` |
| `api.js` (orgApi) | `frontend/src/lib/api.js:70-97` | `orgApi.connectRepository()`, `orgApi.getRepositories()`, `orgApi.triggerIndex()` |

---

## Database Tables Written

| Table | Operation | When |
|---|---|---|
| `github_connection` | UPSERT | On `connect_repository()` |
| `repository` | INSERT | On `connect_repository()` |
| `pull_request` | UPSERT (per PR from GitHub) | On `sync_pull_requests()` |
| `commit` | INSERT (new commits only) | On `sync_pull_requests()` |

---

## Security Properties

| Property | Implementation |
|---|---|
| PAT never stored plaintext | Fernet-encrypted before DB write; plaintext only in-process during API calls |
| PAT never returned to client | `GithubConnection.encrypted_token` never serialized in API responses |
| PAT never logged | All logging of exceptions omits PAT values (only error type logged) |
| PAT never passed to LLM | `review/service.py` security invariant — PAT used for GitHub only, not in prompts |
| REPOS_CONNECT permission | Only `org_admin` can connect repositories |
