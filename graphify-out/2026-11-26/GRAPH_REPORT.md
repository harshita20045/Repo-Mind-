# Graph Report - Repo-Mind-  (2026-11-26)

## Corpus Check
- 449 files · ~267,875 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .bat 4, (none) 3, .ini 2)

## Summary
- 3645 nodes · 9476 edges · 237 communities (144 shown, 93 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1263 edges (avg confidence: 0.93)
- Token cost: 152,469 input · 7,531 output

## Graph Freshness
- Built from commit: `014b45d9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- api.js
- Frontend Dependencies
- typing
- github/routes.py
- Repository
- test_review.py
- organizations/routes.py
- RoleEnum
- fastapi_testclient
- 02 — Feature Flow: Authentication
- chat/service.py
- analyzer.py
- ReviewRun
- github_webhook
- seed_demo_intelligence.py
- 2.3 Domain 3: Review & Risk Engine
- ReviewPage.jsx
- GitHub API Client
- Detailed Step-by-Step
- test_chat_api_route_e2e_grounded_response
- react
- run_architecture_analysis
- review/service.py
- test_review.py
- RepoMind Intelligence 2.0 — Development Handover Report
- RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough
- test_architecture_intelligence.py
- LanguageAwareParser
- 09 — Feature Flow: Risk Scoring Engine
- test_historical_intelligence.py
- poll_and_execute
- Organization API Schemas
- Permission Normalization Tests
- review/router.py
- Onboarding Authorization Tests
- App
- test_linter.py
- DashboardPage.jsx
- _get_authorized_repo
- GitHubIdentity
- verify_org_admin
- re
- TextChunker
- sys
- TestIntelligenceDashboard.jsx
- PullRequest
- RAGRepository
- sync_pull_requests
- calculate_risk
- RepoMind Phase 6–7 Complete Technical Walkthrough
- Step 2: Apply Gap Detection Categories
- auth/routes.py
- index_repository
- 86c411915709_update_role_model_to_developer_reviewer_.py
- api.js
- DependencyExtractor
- PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT
- organizations/service.py
- db_session
- Multi-tenant Security Tests
- test_webhook_idempotency.py
- Final RBAC Parity & Feature Audit Report
- make_client_for_user
- RepoMind Intelligence 2.0 — Complete Technical Audit
- intelligence/routes.py
- GitHub OAuth Identity
- ML Training Service
- Background Workers
- Merge Policy Logic
- Repository Blueprinting
- RepoMind — Environment Configuration
- permissions.py
- RepoMind — Monitoring & Observability
- C. Completed Features Verified from Source Code
- RepoMind — Architecture Decision Record
- Review Pipeline: 11 Stages
- sqlalchemy
- 14 — Feature Flow: Background Worker
- analyzer.py
- CodeGraphNode
- RepoMind — Development Guide
- PullRequest
- Finding
- README.md
- 18 — Feature Flow: ML Prediction (PR Cycle Time)
- pytest
- test_pr_review_engine_upgrade.py
- test_test_runner.py
- testing/routes.py
- test_gap08_superseded_runs.py
- 2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0)
- 15 — Database Schema & Model Cheat Sheet
- Directory Deep Dive
- RepoMind Intelligence - Project Instructions
- Sidebar.jsx
- RepoMind — Database Design
- 01 — System Overview
- RepoMind — Security
- Project Index
- Database Migration Reset
- Vector Database Storage
- GitHub OAuth Authentication
- Organization Management
- Organization Creation API
- User Onboarding Flow
- RepoMind — Testing Strategy
- RepoMind — Operational Runbook
- 08 — Feature Flow: Conflict Detection Engine
- 17 — Security Architecture
- DocumentationIntelligence
- run_test_intelligence_analysis
- RepoMind 2.0 — System Architecture
- RepoMind — Troubleshooting
- 21 — Final Feature Status Matrix
- retrieval.py
- chat/routes.py
- RepositoryScanner
- RepoMind — Authentication & Authorization
- RepoMind — Secrets Management
- RepoMind 2.0 — Deployment Guide (No Docker)
- 2. Phase-by-Phase Implementation Specifications
- sparsevec.h
- End-to-End Flow
- GitHubAPIError
- RepoMind 2.0 — Project Overview
- 2. Analytics Queries
- _setup_repo_and_pr
- RiskAssessmentResponse
- RepoMind — Git Workflow
- RepoMind — Test Plan
- RepoMind — Database Migrations
- get_user_by_email
- Key Architectural Facts (Quick Reference)
- Vector
- RepoMind Intelligence 2.0 — Complete API Audit
- RepoMind 2.0 — UI Design
- 7 Weighted Factors
- `_validate_finding()` — Per-Finding Logic
- RepoMind — Implementation Plan
- RepoMind — Scope
- Local development environment
- End-to-End Flow
- RepoMind 2.0 — Requirements
- RepoMind 2.0 — API Design
- RepoMind — Coding Standards
- End-to-End Flow
- RepoMind 2.0 Complete Technical Guide
- Diagram — PR Review Sequence
- Diagram — RAG Pipeline
- test_concurrent_requests_with_same_delivery_id_handled_safely
- component-architecture.md
- data-flow.md
- deployment-architecture.md
- system-context.md
- test-cases.md
- 9582111491ee_001_initial_auth_tables.py
- _validate_single_finding
- Settings
- TestRepositoryConnect
- ChangeImpactAnalysis
- TestScenario
- test_change_impact_analyzer.py
- cab03f32deec_add_audit_log.py
- RepoMind Intelligence — Current System Architecture
- End-to-End Flow
- FindingSchema
- cd8a43834a0f_add_team_and_teammember_models.py
- Repository Endpoints
- list_security_findings
- github/schemas.py
- make_client_for_user
- Things I Must Not Misunderstand
- .embed_chunks

## God Nodes (most connected - your core abstractions)
1. `User` - 192 edges
2. `Repository` - 156 edges
3. `ReviewRun` - 110 edges
4. `PullRequest` - 108 edges
5. `Project` - 108 edges
6. `Organization` - 99 edges
7. `OrganizationMembership` - 83 edges
8. `RoleEnum` - 75 edges
9. `react` - 74 edges
10. `run_review()` - 60 edges

## Surprising Connections (you probably didn't know these)
- `8. Return Response` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatMessage`` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatSession`` --references--> `ChatSession`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- `5. repository_id Authority` --references--> `PullRequest`  [INFERRED]
  Docs/architecture/security_architecture.md → backend/app/github/models.py
- `Component-Level` --references--> `Finding`  [INFERRED]
  Docs/06-testing/test-plan.md → backend/app/review/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GitHub OAuth Identity Linking** — repomind_2_0_architecture_flow_github_oauth, backend_app_github_oauth_routes_github_oauth_callback, backend_app_github_oauth_service_upsert_github_identity [EXTRACTED 1.00]
- **Developer Onboarding Subsystem** — walkthrough_repository_blueprint, walkthrough_user_onboarding_progress, walkthrough_onboarding_service [EXTRACTED 1.00]
- **RAG Indexing Pipeline** — backend_app_rag_loader, backend_app_rag_chunker, backend_app_rag_embedder, backend_app_rag_repository, postgresql_pgvector [EXTRACTED 1.00]

## Communities (237 total, 93 thin omitted)

### Community 0 - "api.js"
Cohesion: 0.10
Nodes (18): LoginForm(), authApi, historyApi, impactApi, onboardingApi, securityApi, LoginPage(), createTestQueryClient() (+10 more)

### Community 1 - "Frontend Dependencies"
Cohesion: 0.04
Nodes (60): dependencies, mermaid@^12.3.0, react@^18.2.0, react-diff-viewer-continued@^4.4.0, react-dom@^18.2.0, react-markdown@^10.1.0, react-router-dom@^7.18.3, @tanstack/react-query@^5.102.8 (+52 more)

### Community 2 - "typing"
Cohesion: 0.03
Nodes (26): upgrade(), downgrade(), upgrade(), upgrade(), downgrade(), upgrade(), upgrade(), upgrade() (+18 more)

### Community 3 - "github/routes.py"
Cohesion: 0.11
Nodes (20): _assert_repo_access(), get_merge_policy(), get_pull_request(), get_pull_request_commits(), get_pull_request_conflicts(), get_pull_request_events(), get_pull_request_files(), get_repository_branches() (+12 more)

### Community 4 - "Repository"
Cohesion: 0.06
Nodes (49): Organization, OrganizationMembership, User, bootstrap_system(), hash_password(), Project, Repository, review_code_security() (+41 more)

### Community 5 - "test_review.py"
Cohesion: 0.06
Nodes (27): FallbackProvider, GeminiProvider, retry_if_transient_error(), get_llm_provider(), GroqProvider, LLMProvider, LLMProviderError, _mark_failed() (+19 more)

### Community 6 - "organizations/routes.py"
Cohesion: 0.22
Nodes (15): create_organization(), create_project(), create_repository(), create_team(), get_organization(), get_repository(), invite_member(), list_members() (+7 more)

### Community 7 - "RoleEnum"
Cohesion: 0.07
Nodes (32): extract_token_from_request(), get_current_user(), RoleEnum, decode_access_token(), get_user_by_id(), ProjectMember, TeamMember, run_decision_test() (+24 more)

### Community 8 - "fastapi_testclient"
Cohesion: 0.22
Nodes (3): test_bootstrap_flow(), test_onboard_and_change_password_flow(), test_organization_membership_roles()

### Community 9 - "02 — Feature Flow: Authentication"
Cohesion: 0.25
Nodes (7): 02 — Feature Flow: Authentication, Backend (Canonical), Data Flow Diagram (Mermaid), Feature Summary, Frontend (Mirror), RBAC Enforcement, Security Properties

### Community 10 - "chat/service.py"
Cohesion: 0.14
Nodes (13): ChatMessage, ChatSession, _build_grounded_mock_response(), create_session(), get_session_messages(), get_sessions(), send_message(), test_chat_service_generates_grounded_response_with_citations() (+5 more)

### Community 12 - "ReviewRun"
Cohesion: 0.17
Nodes (13): ReviewRun, test_get_review_run_cross_tenant(), test_trigger_review_creates_pending_job_and_returns_202(), test_trigger_review_duplicate_returns_idempotent(), _setup_repo_and_pr(), test_gap_09_abandoned_job_exceeding_max_retries_fails(), test_gap_09_abandoned_job_with_superseded_sha_transitions_to_superseded(), test_gap_09_active_heartbeat_job_is_not_recovered() (+5 more)

### Community 13 - "github_webhook"
Cohesion: 0.13
Nodes (11): github_webhook(), _resolve_repository(), Webhook Endpoint, 12 — Feature Flow: GitHub Webhook Automation, Configuration Required, Feature Summary, Key Files, Security Properties (+3 more)

### Community 14 - "seed_demo_intelligence.py"
Cohesion: 0.10
Nodes (13): Document, DocumentChunk, get_target_repo(), main(), seed_adrs(), seed_blueprint(), seed_commits_and_hotspots(), seed_rag_documentation() (+5 more)

### Community 15 - "2.3 Domain 3: Review & Risk Engine"
Cohesion: 0.05
Nodes (43): 1.1 Domain Table Breakdown, 1. Complete Database Schema Inventory, 2.1 Domain 1: Authentication & Multi-Tenant Hierarchy, 2.2 Domain 2: GitHub Integration & Pull Requests, 2.3 Domain 3: Review & Risk Engine, 2.4 Domain 4: Code-Aware RAG & pgvector Storage, 2.5 Domain 5: Collaboration & Developer Onboarding, 2.6 Domain 6: Webhooks, Audit & ML (+35 more)

### Community 16 - "ReviewPage.jsx"
Cohesion: 0.12
Nodes (22): ImpactOverview(), ActivityLog(), ConflictCard(), ConflictList(), EvidenceStatus(), FindingCard(), LifecycleBadge(), FindingList() (+14 more)

### Community 17 - "GitHub API Client"
Cohesion: 0.11
Nodes (3): GitHubClient, connect_repository(), link_token()

### Community 18 - "Detailed Step-by-Step"
Cohesion: 0.10
Nodes (19): Index Trigger, 04 — Feature Flow: RAG Indexing, Crash Recovery, Database Tables, Detailed Step-by-Step, Embedding Model Details, Feature Summary, Manual Re-Index (+11 more)

### Community 20 - "react"
Cohesion: 0.09
Nodes (31): ArchitectureDashboard(), ArchitectureHealthOverview(), ArchitectureRuleManager(), ArchitectureViolationsList(), CircularDependencyGraph(), FlowAnalysisViewer(), EdgeDetailsModal(), EngineeringGraphEngine() (+23 more)

### Community 21 - "run_architecture_analysis"
Cohesion: 0.22
Nodes (6): ensure_baseline_architecture_rules(), run_architecture_analysis(), ArchitectureAnalysis, ArchitectureRule, ArchitectureViolation, test_engine_run_architecture_analysis()

### Community 22 - "review/service.py"
Cohesion: 0.08
Nodes (16): LocalEmbedder, RAGRetriever, RetrievalResult, retrieve_context(), _persist_conflicts(), run_review(), embedder(), test_empty_repository() (+8 more)

### Community 23 - "test_review.py"
Cohesion: 0.05
Nodes (28): derive_query_from_diff(), LLMOutputParseError, parse_llm_output(), ReviewOutput, test_malformed_ai_output_parsing(), test_multi_stage_review_8_categories_validation(), FailingProvider, FakeProvider (+20 more)

### Community 24 - "RepoMind Intelligence 2.0 — Development Handover Report"
Cohesion: 0.06
Nodes (32): 10. AI Chat Assistant (`/chat`), 11. AI Test Intelligence (`/repositories/{id}/test-intelligence`, `/test-scenarios`, `/generated-tests`, `/test-intelligence`), 12. Technical Debt Intelligence (`/repositories/{id}/tech-debt`), 13. Security & Analytics (`/security`, `/analytics`), 1. Health & Core, 2. Authentication & Memberships (`/auth`), 3. Organizations & Projects (`/organizations`, `/projects`), 4. GitHub Integration & Webhooks (+24 more)

### Community 25 - "RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough"
Cohesion: 0.05
Nodes (39): 10. Complete API Reference, 11. Role Hierarchy & Repository Authorization, 12. Private Progress & Anti-Surveillance Guarantees, 13. Frontend Component & Routing Architecture, 14. Mermaid Rendering Security, 15. Developer Onboarding User Journey, 16. Team Lead Refresh User Journey, 17. Testing Commands & Actual Results (+31 more)

### Community 26 - "test_architecture_intelligence.py"
Cohesion: 0.08
Nodes (22): check_architecture_rules(), GroundedViolation, _matches_pattern(), CircularDependency, detect_circular_dependencies(), calculate_architecture_health_score(), generate_architecture_mermaid(), FlowAnalysisResult (+14 more)

### Community 28 - "LanguageAwareParser"
Cohesion: 0.11
Nodes (8): CodeSymbol, LanguageAwareParser, ParsedCodeFile, ASTChunk, ASTCodeChunker, test_js_ts_parsing(), test_parser_syntax_error_resilience(), test_python_ast_parsing()

### Community 29 - "09 — Feature Flow: Risk Scoring Engine"
Cohesion: 0.12
Nodes (15): _persist_risk(), RiskResult, 09 — Feature Flow: Risk Scoring Engine, Blast Radius and Test Impact, `_calculate_blast_radius(changed_files)` returns:, `calculate_risk()` Structure, `_calculate_test_impact(changed_files, diff)` returns:, Entry Point (+7 more)

### Community 30 - "test_historical_intelligence.py"
Cohesion: 0.05
Nodes (44): compute_and_index_hotspots(), _extract_adrs_from_markdown(), _infer_modules_from_title_and_text(), mine_and_index_commits(), parse_and_index_adrs(), ArchitectureDecisionRecord, HistoricalCommitRecord, RecurringIssueHotspot (+36 more)

### Community 31 - "poll_and_execute"
Cohesion: 0.14
Nodes (6): Startup Crash Recovery, _fail_run(), poll_and_execute(), _process_automations(), _process_one_job(), _process_reconciliation()

### Community 32 - "Organization API Schemas"
Cohesion: 0.14
Nodes (21): update_member_role(), GithubConnectionBase, GithubConnectionCreate, GithubConnectionResponse, MemberBase, MemberInvite, MemberRoleUpdate, OrganizationBase (+13 more)

### Community 33 - "Permission Normalization Tests"
Cohesion: 0.10
Nodes (7): test_def_02_action_casing_cannot_bypass_approve_permission(), override_db(), override_user(), test_def_02_arbitrary_unsupported_action_rejected(), test_def_02_lead_approve_normalized_and_triggers_merge_policy(), test_def_02_reject_permission_and_queue_worker(), test_def_06_missing_pull_request_returns_404_no_500()

### Community 34 - "review/router.py"
Cohesion: 0.13
Nodes (11): evaluate_merge_policy(), get_decrypted_github_token_for_org(), get_repository_by_id(), decide_review_run(), get_review_run(), get_review_run_decisions(), list_review_runs(), trigger_review() (+3 more)

### Community 36 - "Onboarding Authorization Tests"
Cohesion: 0.22
Nodes (16): cleanup_overrides(), make_client_for_user(), test_10_invalid_track_and_milestone_ids_are_rejected(), test_11_repository_access_enforced_across_all_endpoints(), test_12_active_generation_conflict_returns_409(), test_13_unindexed_repository_error_returns_400(), test_14_responses_do_not_leak_internal_prompts_or_traces(), test_1_authorized_user_can_retrieve_blueprint() (+8 more)

### Community 37 - "App"
Cohesion: 0.10
Nodes (28): 19 — Feature Flow: Frontend Application, `App.jsx` — Root Component, Application Entry Point, Feature Summary, Key Files Summary, Layout Structure, `lib/api.js` — API Wrapper, `ProtectedRoute` Component (+20 more)

### Community 38 - "test_linter.py"
Cohesion: 0.07
Nodes (25): _persist_failure(), _persist_result(), run_linters(), BanditLinter, LinterTool, RuffLinter, LinterResult, _setup_pr() (+17 more)

### Community 39 - "DashboardPage.jsx"
Cohesion: 0.12
Nodes (29): Page Components, ChatAssistant(), SOURCE_TYPE_STYLES, SUPPORTED_QUESTIONS, HistoricalContextCard(), Card(), MetricCard(), SectionCard() (+21 more)

### Community 40 - "_get_authorized_repo"
Cohesion: 0.12
Nodes (18): create_architecture_rule(), delete_architecture_rule(), get_architecture_flows(), _get_authorized_repo(), get_circular_dependencies(), get_latest_architecture_analysis(), list_architecture_rules(), reset_architecture_rules_defaults() (+10 more)

### Community 41 - "GitHubIdentity"
Cohesion: 0.07
Nodes (21): decrypt_token(), encrypt_token(), _get_fernet(), GitHubCredential, GitHubIdentity, reconcile_pull_requests(), get_valid_access_token_for_credential(), refresh_github_credential() (+13 more)

### Community 42 - "verify_org_admin"
Cohesion: 0.18
Nodes (11): verify_org_admin(), 2.10 Developer Onboarding Domain, 2.1 Health Domain, 2.3 Organizations, Projects & Repositories Domain, 2.4 GitHub Integration & Pull Requests Domain, 2.5 Review & Decision Domain, 2.6 Webhook Receiver Domain, 2.7 Engineering Analytics Domain (+3 more)

### Community 43 - "re"
Cohesion: 0.08
Nodes (17): _detect_api_contract_conflicts(), _detect_architecture_conflicts(), _detect_configuration_conflicts(), detect_conflicts(), _detect_mechanical_conflicts(), _detect_security_policy_conflicts(), _detect_test_contract_conflicts(), DetectedConflict (+9 more)

### Community 44 - "TextChunker"
Cohesion: 0.22
Nodes (4): TextChunker, test_chunker_determinism_and_overlap(), `backend/app/rag/chunker.py`, 1.9 RAG Implementation & Vector Database

### Community 45 - "sys"
Cohesion: 0.09
Nodes (4): get_auth_token(), test_oauth_routes(), run_test(), test_phase3()

### Community 46 - "TestIntelligenceDashboard.jsx"
Cohesion: 0.21
Nodes (10): TestCodeViewer(), TestExecutionResult(), CATEGORIES, TestIntelligenceDashboard(), CATEGORY_THEMES, PRIORITY_BADGES, TestScenarioCard(), testingApi (+2 more)

### Community 47 - "PullRequest"
Cohesion: 0.12
Nodes (23): AIAnalysis, GitHubComment, GitHubRepositoryAccess, GitHubReview, HumanReview, ProjectMergePolicy, PullRequest, PullRequestCheck (+15 more)

### Community 48 - "RAGRepository"
Cohesion: 0.10
Nodes (11): RAGRepository, setup_test_repos(), test_persistence_and_idempotency(), test_d_rag_integration_correct_repository_id(), test_e_repository_isolation(), `backend/app/rag/embedder.py`, `backend/app/rag/repository.py`, `backend/app/rag/service.py` (+3 more)

### Community 49 - "sync_pull_requests"
Cohesion: 0.17
Nodes (14): sync_pull_requests(), GithubConnection, `GET /repositories/{id}/pull-requests`, 03 — Feature Flow: GitHub Repository Connection & Sync, 1. Connect a GitHub Repository, 2. PR Sync (called after connect and on-demand), 3. PAT Decryption on Demand, Database Tables Written (+6 more)

### Community 50 - "calculate_risk"
Cohesion: 0.09
Nodes (11): _extract_linter_issues(), _calculate_blast_radius(), calculate_risk(), _calculate_test_impact(), _score_dependency_risk(), _score_to_level(), test_bandit_canonical_schema_with_findings(), test_empty_linter_findings() (+3 more)

### Community 51 - "RepoMind Phase 6–7 Complete Technical Walkthrough"
Cohesion: 0.08
Nodes (26): Executive Summary, Part 10 — PostgreSQL + pgvector Internal Understanding, Part 12 — Phase 7 Overview, Part 13 — Phase 7 End-to-End Retrieval Flow, Part 14 — Retriever Code Deep Dive, Part 15 — Cosine Retrieval, Part 16 — top_k, Part 17 — Repository Isolation (+18 more)

### Community 52 - "Step 2: Apply Gap Detection Categories"
Cohesion: 0.08
Nodes (24): A. Entry and Exit Conditions, Analyzing Business Logic Gaps, B. State Definitions, C. State Transitions, Checklist for Quick Analysis, Common Gap Patterns, D. Exceptional Paths, E. Billing and Credit Rules (+16 more)

### Community 53 - "auth/routes.py"
Cohesion: 0.06
Nodes (53): get_org_analytics(), bootstrap(), change_password_route(), format_auth_response(), get_me(), login(), logout(), onboard() (+45 more)

### Community 54 - "index_repository"
Cohesion: 0.20
Nodes (4): index_repository(), test_service_integration(), Part 6 — Hashing, Key Files

### Community 56 - "api.js"
Cohesion: 0.11
Nodes (38): App(), queryClient, RepositoryNav(), ROLE_LABELS, ROLES, TeamManagement(), Badge(), RISK_STYLES (+30 more)

### Community 58 - "PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT"
Cohesion: 0.15
Nodes (12): 10. Defects and Fixes, 11. External Limitations, 12. Conclusion, 1. Objective and Scope, 2. Runtime and Initialization, 3. Authentication & RBAC, 5. Repository Discovery and Connection, 6. Webhook and Review Pipeline (E2E) (+4 more)

### Community 59 - "organizations/service.py"
Cohesion: 0.17
Nodes (18): AuditLog, hash_invitation_token(), Team, add_member(), create_organization(), create_project(), create_repository(), create_team() (+10 more)

### Community 60 - "db_session"
Cohesion: 0.22
Nodes (4): client(), db_session(), setup_test_db(), _verify_test_db_identity()

### Community 62 - "Multi-tenant Security Tests"
Cohesion: 0.29
Nodes (4): test_chat_session_creation_rejects_foreign_repository(), test_def_04_cross_tenant_chat_retrieval_prevented(), override_db(), override_user()

### Community 63 - "test_webhook_idempotency.py"
Cohesion: 0.13
Nodes (7): WebhookEvent, _verify_github_signature(), compute_signature(), test_different_delivery_ids_processed_independently(), test_retry_after_processing_failure_succeeds_without_duplicate_records(), test_same_delivery_received_twice_is_idempotent(), webhook_repo_fixture()

### Community 64 - "Final RBAC Parity & Feature Audit Report"
Cohesion: 0.10
Nodes (17): 4-Role RBAC Model, A. Exact backend roles discovered, B. Four-role mapping, C. Backend permission matrix, D. Frontend permission matrix, E. Feature parity matrix, F. Organization Admin coverage, Final RBAC Parity & Feature Audit Report (+9 more)

### Community 65 - "make_client_for_user"
Cohesion: 0.29
Nodes (7): cleanup_overrides(), make_client_for_user(), test_api_circular_dependencies_endpoint(), test_api_flows_endpoint(), test_api_get_latest_analysis(), test_api_rule_governance_lifecycle(), test_api_trigger_analysis_post()

### Community 66 - "RepoMind Intelligence 2.0 — Complete Technical Audit"
Cohesion: 0.11
Nodes (18): 1.10 Background Jobs & Worker Service, 1.11 Tests & Quality Assurance, 1.1 Frontend Structure, 1.2 Backend Structure, 1.3 Database Models & Schema, 1.4 Database Migrations, 1.5 API Routes & Endpoints, 1.7 GitHub Integration (+10 more)

### Community 67 - "intelligence/routes.py"
Cohesion: 0.30
Nodes (13): get_architecture_diagram(), _get_authorized_repo(), get_repository_dependencies(), get_repository_graph(), get_repository_summary(), get_repository_symbols(), trigger_intelligence_indexing(), CodeSymbolSchema (+5 more)

### Community 89 - "RepoMind — Environment Configuration"
Cohesion: 0.33
Nodes (5): Development, Production, RepoMind — Environment Configuration, Testing / CI, Variables

### Community 90 - "permissions.py"
Cohesion: 0.09
Nodes (15): check_org_permission(), _get_current_user_lazy(), get_role_permissions(), require_org_permission(), _check(), require_permission(), _check(), role_has_permission() (+7 more)

### Community 91 - "RepoMind — Monitoring & Observability"
Cohesion: 0.15
Nodes (12): AI Failures, API Errors, Application Logs, Database Health, GitHub Integration Failures, ML Failures, Performance Metrics, RAG Failures (+4 more)

### Community 92 - "C. Completed Features Verified from Source Code"
Cohesion: 0.25
Nodes (8): 2. Advanced AI Pull Request Intelligence (`backend/app/review/analysis.py`, `service.py`, `evidence.py`), 3. Change Impact & Blast Radius Analyzer (`backend/app/impact/`), 4. Architecture Intelligence (`backend/app/architecture/`), 5. Developer Onboarding & Blueprint Engine (`backend/app/onboarding/`), 6. Foundation & Worker Resiliency (`worker/worker.py`, `backend/app/auth/`), 8. Technical Debt Intelligence (`backend/app/tech_debt/`, `frontend/src/components/TechDebt/`), 9. Smart Developer Onboarding (`backend/app/onboarding/`, `frontend/src/pages/CodebaseGuidePage.jsx`), C. Completed Features Verified from Source Code

### Community 93 - "RepoMind — Architecture Decision Record"
Cohesion: 0.11
Nodes (17): ADR-001 — Modular Monolith Architecture, ADR-002 — Frontend: React + TypeScript + Tailwind, ADR-003 — Backend: FastAPI + Pydantic, ADR-004 — Database: PostgreSQL + SQLAlchemy + Alembic, ADR-005 — Vector Storage: pgvector (not a dedicated vector database), ADR-006 — Embeddings: sentence-transformers (local), ADR-007 — Retrieval Mechanism: pgvector Cosine Similarity, Repository-Scoped, ADR-008 — GitHub Integration Strategy: PAT + REST API (Phase 1) (+9 more)

### Community 94 - "Review Pipeline: 11 Stages"
Cohesion: 0.08
Nodes (19): Conflict, build_user_content(), test_f_prompt_injection_framing(), 05 — Feature Flow: PR Review Pipeline (Full 11-Stage), Data Flow Diagram (Mermaid), Duplicate-Review Invariant, Feature Summary, Review Pipeline: 11 Stages (+11 more)

### Community 95 - "sqlalchemy"
Cohesion: 0.06
Nodes (12): run_migrations_offline(), run_migrations_online(), downgrade(), upgrade(), downgrade(), upgrade(), downgrade(), upgrade() (+4 more)

### Community 96 - "14 — Feature Flow: Background Worker"
Cohesion: 0.11
Nodes (17): 14 — Feature Flow: Background Worker, Configuration, Consecutive Error Tracking, Error Handling, Feature Summary, Job Lifecycle States, LLM Provider Initialization, Parallelism Support (+9 more)

### Community 97 - "analyzer.py"
Cohesion: 0.07
Nodes (23): BreakingChange, _check_signature_compatibility(), detect_breaking_changes(), _detect_breaking_from_diff_lines(), _detect_configuration_breaks(), _detect_database_schema_breaks(), ChangedSymbol, detect_code_changes() (+15 more)

### Community 98 - "CodeGraphNode"
Cohesion: 0.10
Nodes (15): CodeKnowledgeGraph, RepositoryIndexer, CodeGraphEdge, CodeGraphNode, PackageDependency, RepositoryScanSummary, test_incremental_indexing_lifecycle(), test_knowledge_graph_construction_and_mermaid() (+7 more)

### Community 99 - "RepoMind — Development Guide"
Cohesion: 0.13
Nodes (14): Backend Setup (Python / FastAPI), Database Initialization and Migrations, Environment Variables, Frontend Setup, Linting and Formatting, No Docker, PostgreSQL Setup (Native), RepoMind — Development Guide (+6 more)

### Community 100 - "PullRequest"
Cohesion: 0.19
Nodes (10): get_organization_analytics(), Finding, RiskAssessment, test_get_review_run(), _setup_org_project_repo(), test_gap_13_analytics_counts_distinct_prs_not_all_runs(), test_gap_13_higher_id_completed_earlier_lower_id_completed_later(), test_gap_13_pr_without_completed_runs_excluded_from_reviews() (+2 more)

### Community 102 - "Finding"
Cohesion: 0.07
Nodes (39): AutomationAction, HumanDecision, 10 — Feature Flow: Human Review Approval Gate, Feature Summary, HumanDecision Model, Key Files, Permissions Required, Request/Response Schemas (+31 more)

### Community 103 - "README.md"
Cohesion: 0.17
Nodes (7): Documentation Set, Documents, Feature Flows (Start-to-End Traces), RepoMind 2.0 — Architecture Documentation Index, Source Code Truth Principles, Status & Summary, System-Level

### Community 104 - "18 — Feature Flow: ML Prediction (PR Cycle Time)"
Cohesion: 0.11
Nodes (17): 18 — Feature Flow: ML Prediction (PR Cycle Time), 1. API Request, 2. Training Data Check, 3. Rule-Based Baseline, 4. Response, Current State (as observed in source), Data Model, Dataset Building (+9 more)

### Community 105 - "pytest"
Cohesion: 0.05
Nodes (44): RepositoryBlueprint, UserOnboardingProgress, build_onboarding_user_content(), _get_repo_and_verify_access(), get_repository_blueprint(), get_user_onboarding_progress(), refresh_repository_blueprint(), update_user_onboarding_progress() (+36 more)

### Community 106 - "test_pr_review_engine_upgrade.py"
Cohesion: 0.18
Nodes (6): extract_pr_analysis_context(), PRAnalysisContext, PRFileSummary, query_related_modules(), test_empty_diff_and_pure_deletion_handling(), test_pr_analysis_extraction_and_diff_hunks()

### Community 107 - "test_test_runner.py"
Cohesion: 0.27
Nodes (5): GeneratedTestCase, IsolatedTestRunner, test_runner_blocks_malicious_code_and_marks_error(), test_runner_captures_assertion_failure_without_false_pass(), test_runner_executes_safe_test_and_captures_pass()

### Community 108 - "testing/routes.py"
Cohesion: 0.17
Nodes (13): execute_generated_test(), generate_test_case(), _get_authorized_repo(), get_pr_test_scenarios(), get_test_dashboard(), trigger_test_analysis(), ExistingTestFileSummary, GeneratedTestCaseResponse (+5 more)

### Community 109 - "test_gap08_superseded_runs.py"
Cohesion: 0.16
Nodes (12): LocalProvider, _update_progress(), _enqueue_review(), _setup_repo_and_pr(), test_gap_08_completed_historical_runs_are_preserved(), test_gap_08_concurrent_duplicate_webhooks_serialization(), deliver_webhook(), test_gap_08_new_head_sha_supersedes_pending_and_running_runs() (+4 more)

### Community 110 - "2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0)"
Cohesion: 0.13
Nodes (14): 1.1 Complete Feature Classification Table, 1. Feature Audit & Classification Matrix, 2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0), Capability 10: Enterprise Security & Multi-tenant Isolation, Capability 1: Repository Intelligence Engine, Capability 2: AI Pull Request Review, Capability 3: Change Impact Analyzer, Capability 4: Architecture Intelligence (+6 more)

### Community 111 - "15 — Database Schema & Model Cheat Sheet"
Cohesion: 0.06
Nodes (34): 15 — Database Schema & Model Cheat Sheet, All SQLAlchemy Models, `audit_log`, `chat_message`, `chat_session`, `commit`, `conflict`, Database Configuration (+26 more)

### Community 112 - "Directory Deep Dive"
Cohesion: 0.17
Nodes (11): 1. `backend/app/`, 2. `backend/app/auth/`, 3. `backend/app/rag/`, 4. `backend/app/review/`, 5. `backend/alembic/`, 6. `frontend/src/`, 7. `worker/`, 8. `backend/scripts/` & `backend/tests/` (+3 more)

### Community 113 - "RepoMind Intelligence - Project Instructions"
Cohesion: 0.14
Nodes (13): 10. Testing Rules, 11. Implementation Workflow, 12. Completion Criteria, 1. Project Identity, 2. Primary Development Rule, 3. Development Principles, 4. AI Engineering Principles, 5. Repository Intelligence (+5 more)

### Community 114 - "Sidebar.jsx"
Cohesion: 0.27
Nodes (9): AppLayout(), Icons, NavItem(), NavSection(), Sidebar(), getPageInfo(), ROUTE_LABELS, TopNav() (+1 more)

### Community 115 - "RepoMind — Database Design"
Cohesion: 0.15
Nodes (12): Audit Information, Database Technology, Entities, Indexing Strategy, Migration Plan, ML Prediction Data, Primary / Foreign Keys and Constraints, Relationships (ER Diagram) (+4 more)

### Community 116 - "01 — System Overview"
Cohesion: 0.25
Nodes (7): 01 — System Overview, Active Runtime Processes, High-Level Architecture, Repository Directory Map, System Architecture Diagram (Mermaid), Technology Stack Summary, What Is RepoMind 2.0?

### Community 117 - "RepoMind — Security"
Cohesion: 0.15
Nodes (12): AI Security — Prompt Injection Protection, API Security, Application Security, Data Protection, Dependency Security, Explicit "Never" Constraints, GitHub API Security, Hallucination / Groundedness as a Trust Control (+4 more)

### Community 128 - "RepoMind — Testing Strategy"
Cohesion: 0.15
Nodes (13): AI Tests, API Tests, Backend Unit Tests, End-to-End Tests, Error Handling Matrix, Frontend Unit Tests, GitHub Integration Tests, Integration Tests (+5 more)

### Community 129 - "RepoMind — Operational Runbook"
Cohesion: 0.15
Nodes (13): Check Backend Health, Check Database, Inspect Failed AI Processing, Re-run a Review, Recover from Failed Jobs, RepoMind — Operational Runbook, Restart Services, Retrain ML Models (+5 more)

### Community 130 - "08 — Feature Flow: Conflict Detection Engine"
Cohesion: 0.14
Nodes (14): 08 — Feature Flow: Conflict Detection Engine, Conflict Lifecycle, `detect_conflicts()` Orchestrator, DetectedConflict Dataclass, Detector 1: Mechanical Conflicts, Detector 2: Architecture Conflicts, Detector 3: Security Policy Conflicts, Detector 4: API Contract Conflicts (+6 more)

### Community 131 - "17 — Security Architecture"
Cohesion: 0.17
Nodes (12): 10. PAT Logging Policy, 11. No Auto-Merge Policy, 17 — Security Architecture, 1. Password Security, 2. JWT Session Security, 3. PAT Encryption, 5. repository_id Authority, 6. RAG Repository Isolation (+4 more)

### Community 133 - "run_test_intelligence_analysis"
Cohesion: 0.29
Nodes (4): run_test_intelligence_analysis(), test_analyzer_detects_existing_test_mapping(), test_analyzer_empty_diff_returns_empty(), test_analyzer_identifies_modified_functions_and_generates_8_categories()

### Community 134 - "RepoMind 2.0 — System Architecture"
Cohesion: 0.17
Nodes (11): AI Layer, API Communication, Authentication Flow, Backend, Database, Frontend, Overall Architecture, PR Review Flow (+3 more)

### Community 135 - "RepoMind — Troubleshooting"
Cohesion: 0.17
Nodes (12): AI / LLM, Authentication, Backend, Embeddings, Frontend, GitHub API, Linter Execution, Migrations (+4 more)

### Community 136 - "21 — Final Feature Status Matrix"
Cohesion: 0.17
Nodes (12): 21 — Final Feature Status Matrix, AI Chat, Analytics, Core Features, GitHub Integration, ML Prediction, RAG Indexing, RepoMind 2.0 — Feature Implementation Status (+4 more)

### Community 137 - "retrieval.py"
Cohesion: 0.09
Nodes (15): classify_query(), extract_endpoints(), extract_files(), extract_pr_id(), extract_symbols(), ExtractedEntities, QueryIntent, MultiSourceContextRetriever (+7 more)

### Community 138 - "chat/routes.py"
Cohesion: 0.17
Nodes (11): assert_org_permission(), Permission, ChatMessageRequest, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse, get_chat_history(), list_chat_sessions() (+3 more)

### Community 139 - "RepositoryScanner"
Cohesion: 0.26
Nodes (3): RepositoryScanner, test_scanner_exclusion_rules(), test_scanner_language_and_framework_detection()

### Community 140 - "RepoMind — Authentication & Authorization"
Cohesion: 0.18
Nodes (10): Authentication Approach, Authorization Boundaries / Roles, Endpoint-Level Authorization (from `03-design/api-design.md`), GitHub Authentication / Integration, Organization / Team / Project Access, RepoMind — Authentication & Authorization, Repository Access, Sessions / Tokens (+2 more)

### Community 141 - "RepoMind — Secrets Management"
Cohesion: 0.18
Nodes (10): Database Credentials, `.env.example`, Environment Variables, GitHub Credentials / Tokens, LLM / API Keys, RepoMind — Secrets Management, Secret Storage — Local Development, Secret Storage — Production (+2 more)

### Community 142 - "RepoMind 2.0 — Deployment Guide (No Docker)"
Cohesion: 0.18
Nodes (11): Backend Deployment (Python Environment), Components to Deploy, Deployment Validation, Environment Variables, Frontend Build, HTTPS / Reverse Proxy, PostgreSQL (Native), Process Management (+3 more)

### Community 143 - "2. Phase-by-Phase Implementation Specifications"
Cohesion: 0.18
Nodes (10): 1. Upgrade Strategy & Phasing Overview, 2. Phase-by-Phase Implementation Specifications, 3. Summary of Deliverables & Verification Gates, Phase 1: Stabilization & Environment Baseline, Phase 2: Repository Intelligence & AST Graph Engine, Phase 3: Change Impact & Architecture Drift Analyzer, Phase 4: AI Test Intelligence & Technical Debt Engine, Phase 5: Historical Code Intelligence & Inline PR Comments (+2 more)

### Community 145 - "End-to-End Flow"
Cohesion: 0.20
Nodes (8): _safe_join(), 06 — Feature Flow: Static Analysis (Ruff + Bandit), Feature Summary, Linter Output in Evidence Validation, Security Properties, Step 3: Build Temporary Workspace, Review Pipeline, Security Risk Matrix

### Community 146 - "GitHubAPIError"
Cohesion: 0.07
Nodes (10): _get_token_for_identity(), process_automation_actions(), GitHubAPIError, GitHubTransientError, DocumentLoader, test_loader_exclusions(), test_loader_hashing(), Diagram — AI Review Pipeline (LLM) (+2 more)

### Community 148 - "RepoMind 2.0 — Project Overview"
Cohesion: 0.20
Nodes (9): Core Anti-Goals, Current Project Status, High-Level Workflow, Key Technologies, Main Capabilities, Problem Statement, RepoMind 2.0 — Project Overview, Target Users / Intended Usage (+1 more)

### Community 149 - "2. Analytics Queries"
Cohesion: 0.12
Nodes (16): 13 — Feature Flow: Analytics, 1. Frontend Request, 2. Analytics Queries, 3. Response, Base Query Setup, End-to-End Flow, Feature Summary, Key Files (+8 more)

### Community 150 - "_setup_repo_and_pr"
Cohesion: 0.43
Nodes (3): _setup_repo_and_pr(), test_review_comment_does_not_reset_completed_run_and_preserves_metrics(), test_valid_zero_metrics_not_ignored()

### Community 151 - "RiskAssessmentResponse"
Cohesion: 0.06
Nodes (15): ConflictResponse, Config, FindingResponse, Config, HumanDecisionRequest, HumanDecisionResponse, Config, ReviewRunResponse (+7 more)

### Community 152 - "RepoMind — Git Workflow"
Cohesion: 0.22
Nodes (8): Branch Strategy, Commit Conventions, Handling AI Prompt / Model Changes, Handling Database Migrations, Merge Strategy, Pull Requests and Code Review, Release / Versioning Approach, RepoMind — Git Workflow

### Community 153 - "RepoMind — Test Plan"
Cohesion: 0.22
Nodes (8): AI / RAG, Component-Level, Feature-Level, Integration-Level, ML, RepoMind — Test Plan, Security, System-Level

### Community 154 - "RepoMind — Database Migrations"
Cohesion: 0.22
Nodes (9): Alembic Workflow, Applying Migrations, Migration Creation, Migration Review, Migration Testing, Production Migration Precautions, RepoMind — Database Migrations, Rollback Strategy (+1 more)

### Community 155 - "get_user_by_email"
Cohesion: 0.50
Nodes (3): 3. Repository Indexing Flow, 5. PR Review Pipeline, Code Connection Map

### Community 156 - "Key Architectural Facts (Quick Reference)"
Cohesion: 0.29
Nodes (7): Auth, GitHub, Key Architectural Facts (Quick Reference), ML, RAG, Review Pipeline, Worker

### Community 158 - "Vector"
Cohesion: 0.36
Nodes (3): _has_vector_extension(), Vector, process()

### Community 159 - "RepoMind Intelligence 2.0 — Complete API Audit"
Cohesion: 0.40
Nodes (4): 1. Master API Route Catalog, 3.1 Mapping Inconsistencies Between `api.js` and FastAPI Endpoints, 3. Frontend Client Mapping & API Discrepancies, RepoMind Intelligence 2.0 — Complete API Audit

### Community 160 - "RepoMind 2.0 — UI Design"
Cohesion: 0.25
Nodes (7): Application Shell, Design System, Navigation, Page Hierarchy / Route Structure, RepoMind 2.0 — UI Design, Reusable / Feature Components — PR Review Page Breakdown, State Management

### Community 161 - "7 Weighted Factors"
Cohesion: 0.25
Nodes (8): 7 Weighted Factors, Factor 1: Security Exposure (Weight: 25%), Factor 2: Architecture Risk (Weight: 15%), Factor 3: Test Risk (Weight: 15%), Factor 4: Code Complexity (Weight: 20%), Factor 5: Change Size (Weight: 10%), Factor 6: Dependency Risk (Weight: 10%), Factor 7: Blast Radius (Weight: 5%)

### Community 162 - "`_validate_finding()` — Per-Finding Logic"
Cohesion: 0.40
Nodes (5): Check 1: Diff Verification (Hallucination Detection), Check 2: RAG Chunk Support, Check 3: Linter Confirmation, Evidence Status Assignment, `_validate_finding()` — Per-Finding Logic

### Community 163 - "RepoMind — Implementation Plan"
Cohesion: 0.29
Nodes (6): Definition of Done (applies to every phase/feature), Dependency Graph, Parallelization Notes, Phase Overview, Recommended Build Order (condensed), RepoMind — Implementation Plan

### Community 164 - "RepoMind — Scope"
Cohesion: 0.29
Nodes (6): Conflicts Resolved — Which Scope Is "Current", Future Scope, In Scope (Current Phase — Scope B, Internal Company MVP), MVP vs. Production Boundary, Out of Scope (Current Phase), RepoMind — Scope

### Community 165 - "Local development environment"
Cohesion: 0.29
Nodes (6): Backend, Environment Configuration, Frontend, Local development environment, PostgreSQL & pgvector, Running the Application

### Community 166 - "End-to-End Flow"
Cohesion: 0.20
Nodes (10): End-to-End Flow, Step 10: Commit and Return, Step 1: GitHub Sends Webhook, Step 3: HMAC-SHA256 Signature Verification, Step 4: Parse JSON Payload, Step 5: Deduplication by Delivery ID, Step 6: Resolve Repository, Step 7: Persist Webhook Event (+2 more)

### Community 167 - "RepoMind 2.0 — Requirements"
Cohesion: 0.33
Nodes (5): Core Mechanics, Functional Requirements, Non-Functional Requirements, RepoMind 2.0 — Requirements, Tech Stack Requirements

### Community 168 - "RepoMind 2.0 — API Design"
Cohesion: 0.33
Nodes (5): API Conventions, Authentication, Current APIs, Example — Review Run Response Shape, RepoMind 2.0 — API Design

### Community 169 - "RepoMind — Coding Standards"
Cohesion: 0.33
Nodes (5): AI / ML, Backend (Python / FastAPI), Frontend (TypeScript / React), General, RepoMind — Coding Standards

### Community 172 - "End-to-End Flow"
Cohesion: 0.40
Nodes (5): 1. View Completed Review, 2. Trigger Approve/Reject, 3. Authorization Check, 4. Persist Decision (Upsert), End-to-End Flow

### Community 175 - "RepoMind 2.0 Complete Technical Guide"
Cohesion: 0.17
Nodes (11): 10. Manager 1-Minute Explanation, 11. Manager Q&A, 12. Known Limitations & Remaining Work, 1. Executive Summary & Product Problem, 2. Technology Stack & High-level Architecture, 4. Frontend Architecture, 5. Backend Architecture & Complete Code Flow, 7. Repository Indexing, Chunking, and Embeddings (+3 more)

### Community 176 - "Diagram — PR Review Sequence"
Cohesion: 0.50
Nodes (3): Diagram — PR Review Sequence, Job State Machine, Re-analysis Sequence

### Community 177 - "Diagram — RAG Pipeline"
Cohesion: 0.50
Nodes (3): Diagram — RAG Pipeline, Indexing, Retrieval

### Community 187 - "_validate_single_finding"
Cohesion: 0.13
Nodes (5): _compute_relevance(), _find_linter_confirmation(), _find_supporting_chunks(), _validate_single_finding(), _verify_file_in_diff()

### Community 191 - "ChangeImpactAnalysis"
Cohesion: 0.14
Nodes (12): ChangeImpactAnalysis, _get_authorized_repo(), get_impact_analysis_by_id(), get_impact_graph(), get_latest_pr_impact(), trigger_impact_analysis(), AffectedComponentResponse, BreakingChangeResponse (+4 more)

### Community 192 - "TestScenario"
Cohesion: 0.24
Nodes (3): TestCodeGenerator, TestScenario, test_generator_creates_pending_test_case()

### Community 193 - "test_change_impact_analyzer.py"
Cohesion: 0.09
Nodes (16): DetectedCodeChanges, generate_impact_mermaid(), generate_test_recommendations(), run_change_impact_analysis(), AffectedComponent, _fallback_traversal(), TraversalResult, traverse_dependencies() (+8 more)

### Community 197 - "RepoMind Intelligence — Current System Architecture"
Cohesion: 0.17
Nodes (11): 1. High-Level System Architecture, 2. Technology Stack Specifications, 4.1 Authentication & Session Handling, 4.2 Role-Based Access Control (RBAC), 4. API Communication & Security Architecture, 5. Existing AI Pipeline & Review Execution, 6. Repository Indexing & Vector Search Workflow, 7. GitHub Webhook Ingestion Workflow (+3 more)

### Community 198 - "End-to-End Flow"
Cohesion: 0.12
Nodes (15): 11 — Feature Flow: AI Chat Assistant, 1. Create a Chat Session, 2. Send a Message, 4. Build Evidence + System Prompt, 5. Build User Content with History, 7. Persist Messages, 8. Return Response, API Endpoints (+7 more)

### Community 204 - "FindingSchema"
Cohesion: 0.07
Nodes (29): validate_findings(), ValidatedFinding, FindingEvidence, FindingSchema, compute_finding_fingerprint(), _persist_validated_findings(), is_match(), _make_validated_finding() (+21 more)

### Community 206 - "Repository Endpoints"
Cohesion: 0.67
Nodes (3): `POST /repositories/connect`, `POST /repositories/{id}/index`, Repository Endpoints

### Community 207 - "list_security_findings"
Cohesion: 0.22
Nodes (4): FindingStatusUpdate, list_security_findings(), SecurityFindingResponse, update_finding_status()

### Community 210 - "github/schemas.py"
Cohesion: 0.29
Nodes (5): connect_repository(), GitHubConnectRequest, PullRequestListResponse, PullRequestResponse, RepositoryConnectResponse

### Community 213 - "make_client_for_user"
Cohesion: 0.25
Nodes (5): make_client_for_user(), test_generate_and_execute_test_case_endpoints(), test_get_pr_test_scenarios_and_filtering(), test_get_test_dashboard_endpoint(), test_trigger_test_analysis_endpoint()

### Community 218 - "Things I Must Not Misunderstand"
Cohesion: 0.33
Nodes (5): Learning Checklist, Part 26 — Developer Mental Model, Part 27 — Glossary, Things I Must Not Misunderstand, Verification Snapshot

### Community 220 - ".embed_chunks"
Cohesion: 0.14
Nodes (9): EmbedderError, test_embedding_dimension(), test_embedder_validation(), Function: `chunk_text()`, Function: `embed_chunks()`, Function: `_should_exclude_path()`, Part 2 — Phase 6 Complete End-to-End Flow, Part 4 — Line-by-Line Code Teaching (+1 more)

## Knowledge Gaps
- **18 isolated node(s):** `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector`, `Per-User GitHub OAuth`, `Organization` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1684 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **93 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Repository` to `github/routes.py`, `organizations/routes.py`, `RoleEnum`, `fastapi_testclient`, `chat/routes.py`, `seed_demo_intelligence.py`, `GitHub API Client`, `test_review.py`, `test_architecture_intelligence.py`, `test_historical_intelligence.py`, `Organization API Schemas`, `review/router.py`, `Onboarding Authorization Tests`, `_get_authorized_repo`, `GitHubIdentity`, `PullRequest`, `auth/routes.py`, `index_repository`, `organizations/service.py`, `TestRepositoryConnect`, `ChangeImpactAnalysis`, `test_change_impact_analyzer.py`, `intelligence/routes.py`, `list_security_findings`, `github/schemas.py`, `permissions.py`, `sqlalchemy`, `Finding`, `pytest`, `test_pr_review_engine_upgrade.py`, `testing/routes.py`, `Directory Deep Dive`?**
  _High betweenness centrality (0.175) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `User` (e.g. with `get_org_analytics()` and `create_architecture_rule()`) actually correct?**
  _`User` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `api.js` be split into smaller, more focused modules?**
  _Cohesion score 0.10333333333333333 - nodes in this community are weakly interconnected._
- **Why does `Key Files` connect `permissions.py` to `Repository`, `App`, `RoleEnum`, `02 — Feature Flow: Authentication`, `chat/routes.py`, `auth/routes.py`?**
  _High betweenness centrality (0.148) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `Repository` (e.g. with `get_organization_analytics()` and `_get_authorized_repo()`) actually correct?**
  _`Repository` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.03980099502487562 - nodes in this community are weakly interconnected._