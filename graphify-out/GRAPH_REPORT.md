# Graph Report - Repo-Mind-  (2026-11-16)

## Corpus Check
- 439 files · ~253,769 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .bat 4, (none) 3, .ini 2)

## Summary
- 3615 nodes · 9306 edges · 244 communities (154 shown, 90 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1253 edges (avg confidence: 0.93)
- Token cost: 152,469 input · 7,531 output

## Graph Freshness
- Built from commit: `d5914d76`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Frontend Dependencies
- typing
- github/routes.py
- Repository
- test_review.py
- organizations/routes.py
- RoleEnum
- organizations/models.py
- Key Files
- chat/service.py
- analyzer.py
- ReviewRun
- github_webhook
- auth/service.py
- 2.3 Domain 3: Review & Risk Engine
- ReviewPage.jsx
- GitHub API Client
- 04 — Feature Flow: RAG Indexing
- re
- react
- OnboardingService
- Document
- test_review.py
- RepoMind Intelligence 2.0 — Development Handover Report
- RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough
- test_architecture_intelligence.py
- LanguageAwareParser
- 09 — Feature Flow: Risk Scoring Engine
- test_historical_intelligence.py
- history/routes.py
- Organization API Schemas
- Permission Normalization Tests
- review/router.py
- Onboarding Authorization Tests
- App
- test_linter.py
- DashboardPage.jsx
- _get_authorized_repo
- encrypt_token
- fixture
- re
- TextChunker
- sys
- TestIntelligenceDashboard.jsx
- github/service.py
- Detailed Step-by-Step
- GitHubAPIError
- calculate_risk
- RepoMind Phase 6–7 Complete Technical Walkthrough
- Step 2: Apply Gap Detection Categories
- auth/routes.py
- index_repository
- typing
- api.js
- review/service.py
- PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT
- organizations/service.py
- impact/engine.py
- Multi-tenant Security Tests
- json
- Final RBAC Parity & Feature Audit Report
- onboarding/routes.py
- RepoMind Intelligence 2.0 — Complete Technical Audit
- intelligence/routes.py
- GitHub OAuth Identity
- ML Training Service
- Background Workers
- Merge Policy Logic
- Repository Blueprinting
- RepoMind — Environment Configuration
- verify_org_member
- RepoMind — Monitoring & Observability
- UpdateProgressRequest
- RepoMind — Architecture Decision Record
- Review Pipeline: 11 Stages
- sqlalchemy
- 14 — Feature Flow: Background Worker
- test_change_impact_analyzer.py
- test_change_impact_analyzer.py
- RepoMind — Development Guide
- PullRequest
- Finding
- Key Architectural Facts (Quick Reference)
- 18 — Feature Flow: ML Prediction (PR Cycle Time)
- onboarding/service.py
- test_pr_review_engine_upgrade.py
- test_test_runner.py
- testing/routes.py
- _enqueue_review
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
- test_intelligence_routes.py
- RepoMind 2.0 — System Architecture
- RepoMind — Troubleshooting
- 21 — Final Feature Status Matrix
- .retrieve
- chat/routes.py
- RepositoryScanner
- RepoMind — Authentication & Authorization
- RepoMind — Secrets Management
- RepoMind 2.0 — Deployment Guide (No Docker)
- 2. Phase-by-Phase Implementation Specifications
- sparsevec.h
- End-to-End Flow
- DocumentLoader
- RepoMind 2.0 — Project Overview
- 2. Analytics Queries
- _get_authorized_repo
- RiskAssessmentResponse
- RepoMind — Git Workflow
- RepoMind — Test Plan
- RepoMind — Database Migrations
- get_user_by_email
- build_onboarding_user_content
- 1. Project Discovery & Layer Inspection
- Vector
- make_client_for_user
- RepoMind 2.0 — UI Design
- 7 Weighted Factors
- _extract_py_symbols_with_lines
- RepoMind — Implementation Plan
- RepoMind — Scope
- Local development environment
- End-to-End Flow
- RepoMind 2.0 — Requirements
- RepoMind 2.0 — API Design
- RepoMind — Coding Standards
- format_auth_response
- RepoMind 2.0 Complete Technical Guide
- Diagram — PR Review Sequence
- Diagram — RAG Pipeline
- PullRequestFile
- component-architecture.md
- data-flow.md
- deployment-architecture.md
- system-context.md
- test-cases.md
- 16 — API Endpoint Reference
- _validate_single_finding
- Settings
- encrypt_token
- ChangeImpactAnalysis
- TestScenario
- run_change_impact_analysis
- process_automation_actions
- RepoMind Intelligence — Current System Architecture
- End-to-End Flow
- FindingSchema
- LanguageAwareParser
- impact/schemas.py
- list_security_findings
- RepoMind 2.0 Feature Code Flow Walkthroughs
- _process_one_indexing_job
- github/schemas.py
- _extract_py_signatures
- make_client_for_user
- 13 — Feature Flow: Analytics
- Things I Must Not Misunderstand
- Part 4 — Line-by-Line Code Teaching
- Part 20 — Phase 7 Test-by-Test Walkthrough

## God Nodes (most connected - your core abstractions)
1. `User` - 190 edges
2. `Repository` - 144 edges
3. `ReviewRun` - 108 edges
4. `Project` - 107 edges
5. `PullRequest` - 106 edges
6. `Organization` - 98 edges
7. `OrganizationMembership` - 82 edges
8. `RoleEnum` - 74 edges
9. `react` - 74 edges
10. `run_review()` - 60 edges

## Surprising Connections (you probably didn't know these)
- `4.1 Authentication & Session Handling` --references--> `apiRequest()`  [INFERRED]
  Docs/CURRENT_ARCHITECTURE.md → frontend/src/lib/api.js
- `8. Return Response` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatMessage`` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- `Component-Level` --references--> `Finding`  [INFERRED]
  Docs/06-testing/test-plan.md → backend/app/review/models.py
- `Feature Summary` --references--> `ReviewRun`  [INFERRED]
  Docs/architecture/feature_flow_webhooks.md → backend/app/review/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GitHub OAuth Identity Linking** — repomind_2_0_architecture_flow_github_oauth, backend_app_github_oauth_routes_github_oauth_callback, backend_app_github_oauth_service_upsert_github_identity [EXTRACTED 1.00]
- **Developer Onboarding Subsystem** — walkthrough_repository_blueprint, walkthrough_user_onboarding_progress, walkthrough_onboarding_service [EXTRACTED 1.00]
- **RAG Indexing Pipeline** — backend_app_rag_loader, backend_app_rag_chunker, backend_app_rag_embedder, backend_app_rag_repository, postgresql_pgvector [EXTRACTED 1.00]

## Communities (244 total, 90 thin omitted)

### Community 1 - "Frontend Dependencies"
Cohesion: 0.04
Nodes (64): dependencies, mermaid@^12.3.0, react@^18.2.0, react-diff-viewer-continued@^4.4.0, react-dom@^18.2.0, react-markdown@^10.1.0, react-router-dom@^7.18.3, @tanstack/react-query@^5.102.8 (+56 more)

### Community 2 - "typing"
Cohesion: 0.04
Nodes (23): upgrade(), downgrade(), upgrade(), downgrade(), upgrade(), upgrade(), upgrade(), downgrade() (+15 more)

### Community 3 - "github/routes.py"
Cohesion: 0.12
Nodes (22): User, _assert_repo_access(), connect_repository(), get_merge_policy(), get_pull_request(), get_pull_request_commits(), get_pull_request_conflicts(), get_pull_request_events() (+14 more)

### Community 4 - "Repository"
Cohesion: 0.06
Nodes (37): Organization, OrganizationMembership, Project, ProjectMember, Repository, TeamMember, reset_database(), seed_database() (+29 more)

### Community 5 - "test_review.py"
Cohesion: 0.06
Nodes (24): FallbackProvider, GeminiProvider, retry_if_transient_error(), get_llm_provider(), GroqProvider, LLMProvider, LLMProviderError, LocalProvider (+16 more)

### Community 6 - "organizations/routes.py"
Cohesion: 0.20
Nodes (15): create_organization(), create_project(), create_repository(), create_team(), get_organization(), get_repository(), invite_member(), list_members() (+7 more)

### Community 7 - "RoleEnum"
Cohesion: 0.16
Nodes (16): RoleEnum, run_decision_test(), test_approve_developer(), test_approve_org_admin(), test_approve_reviewer(), test_approve_team_lead(), test_reject_developer(), test_reject_org_admin() (+8 more)

### Community 8 - "organizations/models.py"
Cohesion: 0.11
Nodes (8): extract_token_from_request(), get_current_user(), get_db(), test_bootstrap_flow(), test_onboard_and_change_password_flow(), cleanup_overrides(), cleanup_overrides(), test_organization_membership_roles()

### Community 9 - "Key Files"
Cohesion: 0.14
Nodes (15): authenticate_user(), 02 — Feature Flow: Authentication, 2. Login, 3. Session Restoration (Page Reload), 4. Logout, Backend (Canonical), Data Flow Diagram (Mermaid), End-to-End Flow (+7 more)

### Community 10 - "chat/service.py"
Cohesion: 0.12
Nodes (15): ChatMessage, ChatSession, _build_grounded_mock_response(), create_session(), get_session_messages(), get_sessions(), send_message(), test_chat_service_generates_grounded_response_with_citations() (+7 more)

### Community 11 - "analyzer.py"
Cohesion: 0.13
Nodes (5): run_test_intelligence_analysis(), TestIntelligenceAnalyzer, test_analyzer_detects_existing_test_mapping(), test_analyzer_empty_diff_returns_empty(), test_analyzer_identifies_modified_functions_and_generates_8_categories()

### Community 12 - "ReviewRun"
Cohesion: 0.07
Nodes (26): ReviewRun, _update_progress(), test_get_review_run(), test_get_review_run_cross_tenant(), test_trigger_review_creates_pending_job_and_returns_202(), test_trigger_review_duplicate_returns_idempotent(), _setup_repo_and_pr(), test_gap_08_completed_historical_runs_are_preserved() (+18 more)

### Community 13 - "github_webhook"
Cohesion: 0.14
Nodes (10): github_webhook(), _resolve_repository(), 12 — Feature Flow: GitHub Webhook Automation, Configuration Required, Feature Summary, Key Files, Security Properties, Step 2: Raw Body Read (Before JSON Parsing) (+2 more)

### Community 14 - "auth/service.py"
Cohesion: 0.20
Nodes (11): bootstrap_system(), create_access_token(), decode_access_token(), get_user_by_id(), hash_invitation_token(), hash_password(), onboard_user(), verify_password() (+3 more)

### Community 15 - "2.3 Domain 3: Review & Risk Engine"
Cohesion: 0.05
Nodes (43): 1.1 Domain Table Breakdown, 1. Complete Database Schema Inventory, 2.1 Domain 1: Authentication & Multi-Tenant Hierarchy, 2.2 Domain 2: GitHub Integration & Pull Requests, 2.3 Domain 3: Review & Risk Engine, 2.4 Domain 4: Code-Aware RAG & pgvector Storage, 2.5 Domain 5: Collaboration & Developer Onboarding, 2.6 Domain 6: Webhooks, Audit & ML (+35 more)

### Community 16 - "ReviewPage.jsx"
Cohesion: 0.12
Nodes (23): ActivityLog(), ConflictCard(), ConflictList(), EvidenceStatus(), FindingCard(), LifecycleBadge(), FindingList(), SEV_ORDER (+15 more)

### Community 17 - "GitHub API Client"
Cohesion: 0.10
Nodes (5): GitHubClient, reconcile_pull_requests(), connect_repository(), get_github_repositories(), sync_pull_request_details()

### Community 18 - "04 — Feature Flow: RAG Indexing"
Cohesion: 0.25
Nodes (7): 04 — Feature Flow: RAG Indexing, Crash Recovery, Database Tables, Embedding Model Details, Feature Summary, RAG Retrieval (used during review), Trigger Chain

### Community 19 - "re"
Cohesion: 0.12
Nodes (10): classify_query(), extract_endpoints(), extract_files(), extract_pr_id(), extract_symbols(), QueryIntent, ReviewDecisionAction, test_chat_api_route_e2e_grounded_response() (+2 more)

### Community 20 - "react"
Cohesion: 0.08
Nodes (36): ArchitectureDashboard(), ArchitectureHealthOverview(), ArchitectureRuleManager(), ArchitectureViolationsList(), CircularDependencyGraph(), FlowAnalysisViewer(), EdgeDetailsModal(), EngineeringGraphEngine() (+28 more)

### Community 21 - "OnboardingService"
Cohesion: 0.12
Nodes (12): RepositoryBlueprint, BlueprintGenerationError, OnboardingService, test_duplicate_concurrent_generation_prevention(), test_failed_regeneration_preserves_previous_valid_blueprint(), test_generation_and_cache_hit(), test_grounding_rejects_fabricated_request_flow_path(), test_stale_pending_job_recovery() (+4 more)

### Community 22 - "Document"
Cohesion: 0.04
Nodes (33): RepositoryIndexer, PackageDependency, RepositoryScanSummary, GithubConnection, EmbedderError, LocalEmbedder, Document, DocumentChunk (+25 more)

### Community 23 - "test_review.py"
Cohesion: 0.06
Nodes (24): LLMOutputParseError, parse_llm_output(), ReviewOutput, test_malformed_ai_output_parsing(), FailingProvider, FakeProvider, test_a_valid_output_creates_completed_run(), test_b_malformed_json_both_attempts_fail() (+16 more)

### Community 24 - "RepoMind Intelligence 2.0 — Development Handover Report"
Cohesion: 0.05
Nodes (40): 10. AI Chat Assistant (`/chat`), 11. AI Test Intelligence (`/repositories/{id}/test-intelligence`, `/test-scenarios`, `/generated-tests`, `/test-intelligence`), 12. Technical Debt Intelligence (`/repositories/{id}/tech-debt`), 13. Security & Analytics (`/security`, `/analytics`), 1. Health & Core, 2. Advanced AI Pull Request Intelligence (`backend/app/review/analysis.py`, `service.py`, `evidence.py`), 2. Authentication & Memberships (`/auth`), 3. Change Impact & Blast Radius Analyzer (`backend/app/impact/`) (+32 more)

### Community 25 - "RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough"
Cohesion: 0.05
Nodes (39): 10. Complete API Reference, 11. Role Hierarchy & Repository Authorization, 12. Private Progress & Anti-Surveillance Guarantees, 13. Frontend Component & Routing Architecture, 14. Mermaid Rendering Security, 15. Developer Onboarding User Journey, 16. Team Lead Refresh User Journey, 17. Testing Commands & Actual Results (+31 more)

### Community 26 - "test_architecture_intelligence.py"
Cohesion: 0.07
Nodes (27): check_architecture_rules(), GroundedViolation, _matches_pattern(), CircularDependency, detect_circular_dependencies(), calculate_architecture_health_score(), generate_architecture_mermaid(), FlowAnalysisResult (+19 more)

### Community 29 - "09 — Feature Flow: Risk Scoring Engine"
Cohesion: 0.17
Nodes (12): 09 — Feature Flow: Risk Scoring Engine, Blast Radius and Test Impact, `_calculate_blast_radius(changed_files)` returns:, `calculate_risk()` Structure, `_calculate_test_impact(changed_files, diff)` returns:, Entry Point, Fairness Rule, Feature Summary (+4 more)

### Community 30 - "test_historical_intelligence.py"
Cohesion: 0.07
Nodes (21): compute_and_index_hotspots(), _extract_adrs_from_markdown(), _infer_modules_from_title_and_text(), mine_and_index_commits(), parse_and_index_adrs(), ArchitectureDecisionRecord, HistoricalCommitRecord, RecurringIssueHotspot (+13 more)

### Community 31 - "history/routes.py"
Cohesion: 0.17
Nodes (16): ADRResponse, ChangeComparisonItem, ChangeComparisonRequest, ChangeComparisonResponse, HistoricalCommitResponse, HistoricalIndexRequest, HistoricalIndexResponse, HistoricalPRResponse (+8 more)

### Community 32 - "Organization API Schemas"
Cohesion: 0.17
Nodes (20): GithubConnectionBase, GithubConnectionCreate, GithubConnectionResponse, MemberBase, MemberInvite, MemberRoleUpdate, OrganizationBase, OrganizationCreate (+12 more)

### Community 33 - "Permission Normalization Tests"
Cohesion: 0.14
Nodes (6): test_def_02_action_casing_cannot_bypass_approve_permission(), override_db(), override_user(), test_def_02_arbitrary_unsupported_action_rejected(), test_def_02_lead_approve_normalized_and_triggers_merge_policy(), test_def_06_missing_pull_request_returns_404_no_500()

### Community 34 - "review/router.py"
Cohesion: 0.07
Nodes (24): HumanReview, get_pull_request_diff(), get_repository_by_id(), decide_review_run(), get_review_run(), get_review_run_decisions(), list_review_runs(), trigger_review() (+16 more)

### Community 36 - "Onboarding Authorization Tests"
Cohesion: 0.20
Nodes (17): UserOnboardingProgress, cleanup_overrides(), make_client_for_user(), test_10_invalid_track_and_milestone_ids_are_rejected(), test_11_repository_access_enforced_across_all_endpoints(), test_12_active_generation_conflict_returns_409(), test_13_unindexed_repository_error_returns_400(), test_14_responses_do_not_leak_internal_prompts_or_traces() (+9 more)

### Community 37 - "App"
Cohesion: 0.10
Nodes (28): 19 — Feature Flow: Frontend Application, `App.jsx` — Root Component, Application Entry Point, Feature Summary, Key Files Summary, Layout Structure, `lib/api.js` — API Wrapper, `ProtectedRoute` Component (+20 more)

### Community 38 - "test_linter.py"
Cohesion: 0.08
Nodes (17): _persist_failure(), _persist_result(), run_linters(), BanditLinter, LinterTool, RuffLinter, LinterResult, test_failed_tool_execution_preserves_error_signal() (+9 more)

### Community 39 - "DashboardPage.jsx"
Cohesion: 0.10
Nodes (28): Page Components, LoginForm(), ChatAssistant(), SOURCE_TYPE_STYLES, SUPPORTED_QUESTIONS, MetricCard(), SectionCard(), CardListSkeleton() (+20 more)

### Community 40 - "_get_authorized_repo"
Cohesion: 0.09
Nodes (24): ensure_baseline_architecture_rules(), run_architecture_analysis(), ArchitectureAnalysis, ArchitectureRule, ArchitectureViolation, create_architecture_rule(), delete_architecture_rule(), get_architecture_flows() (+16 more)

### Community 41 - "encrypt_token"
Cohesion: 0.09
Nodes (15): decrypt_token(), _get_fernet(), sync_pull_requests(), test_token_refresh_lifecycle(), TestTokenEncryption, 03 — Feature Flow: GitHub Repository Connection & Sync, 2. PR Sync (called after connect and on-demand), 3. PAT Decryption on Demand (+7 more)

### Community 43 - "re"
Cohesion: 0.18
Nodes (12): _detect_api_contract_conflicts(), _detect_architecture_conflicts(), _detect_configuration_conflicts(), detect_conflicts(), _detect_mechanical_conflicts(), _detect_security_policy_conflicts(), _detect_test_contract_conflicts(), DetectedConflict (+4 more)

### Community 44 - "TextChunker"
Cohesion: 0.13
Nodes (6): ASTChunk, ASTCodeChunker, TextChunker, test_chunker_determinism_and_overlap(), `backend/app/rag/chunker.py`, 1.9 RAG Implementation & Vector Database

### Community 45 - "sys"
Cohesion: 0.08
Nodes (7): get_decrypted_github_token_for_user(), main(), reset_db(), get_auth_token(), test_oauth_routes(), run_test(), test_phase3()

### Community 46 - "TestIntelligenceDashboard.jsx"
Cohesion: 0.21
Nodes (10): TestCodeViewer(), TestExecutionResult(), CATEGORIES, TestIntelligenceDashboard(), CATEGORY_THEMES, PRIORITY_BADGES, TestScenarioCard(), testingApi (+2 more)

### Community 47 - "github/service.py"
Cohesion: 0.11
Nodes (15): GitHubComment, GitHubRepositoryAccess, GitHubReview, PullRequestCheck, PullRequestEvent, WebhookEvent, get_decrypted_github_token_for_org(), get_github_connection_for_org() (+7 more)

### Community 48 - "Detailed Step-by-Step"
Cohesion: 0.18
Nodes (11): Detailed Step-by-Step, Step 10: Persist Chunks (with stale-chunk deletion), Step 11: Final Commit, Step 2: Setup — Decrypt PAT & Initialize Components, Step 3: Discover Documents, Step 4: Load Document Content, Step 5: Hash for Idempotency, Step 6: Save Document Metadata (+3 more)

### Community 49 - "GitHubAPIError"
Cohesion: 0.18
Nodes (3): GitHubAPIError, GitHubTransientError, GitHub Client API Calls

### Community 50 - "calculate_risk"
Cohesion: 0.05
Nodes (18): _extract_linter_issues(), _calculate_blast_radius(), calculate_risk(), _calculate_test_impact(), _generate_summary(), RiskResult, _score_architecture(), _score_change_size() (+10 more)

### Community 51 - "RepoMind Phase 6–7 Complete Technical Walkthrough"
Cohesion: 0.08
Nodes (26): `backend/app/rag/service.py`, Executive Summary, Part 10 — PostgreSQL + pgvector Internal Understanding, Part 12 — Phase 7 Overview, Part 13 — Phase 7 End-to-End Retrieval Flow, Part 14 — Retriever Code Deep Dive, Part 15 — Cosine Retrieval, Part 16 — top_k (+18 more)

### Community 52 - "Step 2: Apply Gap Detection Categories"
Cohesion: 0.08
Nodes (24): A. Entry and Exit Conditions, Analyzing Business Logic Gaps, B. State Definitions, C. State Transitions, Checklist for Quick Analysis, Common Gap Patterns, D. Exceptional Paths, E. Billing and Credit Rules (+16 more)

### Community 53 - "auth/routes.py"
Cohesion: 0.29
Nodes (14): change_password_route(), AuthResponse, BootstrapRequest, MembershipResponse, OnboardRequest, OrganizationResponse, PasswordChangeRequest, UserLogin (+6 more)

### Community 54 - "index_repository"
Cohesion: 0.40
Nodes (3): index_repository(), Part 6 — Hashing, Key Files

### Community 55 - "typing"
Cohesion: 0.04
Nodes (10): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade() (+2 more)

### Community 56 - "api.js"
Cohesion: 0.09
Nodes (47): App(), queryClient, RepositoryNav(), ROLE_LABELS, ROLES, TeamManagement(), Badge(), StatusBadge() (+39 more)

### Community 57 - "review/service.py"
Cohesion: 0.10
Nodes (17): AIAnalysis, derive_query_from_diff(), retrieve_context(), Conflict, _mark_failed(), _persist_conflicts(), _persist_risk(), run_review() (+9 more)

### Community 58 - "PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT"
Cohesion: 0.15
Nodes (12): 10. Defects and Fixes, 11. External Limitations, 12. Conclusion, 1. Objective and Scope, 2. Runtime and Initialization, 3. Authentication & RBAC, 5. Repository Discovery and Connection, 6. Webhook and Review Pipeline (E2E) (+4 more)

### Community 59 - "organizations/service.py"
Cohesion: 0.16
Nodes (19): AuditLog, Team, add_member(), create_organization(), create_project(), create_repository(), create_team(), get_members() (+11 more)

### Community 60 - "impact/engine.py"
Cohesion: 0.23
Nodes (5): ChangedSymbol, detect_code_changes(), _detect_symbols_from_diff_hunks(), DetectedCodeChanges, test_ast_change_detection_functions_and_classes()

### Community 62 - "Multi-tenant Security Tests"
Cohesion: 0.29
Nodes (4): test_chat_session_creation_rejects_foreign_repository(), test_def_04_cross_tenant_chat_retrieval_prevented(), override_db(), override_user()

### Community 63 - "json"
Cohesion: 0.13
Nodes (8): main(), test_multi_stage_review_8_categories_validation(), compute_signature(), test_concurrent_requests_with_same_delivery_id_handled_safely(), test_different_delivery_ids_processed_independently(), test_invalid_webhook_signature_rejected(), test_retry_after_processing_failure_succeeds_without_duplicate_records(), test_same_delivery_received_twice_is_idempotent()

### Community 64 - "Final RBAC Parity & Feature Audit Report"
Cohesion: 0.10
Nodes (17): 4-Role RBAC Model, A. Exact backend roles discovered, B. Four-role mapping, C. Backend permission matrix, D. Frontend permission matrix, E. Feature parity matrix, F. Organization Admin coverage, Final RBAC Parity & Feature Audit Report (+9 more)

### Community 65 - "onboarding/routes.py"
Cohesion: 0.12
Nodes (11): get_role_permissions(), Permission, _get_repo_and_verify_access(), get_repository_blueprint(), get_user_onboarding_progress(), refresh_repository_blueprint(), update_user_onboarding_progress(), GenerationInProgressError (+3 more)

### Community 66 - "RepoMind Intelligence 2.0 — Complete Technical Audit"
Cohesion: 0.20
Nodes (9): 2.1 Critical Runtime & Dependency Issues, 2.2 Model & Architectural Inconsistencies, 2.3 Mock & Incomplete Endpoints, 2.4 Frontend Test Failures, 2. Technical Audit Findings & Discrepancies, 3. Technology Stack Verification, 4. Conclusion & Audit Sign-Off, Executive Summary (+1 more)

### Community 67 - "intelligence/routes.py"
Cohesion: 0.19
Nodes (15): DependencyExtractor, get_architecture_diagram(), _get_authorized_repo(), get_repository_dependencies(), get_repository_graph(), get_repository_summary(), get_repository_symbols(), trigger_intelligence_indexing() (+7 more)

### Community 89 - "RepoMind — Environment Configuration"
Cohesion: 0.33
Nodes (5): Development, Production, RepoMind — Environment Configuration, Testing / CI, Variables

### Community 90 - "verify_org_member"
Cohesion: 0.05
Nodes (32): assert_org_permission(), check_org_permission(), _get_current_user_lazy(), require_org_permission(), _check(), require_permission(), _check(), role_has_permission() (+24 more)

### Community 91 - "RepoMind — Monitoring & Observability"
Cohesion: 0.15
Nodes (12): AI Failures, API Errors, Application Logs, Database Health, GitHub Integration Failures, ML Failures, Performance Metrics, RAG Failures (+4 more)

### Community 93 - "RepoMind — Architecture Decision Record"
Cohesion: 0.11
Nodes (17): ADR-001 — Modular Monolith Architecture, ADR-002 — Frontend: React + TypeScript + Tailwind, ADR-003 — Backend: FastAPI + Pydantic, ADR-004 — Database: PostgreSQL + SQLAlchemy + Alembic, ADR-005 — Vector Storage: pgvector (not a dedicated vector database), ADR-006 — Embeddings: sentence-transformers (local), ADR-007 — Retrieval Mechanism: pgvector Cosine Similarity, Repository-Scoped, ADR-008 — GitHub Integration Strategy: PAT + REST API (Phase 1) (+9 more)

### Community 94 - "Review Pipeline: 11 Stages"
Cohesion: 0.09
Nodes (16): build_user_content(), test_f_prompt_injection_framing(), 05 — Feature Flow: PR Review Pipeline (Full 11-Stage), Data Flow Diagram (Mermaid), Review Pipeline: 11 Stages, Stage 11: Mark Completed, Stage 1: Resolve PR + Repository (DB Authoritative), Stage 2: Create ReviewRun (pending → running) (+8 more)

### Community 95 - "sqlalchemy"
Cohesion: 0.06
Nodes (13): run_migrations_offline(), run_migrations_online(), downgrade(), upgrade(), downgrade(), upgrade(), downgrade(), upgrade() (+5 more)

### Community 96 - "14 — Feature Flow: Background Worker"
Cohesion: 0.12
Nodes (15): 14 — Feature Flow: Background Worker, Configuration, Consecutive Error Tracking, Error Handling, Feature Summary, Job Lifecycle States, LLM Provider Initialization, Parallelism Support (+7 more)

### Community 97 - "test_change_impact_analyzer.py"
Cohesion: 0.14
Nodes (9): BreakingChange, _check_signature_compatibility(), detect_breaking_changes(), _detect_breaking_from_diff_lines(), _detect_configuration_breaks(), _detect_database_schema_breaks(), test_database_model_column_dropped_is_breaking(), test_detect_breaking_signature_mutations() (+1 more)

### Community 98 - "test_change_impact_analyzer.py"
Cohesion: 0.07
Nodes (22): AffectedComponent, _fallback_traversal(), TraversalResult, traverse_dependencies(), CodeKnowledgeGraph, CodeGraphEdge, CodeGraphNode, extract_pr_analysis_context() (+14 more)

### Community 99 - "RepoMind — Development Guide"
Cohesion: 0.13
Nodes (14): Backend Setup (Python / FastAPI), Database Initialization and Migrations, Environment Variables, Frontend Setup, Linting and Formatting, No Docker, PostgreSQL Setup (Native), RepoMind — Development Guide (+6 more)

### Community 100 - "PullRequest"
Cohesion: 0.17
Nodes (11): get_organization_analytics(), PullRequest, RiskAssessment, _setup_org_project_repo(), test_gap_13_analytics_counts_distinct_prs_not_all_runs(), test_gap_13_higher_id_completed_earlier_lower_id_completed_later(), test_gap_13_pr_without_completed_runs_excluded_from_reviews(), test_gap_13_time_window_boundary_filtering() (+3 more)

### Community 102 - "Finding"
Cohesion: 0.06
Nodes (46): evaluate_merge_policy(), AutomationAction, Finding, FindingEvidence, HumanDecision, 10 — Feature Flow: Human Review Approval Gate, 1. View Completed Review, 2. Trigger Approve/Reject (+38 more)

### Community 103 - "Key Architectural Facts (Quick Reference)"
Cohesion: 0.14
Nodes (14): Auth, Documentation Set, Documents, Feature Flows (Start-to-End Traces), GitHub, Key Architectural Facts (Quick Reference), ML, RAG (+6 more)

### Community 104 - "18 — Feature Flow: ML Prediction (PR Cycle Time)"
Cohesion: 0.11
Nodes (17): 18 — Feature Flow: ML Prediction (PR Cycle Time), 1. API Request, 2. Training Data Check, 3. Rule-Based Baseline, 4. Response, Current State (as observed in source), Data Model, Dataset Building (+9 more)

### Community 105 - "onboarding/service.py"
Cohesion: 0.14
Nodes (17): CautionZone, ExecutionFlows, ExecutionFlowStep, GlossaryItem, LLMBlueprintPayload, MilestoneItem, ReadingOrderItem, RepositoryBlueprintResponse (+9 more)

### Community 106 - "test_pr_review_engine_upgrade.py"
Cohesion: 0.10
Nodes (15): encrypt_token(), GitHubCredential, GitHubIdentity, _get_system_user_id_for_repo(), _verify_github_signature(), api_test_data(), auth_client(), auth_client2() (+7 more)

### Community 107 - "test_test_runner.py"
Cohesion: 0.20
Nodes (7): GeneratedTestCase, IsolatedTestRunner, review_code_security(), test_runner_blocks_malicious_code_and_marks_error(), test_runner_captures_assertion_failure_without_false_pass(), test_runner_executes_safe_test_and_captures_pass(), test_security_review_detects_dangerous_calls()

### Community 108 - "testing/routes.py"
Cohesion: 0.17
Nodes (13): execute_generated_test(), generate_test_case(), _get_authorized_repo(), get_pr_test_scenarios(), get_test_dashboard(), trigger_test_analysis(), ExistingTestFileSummary, GeneratedTestCaseResponse (+5 more)

### Community 109 - "_enqueue_review"
Cohesion: 0.28
Nodes (5): _enqueue_review(), _upsert_pr_from_webhook(), test_gap_08_concurrent_duplicate_webhooks_serialization(), deliver_webhook(), Step 9: Enqueue Review for pull_request Events

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
Cohesion: 0.26
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
Cohesion: 0.15
Nodes (13): 08 — Feature Flow: Conflict Detection Engine, Conflict Lifecycle, `detect_conflicts()` Orchestrator, Detector 1: Mechanical Conflicts, Detector 2: Architecture Conflicts, Detector 3: Security Policy Conflicts, Detector 4: API Contract Conflicts, Detector 5: Test Contract Conflicts (+5 more)

### Community 131 - "17 — Security Architecture"
Cohesion: 0.15
Nodes (13): 10. PAT Logging Policy, 11. No Auto-Merge Policy, 17 — Security Architecture, 1. Password Security, 2. JWT Session Security, 3. PAT Encryption, 4. LLM Security: System Prompt Separation, 5. repository_id Authority (+5 more)

### Community 133 - "test_intelligence_routes.py"
Cohesion: 0.27
Nodes (8): make_client_for_user(), test_get_architecture_diagram(), test_get_dependencies(), test_get_graph_and_filtering(), test_get_summary_authorized(), test_get_summary_cross_tenant_forbidden(), test_get_symbols_search(), test_trigger_indexing_endpoint()

### Community 134 - "RepoMind 2.0 — System Architecture"
Cohesion: 0.17
Nodes (11): AI Layer, API Communication, Authentication Flow, Backend, Database, Frontend, Overall Architecture, PR Review Flow (+3 more)

### Community 135 - "RepoMind — Troubleshooting"
Cohesion: 0.13
Nodes (12): AI / LLM, Authentication, Backend, Embeddings, Frontend, GitHub API, Linter Execution, Migrations (+4 more)

### Community 136 - "21 — Final Feature Status Matrix"
Cohesion: 0.17
Nodes (12): 21 — Final Feature Status Matrix, AI Chat, Analytics, Core Features, GitHub Integration, ML Prediction, RAG Indexing, RepoMind 2.0 — Feature Implementation Status (+4 more)

### Community 137 - ".retrieve"
Cohesion: 0.15
Nodes (6): ExtractedEntities, MultiSourceContextRetriever, test_dependency_graph_and_call_chain_retrieval(), test_multi_source_retriever_pulls_all_sources(), test_pr_review_rationale_retrieval(), test_test_coverage_retrieval()

### Community 138 - "chat/routes.py"
Cohesion: 0.20
Nodes (8): ChatMessageRequest, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse, get_chat_history(), list_chat_sessions(), post_chat_message(), start_chat_session()

### Community 139 - "RepositoryScanner"
Cohesion: 0.27
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
Cohesion: 0.12
Nodes (16): _safe_join(), 06 — Feature Flow: Static Analysis (Ruff + Bandit), End-to-End Flow, Feature Summary, Linter Output in Evidence Validation, Security Properties, Step 1: Entry Point, Step 2: Fetch PR File Metadata (+8 more)

### Community 146 - "DocumentLoader"
Cohesion: 0.15
Nodes (6): DocumentLoader, test_loader_exclusions(), test_loader_hashing(), Diagram — AI Review Pipeline (LLM), `backend/app/rag/loader.py`, Function: `_should_exclude_path()`

### Community 148 - "RepoMind 2.0 — Project Overview"
Cohesion: 0.20
Nodes (9): Core Anti-Goals, Current Project Status, High-Level Workflow, Key Technologies, Main Capabilities, Problem Statement, RepoMind 2.0 — Project Overview, Target Users / Intended Usage (+1 more)

### Community 149 - "2. Analytics Queries"
Cohesion: 0.20
Nodes (10): 1. Frontend Request, 2. Analytics Queries, 3. Response, Base Query Setup, End-to-End Flow, Metric 1: Total PRs Reviewed, Metric 2: Average Risk Score, Metric 3: Findings by Severity (+2 more)

### Community 150 - "_get_authorized_repo"
Cohesion: 0.17
Nodes (8): compare_change_with_history(), get_architecture_decision_records(), _get_authorized_repo(), get_historical_prs(), get_previous_changes(), get_recurring_issue_hotspots(), get_similar_bugs(), trigger_historical_index()

### Community 151 - "RiskAssessmentResponse"
Cohesion: 0.13
Nodes (4): FindingResponse, Config, RiskAssessmentResponse, Config

### Community 152 - "RepoMind — Git Workflow"
Cohesion: 0.22
Nodes (8): Branch Strategy, Commit Conventions, Handling AI Prompt / Model Changes, Handling Database Migrations, Merge Strategy, Pull Requests and Code Review, Release / Versioning Approach, RepoMind — Git Workflow

### Community 153 - "RepoMind — Test Plan"
Cohesion: 0.22
Nodes (8): AI / RAG, Component-Level, Feature-Level, Integration-Level, ML, RepoMind — Test Plan, Security, System-Level

### Community 154 - "RepoMind — Database Migrations"
Cohesion: 0.17
Nodes (9): Alembic Workflow, Applying Migrations, Migration Creation, Migration Review, Migration Testing, Production Migration Precautions, RepoMind — Database Migrations, Rollback Strategy (+1 more)

### Community 155 - "get_user_by_email"
Cohesion: 0.33
Nodes (5): get_user_by_email(), 1. Login & Authentication Flow, 3. Repository Indexing Flow, 5. PR Review Pipeline, Code Connection Map

### Community 157 - "1. Project Discovery & Layer Inspection"
Cohesion: 0.22
Nodes (9): 1.10 Background Jobs & Worker Service, 1.11 Tests & Quality Assurance, 1.1 Frontend Structure, 1.2 Backend Structure, 1.3 Database Models & Schema, 1.4 Database Migrations, 1.5 API Routes & Endpoints, 1.7 GitHub Integration (+1 more)

### Community 158 - "Vector"
Cohesion: 0.36
Nodes (3): _has_vector_extension(), Vector, process()

### Community 159 - "make_client_for_user"
Cohesion: 0.25
Nodes (3): make_client_for_user(), test_impact_api_tenant_isolation(), test_impact_api_trigger_and_get()

### Community 160 - "RepoMind 2.0 — UI Design"
Cohesion: 0.25
Nodes (7): Application Shell, Design System, Navigation, Page Hierarchy / Route Structure, RepoMind 2.0 — UI Design, Reusable / Feature Components — PR Review Page Breakdown, State Management

### Community 161 - "7 Weighted Factors"
Cohesion: 0.25
Nodes (8): 7 Weighted Factors, Factor 1: Security Exposure (Weight: 25%), Factor 2: Architecture Risk (Weight: 15%), Factor 3: Test Risk (Weight: 15%), Factor 4: Code Complexity (Weight: 20%), Factor 5: Change Size (Weight: 10%), Factor 6: Dependency Risk (Weight: 10%), Factor 7: Blast Radius (Weight: 5%)

### Community 162 - "_extract_py_symbols_with_lines"
Cohesion: 0.38
Nodes (4): _extract_py_symbols_with_lines(), _record_func(), visit_AsyncFunctionDef(), visit_FunctionDef()

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
Cohesion: 0.22
Nodes (9): End-to-End Flow, Step 10: Commit and Return, Step 1: GitHub Sends Webhook, Step 3: HMAC-SHA256 Signature Verification, Step 4: Parse JSON Payload, Step 5: Deduplication by Delivery ID, Step 6: Resolve Repository, Step 7: Persist Webhook Event (+1 more)

### Community 167 - "RepoMind 2.0 — Requirements"
Cohesion: 0.33
Nodes (5): Core Mechanics, Functional Requirements, Non-Functional Requirements, RepoMind 2.0 — Requirements, Tech Stack Requirements

### Community 168 - "RepoMind 2.0 — API Design"
Cohesion: 0.33
Nodes (5): API Conventions, Authentication, Current APIs, Example — Review Run Response Shape, RepoMind 2.0 — API Design

### Community 169 - "RepoMind — Coding Standards"
Cohesion: 0.33
Nodes (5): AI / ML, Backend (Python / FastAPI), Frontend (TypeScript / React), General, RepoMind — Coding Standards

### Community 172 - "format_auth_response"
Cohesion: 0.23
Nodes (11): bootstrap(), format_auth_response(), get_me(), login(), logout(), onboard(), set_session_cookie(), Authentication Endpoints (+3 more)

### Community 175 - "RepoMind 2.0 Complete Technical Guide"
Cohesion: 0.12
Nodes (15): 10. Manager 1-Minute Explanation, 11. Manager Q&A, 12. Known Limitations & Remaining Work, 1. Executive Summary & Product Problem, 2. Technology Stack & High-level Architecture, 4. Frontend Architecture, 5. Backend Architecture & Complete Code Flow, 6. Authentication, Security & Credential Expiry (+7 more)

### Community 176 - "Diagram — PR Review Sequence"
Cohesion: 0.50
Nodes (3): Diagram — PR Review Sequence, Job State Machine, Re-analysis Sequence

### Community 177 - "Diagram — RAG Pipeline"
Cohesion: 0.50
Nodes (3): Diagram — RAG Pipeline, Indexing, Retrieval

### Community 178 - "PullRequestFile"
Cohesion: 0.29
Nodes (4): PullRequestCommit, PullRequestFile, history_setup(), 10. Repository-Aware AI Assistant Upgrade (`backend/app/chat/`, `frontend/src/components/Review/ChatAssistant.jsx`)

### Community 186 - "16 — API Endpoint Reference"
Cohesion: 0.14
Nodes (11): get_org_analytics(), 16 — API Endpoint Reference, All Registered API Endpoints, Analytics Endpoints, Common Response Codes, CORS Configuration, `GET /repositories/{id}/pull-requests`, Global API Base URL (+3 more)

### Community 187 - "_validate_single_finding"
Cohesion: 0.13
Nodes (5): _compute_relevance(), _find_linter_confirmation(), _find_supporting_chunks(), _validate_single_finding(), _verify_file_in_diff()

### Community 189 - "encrypt_token"
Cohesion: 0.17
Nodes (5): test_connect_unexpected_pat_field(), test_connect_without_oauth_identity_fails(), _setup_user_and_org(), TestPullRequestEndpoints, TestRepositoryConnect

### Community 191 - "ChangeImpactAnalysis"
Cohesion: 0.21
Nodes (6): ChangeImpactAnalysis, _get_authorized_repo(), get_impact_analysis_by_id(), get_impact_graph(), get_latest_pr_impact(), trigger_impact_analysis()

### Community 192 - "TestScenario"
Cohesion: 0.21
Nodes (3): TestCodeGenerator, TestScenario, test_generator_creates_pending_test_case()

### Community 193 - "run_change_impact_analysis"
Cohesion: 0.18
Nodes (5): generate_impact_mermaid(), generate_test_recommendations(), run_change_impact_analysis(), test_mermaid_generation(), test_run_change_impact_analysis_engine()

### Community 196 - "process_automation_actions"
Cohesion: 0.22
Nodes (4): _get_token_for_identity(), process_automation_actions(), test_def_02_reject_permission_and_queue_worker(), PART 17 — REQUEST CHANGES

### Community 197 - "RepoMind Intelligence — Current System Architecture"
Cohesion: 0.17
Nodes (11): 1. High-Level System Architecture, 2. Technology Stack Specifications, 4.1 Authentication & Session Handling, 4.2 Role-Based Access Control (RBAC), 4. API Communication & Security Architecture, 5. Existing AI Pipeline & Review Execution, 6. Repository Indexing & Vector Search Workflow, 7. GitHub Webhook Ingestion Workflow (+3 more)

### Community 198 - "End-to-End Flow"
Cohesion: 0.12
Nodes (15): 11 — Feature Flow: AI Chat Assistant, 2. Send a Message, 4. Build Evidence + System Prompt, 5. Build User Content with History, 6. Call LLM, 7. Persist Messages, 8. Return Response, API Endpoints (+7 more)

### Community 204 - "FindingSchema"
Cohesion: 0.06
Nodes (30): validate_findings(), ValidatedFinding, FindingSchema, compute_finding_fingerprint(), _persist_validated_findings(), is_match(), _make_validated_finding(), test_def_03_no_infinite_zombie_duplication_across_runs() (+22 more)

### Community 205 - "LanguageAwareParser"
Cohesion: 0.40
Nodes (5): LanguageAwareParser, test_js_ts_parsing(), test_parser_syntax_error_resilience(), test_python_ast_parsing(), test_knowledge_graph_construction_and_mermaid()

### Community 206 - "impact/schemas.py"
Cohesion: 0.36
Nodes (6): AffectedComponentResponse, BreakingChangeResponse, ChangeImpactAnalysisResponse, GraphVisualizationResponse, ImpactAnalysisTriggerRequest, TestRecommendationResponse

### Community 207 - "list_security_findings"
Cohesion: 0.22
Nodes (4): FindingStatusUpdate, list_security_findings(), SecurityFindingResponse, update_finding_status()

### Community 208 - "RepoMind 2.0 Feature Code Flow Walkthroughs"
Cohesion: 0.29
Nodes (6): 1. Authentication & Bootstrapping Flow, 3. RAG Pipeline Flow (Repository Indexing, Chunking, Embedding), 3a. Ingestion Trigger & Job Queue, 3b. Fetch & Chunking, 3c. Embedding & Vector Storage, RepoMind 2.0 Feature Code Flow Walkthroughs

### Community 209 - "_process_one_indexing_job"
Cohesion: 0.22
Nodes (7): Phase 1: Atomic Job Claim, Phase 2: Execute in Fresh Session, Repository Indexing Job Processing, Index Trigger, Manual Re-Index, Step 1: Worker Claims the Job, _process_one_indexing_job()

### Community 210 - "github/schemas.py"
Cohesion: 0.36
Nodes (4): GitHubConnectRequest, PullRequestListResponse, PullRequestResponse, RepositoryConnectResponse

### Community 211 - "_extract_py_signatures"
Cohesion: 0.36
Nodes (5): _extract_py_signatures(), _handle_func(), visit_AsyncFunctionDef(), visit_FunctionDef(), FunctionSignature

### Community 213 - "make_client_for_user"
Cohesion: 0.25
Nodes (5): make_client_for_user(), test_generate_and_execute_test_case_endpoints(), test_get_pr_test_scenarios_and_filtering(), test_get_test_dashboard_endpoint(), test_trigger_test_analysis_endpoint()

### Community 214 - "13 — Feature Flow: Analytics"
Cohesion: 0.29
Nodes (6): 13 — Feature Flow: Analytics, Feature Summary, Key Files, Permission Required, Tables Read, UI Display

### Community 218 - "Things I Must Not Misunderstand"
Cohesion: 0.33
Nodes (5): Learning Checklist, Part 26 — Developer Mental Model, Part 27 — Glossary, Things I Must Not Misunderstand, Verification Snapshot

### Community 220 - "Part 4 — Line-by-Line Code Teaching"
Cohesion: 0.67
Nodes (3): Function: `chunk_text()`, Function: `embed_chunks()`, Part 4 — Line-by-Line Code Teaching

### Community 221 - "Part 20 — Phase 7 Test-by-Test Walkthrough"
Cohesion: 0.67
Nodes (3): Part 20 — Phase 7 Test-by-Test Walkthrough, Test B — test_repository_isolation, Test E — test_embedding_dimension

## Knowledge Gaps
- **18 isolated node(s):** `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector`, `Per-User GitHub OAuth`, `Organization` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1677 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **90 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `github/routes.py` to `Repository`, `test_intelligence_routes.py`, `organizations/routes.py`, `RoleEnum`, `organizations/models.py`, `Key Files`, `chat/routes.py`, `auth/service.py`, `re`, `_get_authorized_repo`, `Document`, `test_review.py`, `test_architecture_intelligence.py`, `get_user_by_email`, `test_historical_intelligence.py`, `history/routes.py`, `review/router.py`, `Onboarding Authorization Tests`, `_get_authorized_repo`, `encrypt_token`, `format_auth_response`, `github/service.py`, `PullRequestFile`, `auth/routes.py`, `16 — API Endpoint Reference`, `organizations/service.py`, `encrypt_token`, `ChangeImpactAnalysis`, `onboarding/routes.py`, `intelligence/routes.py`, `list_security_findings`, `UpdateProgressRequest`, `sqlalchemy`, `test_change_impact_analyzer.py`, `Finding`, `onboarding/service.py`, `test_pr_review_engine_upgrade.py`, `testing/routes.py`, `Directory Deep Dive`?**
  _High betweenness centrality (0.167) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `User` (e.g. with `get_org_analytics()` and `create_architecture_rule()`) actually correct?**
  _`User` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.03729071537290715 - nodes in this community are weakly interconnected._
- **Why does `Key Files` connect `Key Files` to `onboarding/routes.py`, `github/routes.py`, `App`, `organizations/models.py`, `auth/service.py`, `verify_org_member`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `Repository` (e.g. with `get_organization_analytics()` and `_get_authorized_repo()`) actually correct?**
  _`Repository` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `typing` be split into smaller, more focused modules?**
  _Cohesion score 0.03773584905660377 - nodes in this community are weakly interconnected._