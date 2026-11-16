# RepoMind Intelligence 2.0 — Feature Audit & Gap Analysis

**Document Version:** 2.0-Audit  
**Status:** Comprehensive Feature Classification & Target Gap Analysis  
**Directives Observed:** No implementation details assumed; strictly grounded in existing files and schema.

---

## 1. Feature Audit & Classification Matrix

Every feature currently present in the codebase is categorized into one of seven standard classifications:
1. **Fully implemented and tested:** Production-grade implementation backed by unit/integration tests that pass.
2. **Implemented but not fully tested:** Functional implementation exists in both backend and frontend, but test coverage is missing, partial, or unverified.
3. **Partially implemented:** Functional code exists in backend or frontend, but core behaviors or integrations are incomplete.
4. **Present only in frontend:** UI views, forms, or mock presentations exist in the React SPA without backing backend endpoints or persistence.
5. **Present only in backend:** Functional backend models, services, or APIs exist, but no corresponding frontend interface is exposed to users.
6. **Broken:** Implementation exists but fails at runtime due to code defects, missing dependencies, or contract mismatches.
7. **Not implemented:** Planned or required capability with zero code currently in the repository.

### 1.1 Complete Feature Classification Table

| Feature / Subsystem | Current State | Classification | Evidence & File References |
|---------------------|---------------|----------------|----------------------------|
| **Local Account Authentication** | Salted bcrypt, JWT issue, HttpOnly cookie | **Fully implemented and tested** | `backend/app/auth/`, `backend/tests/test_auth.py`, `LoginPage.jsx` |
| **New User Invite Onboarding** | Token hash validation, password setup | **Fully implemented and tested** | `backend/app/auth/service.py:onboard_user`, `OnboardPage.jsx` |
| **4-Tier RBAC Permission Enforcement** | 4 roles, 22 permissions, server-side assert | **Fully implemented and tested** | `backend/app/auth/permissions.py`, `backend/tests/test_approval_authorization.py` |
| **Organization Management** | Create org, list, fetch org detail | **Implemented but not fully tested** | `backend/app/organizations/routes.py`, `SettingsPage.jsx` |
| **Member Management** | Invite member, update role, remove member | **Fully implemented and tested** | `backend/app/organizations/service.py`, `backend/tests/test_organization_members.py`, `MemberManagement.jsx` |
| **Team Management** | Team CRUD, team member linking | **Implemented but not fully tested** | `backend/app/organizations/models.py`, `TeamManagement.jsx` |
| **Project Management** | Create project, list projects | **Present only in backend** | `POST/GET /organizations/{id}/projects` exists in backend; frontend lacks Project navigation or project switcher |
| **GitHub OAuth Linking** | State CSRF cookie, code exchange, Fernet encrypt | **Implemented but not fully tested** | `backend/app/github/routes.py`, `backend/tests/test_github_auth.py`, simulated in Phase 20 |
| **GitHub Repository Discovery** | List user's admin repos on GitHub | **Implemented but not fully tested** | `GET /organizations/{id}/github/repos`, `backend/app/github/service.py` |
| **Repository Connection** | Store owner, name, default branch, link project | **Fully implemented and tested** | `POST /repositories/connect`, `RepositoriesPage.jsx`, `backend/tests/test_github_integration.py` |
| **Repository Code Indexing** | Git tree traversal, exclusion filter, pgvector | **Fully implemented and tested** | `backend/app/rag/loader.py`, `backend/tests/test_rag.py`, `worker/worker.py` |
| **GitHub Webhook Ingestion** | HMAC-SHA256 verify, delivery deduplication | **Fully implemented and tested** | `backend/app/webhooks/routes.py`, `backend/tests/test_webhook_idempotency.py` |
| **Pull Request Metadata Sync** | Sync PR details, commits, checks, comments | **Implemented but not fully tested** | `POST /pull-requests/{id}/sync`, `backend/app/github/service.py:sync_pull_request_details` |
| **PR Files Changed List** | Return changed files and line additions/deletions | **Broken** | `GET /pull-requests/{id}/files` returns hardcoded mock: `[{"filename": "example.py", ...}]` |
| **PR Activity Log** | View timeline of PR events | **Implemented but not fully tested** | `GET /pull-requests/{id}/events`, `ActivityLog.jsx` |
| **Static Code Analysis** | Isolated temp dir runner for Ruff & Bandit | **Fully implemented and tested** | `backend/app/linter/service.py`, `backend/tests/test_linter.py`, `backend/tests/test_linter_contract.py` |
| **Semantic Conflict Engine** | Mechanical conflict, API/arch/config conflict | **Fully implemented and tested** | `backend/app/conflicts/engine.py`, `ConflictList.jsx` |
| **Explainable PR Risk Scoring** | 7-factor weighted formula, no developer scoring | **Fully implemented and tested** | `backend/app/risk/engine.py`, `RiskAssessment.jsx` |
| **AI PR Review Pipeline** | Multi-prompt review, JSON parsing, retry logic | **Fully implemented and tested** | `backend/app/review/service.py`, `backend/tests/test_review.py` |
| **Finding Evidence Validation** | Grounding check against diff, RAG, linters | **Fully implemented and tested** | `backend/app/review/evidence.py`, `FindingCard.jsx` |
| **Review UI & Interaction** | Review run trigger, finding list, conflict list | **Broken** | `ReviewUI.test.jsx` fails in Vitest due to auto-trigger lifecycle eating mock |
| **Human Review Decision Gate** | Approve/Reject/Request Changes, role-gated | **Fully implemented and tested** | `POST /review-runs/{id}/decide`, `backend/tests/test_review_decision_security.py` |
| **GitHub Automation Actions** | Queue approval or changes back to GitHub | **Implemented but not fully tested** | `AutomationAction` queue processed in `worker/worker.py:process_automation_actions` |
| **Project Merge Policy** | Require AI, CI, human approval before merge | **Implemented but not fully tested** | `ProjectMergePolicy` model, `MergePolicyModal.jsx` |
| **PR Merge Execution** | Trigger GitHub merge via automation queue | **Implemented but not fully tested** | `POST /pull-requests/{id}/merge`, `backend/tests/test_merge_authorization.py` |
| **Security Finding Browser** | Org-wide security finding triage and status | **Implemented but not fully tested** | `backend/app/security/routes.py`, `SecurityBrowserPage.jsx` |
| **Engineering Analytics** | Risk trends, severity/category/lifecycle distributions | **Fully implemented and tested** | `backend/app/analytics/service.py`, `backend/tests/test_gap13_analytics.py`, `AnalyticsPage.jsx` |
| **Context-Aware AI Chat** | Scoped session (PR/Repo/Review), RAG grounding | **Fully implemented and tested** | `backend/app/chat/`, `backend/tests/test_chat_security.py`, `ChatPage.jsx` |
| **Developer Codebase Blueprint** | Auto-generate architecture map, tracks, flows | **Fully implemented and tested** | `backend/app/onboarding/`, `backend/tests/test_onboarding_service.py`, `CodebaseGuidePage.jsx` |
| **Private Developer Progress** | Milestone checkboxes, private notes scratchpad | **Fully implemented and tested** | `user_onboarding_progress`, `frontend/tests/CodebaseGuidePage.test.jsx` (12 tests pass) |
| **GitHub Background Reconciliation**| Sync drift between GitHub and local PRs | **Present only in backend** | Implemented in `backend/app/github/reconciliation.py`, but NOT called in `worker/worker.py` |
| **ML Review Delay Prediction** | Predicted delay category and confidence | **Partially implemented** | Table `ml_prediction` migrated in DB; NO model, ORM, or inference code exists |
| **In-Line PR Diff Comments** | Post review findings directly to GitHub line | **Not implemented** | Findings stored in DB; not dispatched to GitHub PR review comment thread |
| **AST Code Graph & Structure** | Symbol resolution, class/function call graphs | **Not implemented** | Only line-based text chunking currently exists |
| **Semantic Change Impact Analyzer**| Downstream symbol, API, service ripple analysis| **Not implemented** | Only basic filename-heuristic blast radius factor currently exists |
| **AI Test Case Intelligence** | Automated test recommendations for PR diff | **Not implemented** | Only basic test risk detection currently exists |
| **Technical Debt Analyzer** | Churn vs complexity heatmaps, debt backlog | **Not implemented** | Only static finding categorization currently exists |
| **Historical Hotspot Intelligence** | Bug frequency, git blame knowledge maps | **Not implemented** | Raw commit records exist, but no analysis engine |

---

## 2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0)

### Capability 1: Repository Intelligence Engine
- **Current State:** Basic document discovery via GitHub Git tree API, line-based text chunking (50 lines), 384-dimensional dense embeddings (`all-MiniLM-L6-v2`), and cosine distance vector search via `pgvector`.
- **Gaps Identified:**
  - Lack of syntactic AST parsing (function, class, interface boundaries are ignored during chunking).
  - No symbol index or cross-file dependency graph (cannot answer "where is this function called across the codebase?").
  - No package dependency extraction (does not parse `package.json`, `requirements.txt`, `go.mod`, etc., into structured dependency entities).
  - No interactive repository architecture explorer (only static Mermaid generation in onboarding).
- **Required Backend Modules:** `backend/app/intelligence/ast/`, `backend/app/intelligence/symbols/`, `backend/app/intelligence/dependencies/`.
- **Required Frontend Modules:** `frontend/src/components/Intelligence/DependencyGraphViewer.jsx`, `frontend/src/pages/RepositoryTopologyPage.jsx`.
- **Database Changes:** Tables for `code_symbol`, `symbol_reference`, and `package_dependency`.
- **API Endpoints:** `GET /repositories/{id}/symbols`, `GET /repositories/{id}/dependencies`, `GET /repositories/{id}/topology`.

### Capability 2: AI Pull Request Review
- **Current State:** Comprehensive pipeline combining diff extraction, RAG context, Ruff & Bandit linters, semantic conflict detection, LLM structured review with failover, and evidence validation.
- **Gaps Identified:**
  - `GET /pull-requests/{id}/files` returns hardcoded mock data.
  - No dispatch of line-level inline review comments back to GitHub via GitHub Pull Request Review Comments API.
  - Review findings are not automatically correlated across commits (tracking whether an open finding was resolved by the developer's latest push).
- **Required Backend Modules:** `backend/app/github/inline_comments.py`, `backend/app/review/reconciliation.py`.
- **Required Frontend Modules:** `frontend/src/components/Review/InlineDiffAnnotation.jsx`.
- **Database Changes:** Add `github_comment_id` and `is_inline_synced` to `finding` table.
- **API Endpoints:** Fix `GET /pull-requests/{id}/files` to return actual `pull_request_file` records; `POST /review-runs/{id}/publish-comments`.

### Capability 3: Change Impact Analyzer
- **Current State:** Basic blast radius factor in `RiskAssessment` (counts total changed files, directories, and potential test matches).
- **Gaps Identified:**
  - No semantic symbol impact analysis: does not compute which functions, classes, or routes outside the PR files are affected by modified signatures.
  - No breaking API change detection (comparing OpenAPI specs or route handler signatures).
  - No database migration impact analysis (checking for locks, column drops, zero-downtime safety).
  - No dedicated Change Impact visualization UI.
- **Required Backend Modules:** `backend/app/impact/engine.py`, `backend/app/impact/api_diff.py`, `backend/app/impact/db_migration_analyzer.py`.
- **Required Frontend Modules:** `frontend/src/pages/ChangeImpactPage.jsx`, `frontend/src/components/Impact/BlastRadiusGraph.jsx`.
- **Database Changes:** Table `change_impact_assessment` linked to `review_run`.
- **API Endpoints:** `GET /review-runs/{id}/impact`.

### Capability 4: Architecture Intelligence
- **Current State:** Architecture pattern and subsystem breakdown generated by LLM during Onboarding Blueprint generation; basic regex check for layer violations in conflict engine.
- **Gaps Identified:**
  - No deterministic architecture rules engine (e.g., configuring forbidden imports such as Controller -> DB or UI -> Service).
  - No architectural drift detection across PRs (detecting when new code violates designated modular boundaries).
  - No repo-wide component interaction diagram.
- **Required Backend Modules:** `backend/app/architecture/rules.py`, `backend/app/architecture/drift_detector.py`.
- **Required Frontend Modules:** `frontend/src/pages/ArchitecturePoliciesPage.jsx`, `frontend/src/components/Architecture/DriftWarningCard.jsx`.
- **Database Changes:** Table `architecture_policy` linked to `project`.
- **API Endpoints:** `GET/POST /projects/{id}/architecture-policies`, `GET /review-runs/{id}/architecture-drift`.

### Capability 5: AI Test Intelligence
- **Current State:** Scoring of `test_risk` based on presence or absence of test files in PR diff; conflict detector for modified test contracts.
- **Gaps Identified:**
  - No AI-generated test recommendations (suggesting edge cases, inputs, and test assertions for changed functions).
  - No test impact analysis (identifying which specific test files should be run for a PR).
  - No test coverage report ingestion (lcov / Cobertura XML).
- **Required Backend Modules:** `backend/app/testing/recommendations.py`, `backend/app/testing/impact.py`, `backend/app/testing/coverage_ingest.py`.
- **Required Frontend Modules:** `frontend/src/components/Review/TestRecommendationsCard.jsx`.
- **Database Changes:** Table `test_recommendation` linked to `review_run`.
- **API Endpoints:** `GET /review-runs/{id}/test-recommendations`, `POST /repositories/{id}/coverage`.

### Capability 6: Technical Debt Intelligence
- **Current State:** Finding categories include `maintainability` and `standards_violation`; basic analytics distribution.
- **Gaps Identified:**
  - No dedicated Technical Debt scoring or dashboard.
  - No code churn vs complexity quadrant analysis (identifying high-churn, high-complexity hotspot files).
  - No technical debt remediation effort estimation.
- **Required Backend Modules:** `backend/app/tech_debt/engine.py`, `backend/app/tech_debt/hotspot.py`.
- **Required Frontend Modules:** `frontend/src/pages/TechnicalDebtPage.jsx`, `frontend/src/components/TechDebt/ChurnComplexityMatrix.jsx`.
- **Database Changes:** Table `repository_tech_debt_snapshot`.
- **API Endpoints:** `GET /repositories/{id}/technical-debt`.

### Capability 7: Developer Onboarding & Codebase Blueprint
- **Current State:** Highly mature. Generates architecture summaries, Mermaid charts, 3 role tracks (backend, frontend, fullstack), 5-7 file reading orders, hands-on milestones, caution zones, starter issues, and private unmonitored user scratchpads.
- **Gaps Identified:**
  - Generation currently fails if GitHub OAuth credentials expire or repository lacks internet egress.
  - Starter issues are synthetic LLM recommendations, not linked to active GitHub Issues.
- **Required Backend Modules:** `backend/app/onboarding/issue_linker.py`, fallback to offline snapshot generator.
- **Required Frontend Modules:** Enhancements to existing `CodebaseGuidePage.jsx`.
- **Database Changes:** None required (tables `repository_blueprint` and `user_onboarding_progress` are already feature-complete).
- **API Endpoints:** `POST /repositories/{id}/onboarding/link-issues`.

### Capability 8: Repository-Aware AI Assistant
- **Current State:** Context-scoped chat sessions (`pr`, `repository`, `review`) with RAG retrieval and role-gated access (`CHAT_USE`).
- **Gaps Identified:**
  - No conversational memory compaction / token window management (injects full RAG evidence into every turn without rolling summarization).
  - Assistant is read-only; cannot generate executable patch files or PR code suggestions.
  - In PR Review page, the assistant cannot be targeted directly from an individual finding ("Explain this finding in chat").
- **Required Backend Modules:** `backend/app/chat/memory.py`, `backend/app/chat/code_actions.py`.
- **Required Frontend Modules:** "Discuss with AI" button on `FindingCard.jsx` routing directly into contextual chat.
- **Database Changes:** Add `parent_finding_id` to `chat_session`.
- **API Endpoints:** `POST /chat/sessions/{id}/suggest-patch`.

### Capability 9: Historical Code Intelligence
- **Current State:** Commits and webhook events are captured; `ml_prediction` table exists in database without backing code.
- **Gaps Identified:**
  - No git blame / author expertise index (who has the most commits/reviews on the affected files).
  - No PR velocity / review cycle time analytics.
  - No regression prediction model.
- **Required Backend Modules:** `backend/app/historical/author_expertise.py`, `backend/app/historical/velocity.py`.
- **Required Frontend Modules:** `frontend/src/components/Review/ReviewerSuggestions.jsx`, `frontend/src/pages/EngineeringVelocityPage.jsx`.
- **Database Changes:** Table `code_author_metric`.
- **API Endpoints:** `GET /pull-requests/{id}/suggested-reviewers`, `GET /organizations/{id}/velocity`.

### Capability 10: Enterprise Security & Multi-tenant Isolation
- **Current State:** Solid foundation: organization scoping, 4-tier RBAC, Fernet encryption, HMAC webhook verification, rate limiting, and Bandit static analysis.
- **Gaps Identified:**
  - Dedicated secret scanning is missing (Bandit only scans Python AST; general secret scanning for API keys, private keys, and passwords across all file formats is absent).
  - Incomplete audit trail: `audit_log` only captures repo connections and member changes; lacks entries for review decisions, PR merges, and permission rejections.
  - Background worker does not execute inside an isolated tenant context (resolves org manually; risks cross-tenant leaks if an error occurs).
- **Required Backend Modules:** `backend/app/security/secret_scanner.py`, `backend/app/audit/service.py` (centralized audit dispatcher), `backend/app/core/tenant_context.py`.
- **Required Frontend Modules:** `frontend/src/pages/AuditLogPage.jsx`.
- **Database Changes:** Add `organization_id`, `ip_address`, and `metadata` columns to `audit_log`.
- **API Endpoints:** `GET /organizations/{id}/audit-logs`.
