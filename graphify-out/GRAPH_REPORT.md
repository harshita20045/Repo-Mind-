# Graph Report - Repo-Mind-  (2026-11-26)

## Corpus Check
- 452 files · ~277,403 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .bat 4, (none) 3, .ini 2)

## Summary
- 3697 nodes · 9659 edges · 241 communities (144 shown, 97 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1274 edges (avg confidence: 0.93)
- Token cost: 152,469 input · 7,531 output

## Graph Freshness
- Built from commit: `014b45d9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- HistoricalIntelligenceDashboard.test.jsx
- Frontend Dependencies
- typing
- github/routes.py
- Project
- 07 — Feature Flow: LLM Provider (Groq / Gemini / Fallback)
- organizations/service.py
- RoleEnum
- get
- 02 — Feature Flow: Authentication
- chat/service.py
- analyzer.py
- ReviewRun
- onboarding/routes.py
- seed_demo_intelligence.py
- 2.3 Domain 3: Review & Risk Engine
- ReviewPage.jsx
- GitHub API Client
- Detailed Step-by-Step
- test_chat_api_route_e2e_grounded_response
- react
- architecture/engine.py
- RAGRetriever
- test_review.py
- RepoMind Intelligence 2.0 — Development Handover Report
- RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough
- test_architecture_intelligence.py
- LanguageAwareParser
- 09 — Feature Flow: Risk Scoring Engine
- test_historical_intelligence.py
- test_phase12_scenarios.py
- Organization API Schemas
- Permission Normalization Tests
- review/router.py
- Onboarding Authorization Tests
- App
- test_linter_contract.py
- DashboardPage.jsx
- _get_authorized_repo
- GitHubIdentity
- OnboardingService
- RetrievalResult
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
- history/routes.py
- json
- api.js
- LLMProvider
- PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT
- run_change_impact_analysis
- db_session
- Multi-tenant Security Tests
- ReviewRun
- Final RBAC Parity & Feature Audit Report
- test_change_impact_analyzer.py
- RepoMind Intelligence 2.0 — Complete Technical Audit
- intelligence/routes.py
- GitHub OAuth Identity
- ML Training Service
- Background Workers
- Merge Policy Logic
- Repository Blueprinting
- RepoMind — Environment Configuration
- re
- RepoMind — Monitoring & Observability
- run_review
- RepoMind — Architecture Decision Record
- Review Pipeline: 11 Stages
- sqlalchemy
- requests
- detector.py
- CodeGraphNode
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
- breaking.py
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
- ArchitectureDecisionRecord
- RepoMind 2.0 — System Architecture
- RepoMind — Troubleshooting
- README.md
- MultiSourceContextRetriever
- chat/routes.py
- RepositoryScanner
- RepoMind — Authentication & Authorization
- RepoMind — Secrets Management
- RepoMind 2.0 — Deployment Guide (No Docker)
- 2. Phase-by-Phase Implementation Specifications
- sparsevec.h
- b334a8c323d8_fix_role_enum_casing.py
- index_repository
- RepoMind 2.0 — Project Overview
- 2. Analytics Queries
- run_linters
- RiskAssessmentResponse
- RepoMind — Git Workflow
- RepoMind — Test Plan
- RepoMind — Database Migrations
- test_intelligence_routes.py
- UserOnboardingProgress
- Vector
- 1. Project Discovery & Layer Inspection
- RepoMind 2.0 — UI Design
- _extract_py_signatures
- ReviewRunResponse
- RepoMind — Implementation Plan
- RepoMind — Scope
- Local development environment
- _extract_py_symbols_with_lines
- RepoMind 2.0 — Requirements
- RepoMind 2.0 — API Design
- RepoMind — Coding Standards
- RepoMind 2.0 Feature Code Flow Walkthroughs
- RepoMind 2.0 Complete Technical Guide
- Diagram — PR Review Sequence
- Diagram — RAG Pipeline
- ._enforce_grounding_invariants
- component-architecture.md
- data-flow.md
- deployment-architecture.md
- system-context.md
- test-cases.md
- build_user_content
- _validate_single_finding
- Settings
- GitHubAPIError
- ChangeImpactAnalysis
- TestScenario
- impact/engine.py
- cab03f32deec_add_audit_log.py
- RepoMind Intelligence — Current System Architecture
- End-to-End Flow
- FindingSchema
- test_blueprint_persistence_and_api_roundtrip
- 16 — API Endpoint Reference
- get_current_user
- search_historical_prs
- build_onboarding_user_content
- make_client_for_user
- 5a5ce4894f5c_add_ml_prediction.py
- Things I Must Not Misunderstand

## God Nodes (most connected - your core abstractions)
1. `User` - 198 edges
2. `Repository` - 157 edges
3. `ReviewRun` - 110 edges
4. `Project` - 108 edges
5. `PullRequest` - 108 edges
6. `Organization` - 99 edges
7. `OrganizationMembership` - 83 edges
8. `RoleEnum` - 75 edges
9. `react` - 74 edges
10. `run_review()` - 60 edges

## Surprising Connections (you probably didn't know these)
- `4.1 Authentication & Session Handling` --references--> `apiRequest()`  [INFERRED]
  Docs/CURRENT_ARCHITECTURE.md → frontend/src/lib/api.js
- ``POST /chat/sessions/{id}/messages`` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/api_endpoint_reference.md → backend/app/chat/models.py
- `8. Return Response` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatMessage`` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatSession`` --references--> `ChatSession`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GitHub OAuth Identity Linking** — repomind_2_0_architecture_flow_github_oauth, backend_app_github_oauth_routes_github_oauth_callback, backend_app_github_oauth_service_upsert_github_identity [EXTRACTED 1.00]
- **Developer Onboarding Subsystem** — walkthrough_repository_blueprint, walkthrough_user_onboarding_progress, walkthrough_onboarding_service [EXTRACTED 1.00]
- **RAG Indexing Pipeline** — backend_app_rag_loader, backend_app_rag_chunker, backend_app_rag_embedder, backend_app_rag_repository, postgresql_pgvector [EXTRACTED 1.00]

## Communities (241 total, 97 thin omitted)

### Community 0 - "HistoricalIntelligenceDashboard.test.jsx"
Cohesion: 0.22
Nodes (7): historyApi, mockAdrs, mockComparison, mockHistoricalCommits, mockHistoricalPrs, mockHotspots, mockRepo

### Community 1 - "Frontend Dependencies"
Cohesion: 0.04
Nodes (66): dependencies, mermaid@^12.3.0, react@^18.2.0, react-diff-viewer-continued@^4.4.0, react-dom@^18.2.0, react-markdown@^10.1.0, react-router-dom@^7.18.3, @tanstack/react-query@^5.102.8 (+58 more)

### Community 2 - "typing"
Cohesion: 0.03
Nodes (29): upgrade(), downgrade(), upgrade(), downgrade(), upgrade(), upgrade(), upgrade(), upgrade() (+21 more)

### Community 3 - "github/routes.py"
Cohesion: 0.10
Nodes (23): User, _assert_repo_access(), connect_repository(), get_merge_policy(), get_pull_request(), get_pull_request_commits(), get_pull_request_conflicts(), get_pull_request_events() (+15 more)

### Community 4 - "Project"
Cohesion: 0.05
Nodes (29): Organization, Project, reset_database(), seed_database(), api_test_data(), test_setup(), arch_test_env(), impact_test_env() (+21 more)

### Community 5 - "07 — Feature Flow: LLM Provider (Groq / Gemini / Fallback)"
Cohesion: 0.10
Nodes (10): retry_if_transient_error(), GroqProvider, 07 — Feature Flow: LLM Provider (Groq / Gemini / Fallback), Environment Configuration, GroqProvider, LLMProvider Protocol, LocalProvider (Development / Mock), Prompt Security Architecture (+2 more)

### Community 6 - "organizations/service.py"
Cohesion: 0.08
Nodes (44): AuditLog, Team, create_organization(), create_project(), create_repository(), create_team(), get_organization(), get_repository() (+36 more)

### Community 7 - "RoleEnum"
Cohesion: 0.13
Nodes (18): RoleEnum, ProjectMember, TeamMember, run_decision_test(), test_approve_developer(), test_approve_org_admin(), test_approve_reviewer(), test_approve_team_lead() (+10 more)

### Community 8 - "get"
Cohesion: 0.09
Nodes (17): github_oauth_callback(), list_github_repositories(), compare_change_with_history(), discover_similar_historical_prs(), get_architecture_decision_records(), _get_authorized_repo(), get_historical_bug_lessons(), get_historical_prs() (+9 more)

### Community 9 - "02 — Feature Flow: Authentication"
Cohesion: 0.25
Nodes (7): 02 — Feature Flow: Authentication, Backend (Canonical), Data Flow Diagram (Mermaid), Feature Summary, Frontend (Mirror), RBAC Enforcement, Security Properties

### Community 10 - "chat/service.py"
Cohesion: 0.17
Nodes (9): _build_grounded_mock_response(), create_session(), get_session_messages(), get_sessions(), send_message(), test_chat_service_generates_grounded_response_with_citations(), Chat Endpoints, `POST /chat/sessions/{id}/messages` (+1 more)

### Community 11 - "analyzer.py"
Cohesion: 0.13
Nodes (5): run_test_intelligence_analysis(), TestIntelligenceAnalyzer, test_analyzer_detects_existing_test_mapping(), test_analyzer_empty_diff_returns_empty(), test_analyzer_identifies_modified_functions_and_generates_8_categories()

### Community 12 - "ReviewRun"
Cohesion: 0.11
Nodes (14): _setup_repo_and_pr(), test_gap_09_abandoned_job_exceeding_max_retries_fails(), test_gap_09_abandoned_job_with_superseded_sha_transitions_to_superseded(), test_gap_09_active_heartbeat_job_is_not_recovered(), test_gap_09_concurrent_worker_recovery_postgres_skip_locked(), worker_recovery_task(), test_gap_09_heartbeat_renewal_and_token_validation(), test_gap_09_stale_running_job_recovered_to_pending() (+6 more)

### Community 13 - "onboarding/routes.py"
Cohesion: 0.14
Nodes (10): _get_repo_and_verify_access(), get_repository_blueprint(), get_user_onboarding_progress(), refresh_repository_blueprint(), update_user_onboarding_progress(), BlueprintGenerationError, GenerationInProgressError, GroundingValidationError (+2 more)

### Community 14 - "seed_demo_intelligence.py"
Cohesion: 0.11
Nodes (18): Repository, get_demo_bug_lessons(), get_demo_evolution_milestones(), get_target_repo(), main(), seed_adrs(), seed_blueprint(), seed_commits_and_hotspots() (+10 more)

### Community 15 - "2.3 Domain 3: Review & Risk Engine"
Cohesion: 0.05
Nodes (43): 1.1 Domain Table Breakdown, 1. Complete Database Schema Inventory, 2.1 Domain 1: Authentication & Multi-Tenant Hierarchy, 2.2 Domain 2: GitHub Integration & Pull Requests, 2.3 Domain 3: Review & Risk Engine, 2.4 Domain 4: Code-Aware RAG & pgvector Storage, 2.5 Domain 5: Collaboration & Developer Onboarding, 2.6 Domain 6: Webhooks, Audit & ML (+35 more)

### Community 16 - "ReviewPage.jsx"
Cohesion: 0.12
Nodes (22): ImpactOverview(), ActivityLog(), ConflictCard(), ConflictList(), EvidenceStatus(), FindingCard(), LifecycleBadge(), FindingList() (+14 more)

### Community 18 - "Detailed Step-by-Step"
Cohesion: 0.05
Nodes (39): 14 — Feature Flow: Background Worker, Configuration, Consecutive Error Tracking, Error Handling, Job Lifecycle States, Key Files, LLM Provider Initialization, Parallelism Support (+31 more)

### Community 20 - "react"
Cohesion: 0.09
Nodes (31): ArchitectureDashboard(), ArchitectureHealthOverview(), ArchitectureRuleManager(), ArchitectureViolationsList(), CircularDependencyGraph(), FlowAnalysisViewer(), EdgeDetailsModal(), EngineeringGraphEngine() (+23 more)

### Community 21 - "architecture/engine.py"
Cohesion: 0.14
Nodes (10): GroundedViolation, calculate_architecture_health_score(), ensure_baseline_architecture_rules(), generate_architecture_mermaid(), run_architecture_analysis(), ArchitectureAnalysis, ArchitectureViolation, detect_architecture_pattern() (+2 more)

### Community 22 - "RAGRetriever"
Cohesion: 0.09
Nodes (13): RAGRetriever, derive_query_from_diff(), retrieve_context(), test_invalid_top_k(), test_relevant_retrieval(), test_repository_isolation(), test_top_k(), test_derive_query_extracts_paths() (+5 more)

### Community 23 - "test_review.py"
Cohesion: 0.08
Nodes (18): get_llm_provider(), LLMProviderError, LocalProvider, FailingProvider, FakeProvider, test_a_valid_output_creates_completed_run(), test_b_malformed_json_both_attempts_fail(), test_b_malformed_json_retries_then_succeeds() (+10 more)

### Community 24 - "RepoMind Intelligence 2.0 — Development Handover Report"
Cohesion: 0.05
Nodes (40): 10. AI Chat Assistant (`/chat`), 11. AI Test Intelligence (`/repositories/{id}/test-intelligence`, `/test-scenarios`, `/generated-tests`, `/test-intelligence`), 12. Technical Debt Intelligence (`/repositories/{id}/tech-debt`), 13. Security & Analytics (`/security`, `/analytics`), 1. Health & Core, 2. Advanced AI Pull Request Intelligence (`backend/app/review/analysis.py`, `service.py`, `evidence.py`), 2. Authentication & Memberships (`/auth`), 3. Change Impact & Blast Radius Analyzer (`backend/app/impact/`) (+32 more)

### Community 25 - "RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough"
Cohesion: 0.05
Nodes (39): 10. Complete API Reference, 11. Role Hierarchy & Repository Authorization, 12. Private Progress & Anti-Surveillance Guarantees, 13. Frontend Component & Routing Architecture, 14. Mermaid Rendering Security, 15. Developer Onboarding User Journey, 16. Team Lead Refresh User Journey, 17. Testing Commands & Actual Results (+31 more)

### Community 26 - "test_architecture_intelligence.py"
Cohesion: 0.08
Nodes (24): check_architecture_rules(), _matches_pattern(), CircularDependency, detect_circular_dependencies(), FlowAnalysisResult, FlowChain, trace_architecture_flows(), classify_layer() (+16 more)

### Community 28 - "LanguageAwareParser"
Cohesion: 0.19
Nodes (7): CodeSymbol, LanguageAwareParser, ParsedCodeFile, test_js_ts_parsing(), test_parser_syntax_error_resilience(), test_python_ast_parsing(), test_knowledge_graph_construction_and_mermaid()

### Community 29 - "09 — Feature Flow: Risk Scoring Engine"
Cohesion: 0.10
Nodes (20): 09 — Feature Flow: Risk Scoring Engine, 7 Weighted Factors, Blast Radius and Test Impact, `_calculate_blast_radius(changed_files)` returns:, `calculate_risk()` Structure, `_calculate_test_impact(changed_files, diff)` returns:, Entry Point, Factor 1: Security Exposure (Weight: 25%) (+12 more)

### Community 30 - "test_historical_intelligence.py"
Cohesion: 0.09
Nodes (16): compute_and_index_hotspots(), mine_and_index_commits(), HistoricalCommitRecord, RecurringIssueHotspot, compare_changes_with_history(), get_similar_resolved_bugs(), search_previous_changes(), test_api_historical_prs_and_changes() (+8 more)

### Community 31 - "test_phase12_scenarios.py"
Cohesion: 0.13
Nodes (12): HistoricalBugLesson, HistoricalEvolutionMilestone, analyze_historical_impact(), get_bug_lessons(), get_evolution_milestones(), get_evolution_overview(), get_module_evolution(), get_recurring_issues() (+4 more)

### Community 32 - "Organization API Schemas"
Cohesion: 0.17
Nodes (20): GithubConnectionBase, GithubConnectionCreate, GithubConnectionResponse, MemberBase, MemberInvite, MemberRoleUpdate, OrganizationBase, OrganizationCreate (+12 more)

### Community 33 - "Permission Normalization Tests"
Cohesion: 0.10
Nodes (7): test_def_02_action_casing_cannot_bypass_approve_permission(), override_db(), override_user(), test_def_02_arbitrary_unsupported_action_rejected(), test_def_02_lead_approve_normalized_and_triggers_merge_policy(), test_def_02_reject_permission_and_queue_worker(), test_def_06_missing_pull_request_returns_404_no_500()

### Community 34 - "review/router.py"
Cohesion: 0.10
Nodes (11): HumanReview, get_decrypted_github_token_for_org(), get_repository_by_id(), decide_review_run(), get_review_run(), get_review_run_decisions(), list_review_runs(), trigger_review() (+3 more)

### Community 36 - "Onboarding Authorization Tests"
Cohesion: 0.22
Nodes (16): cleanup_overrides(), make_client_for_user(), test_10_invalid_track_and_milestone_ids_are_rejected(), test_11_repository_access_enforced_across_all_endpoints(), test_12_active_generation_conflict_returns_409(), test_13_unindexed_repository_error_returns_400(), test_14_responses_do_not_leak_internal_prompts_or_traces(), test_1_authorized_user_can_retrieve_blueprint() (+8 more)

### Community 37 - "App"
Cohesion: 0.09
Nodes (31): 19 — Feature Flow: Frontend Application, `App.jsx` — Root Component, Application Entry Point, Feature Summary, Key Files Summary, Layout Structure, `lib/api.js` — API Wrapper, `ProtectedRoute` Component (+23 more)

### Community 38 - "test_linter_contract.py"
Cohesion: 0.07
Nodes (16): BanditLinter, LinterTool, RuffLinter, _extract_linter_issues(), test_bandit_canonical_schema_with_findings(), test_empty_linter_findings(), test_failed_tool_execution_preserves_error_signal(), test_malformed_and_unexpected_linter_output() (+8 more)

### Community 39 - "DashboardPage.jsx"
Cohesion: 0.12
Nodes (29): Page Components, ChatAssistant(), SOURCE_TYPE_STYLES, SUPPORTED_QUESTIONS, HistoricalContextCard(), Card(), MetricCard(), SectionCard() (+21 more)

### Community 40 - "_get_authorized_repo"
Cohesion: 0.11
Nodes (19): ArchitectureRule, create_architecture_rule(), delete_architecture_rule(), get_architecture_flows(), _get_authorized_repo(), get_circular_dependencies(), get_latest_architecture_analysis(), list_architecture_rules() (+11 more)

### Community 41 - "GitHubIdentity"
Cohesion: 0.07
Nodes (17): _get_token_for_identity(), process_automation_actions(), decrypt_token(), encrypt_token(), _get_fernet(), reconcile_pull_requests(), get_valid_access_token_for_credential(), refresh_github_credential() (+9 more)

### Community 42 - "OnboardingService"
Cohesion: 0.15
Nodes (12): RepositoryBlueprint, RepositoryBlueprintResponse, OnboardingService, test_duplicate_concurrent_generation_prevention(), test_failed_regeneration_preserves_previous_valid_blueprint(), test_generation_and_cache_hit(), test_grounding_rejects_fabricated_request_flow_path(), test_stale_pending_job_recovery() (+4 more)

### Community 43 - "RetrievalResult"
Cohesion: 0.17
Nodes (12): _detect_api_contract_conflicts(), _detect_architecture_conflicts(), _detect_configuration_conflicts(), detect_conflicts(), _detect_mechanical_conflicts(), _detect_security_policy_conflicts(), _detect_test_contract_conflicts(), DetectedConflict (+4 more)

### Community 44 - "TextChunker"
Cohesion: 0.12
Nodes (8): ASTChunk, ASTCodeChunker, TextChunker, test_chunker_determinism_and_overlap(), `backend/app/rag/chunker.py`, `backend/app/rag/service.py`, Part 3 — Phase 6 File-by-File Walkthrough, 1.9 RAG Implementation & Vector Database

### Community 46 - "TestIntelligenceDashboard.jsx"
Cohesion: 0.13
Nodes (15): LoginForm(), TestCodeViewer(), TestExecutionResult(), CATEGORIES, TestIntelligenceDashboard(), CATEGORY_THEMES, PRIORITY_BADGES, TestScenarioCard() (+7 more)

### Community 47 - "PullRequest"
Cohesion: 0.12
Nodes (18): GitHubComment, GitHubRepositoryAccess, GitHubReview, ProjectMergePolicy, PullRequestCheck, PullRequestCommit, PullRequestEvent, WebhookEvent (+10 more)

### Community 48 - "RAGRepository"
Cohesion: 0.07
Nodes (13): EmbedderError, LocalEmbedder, RAGRepository, embedder(), setup_test_repos(), test_embedding_dimension(), test_embedder_validation(), test_persistence_and_idempotency() (+5 more)

### Community 49 - "sync_pull_requests"
Cohesion: 0.15
Nodes (15): sync_pull_requests(), GithubConnection, `GET /repositories/{id}/pull-requests`, `POST /repositories/connect`, Pull Request Endpoints, 03 — Feature Flow: GitHub Repository Connection & Sync, 1. Connect a GitHub Repository, 2. PR Sync (called after connect and on-demand) (+7 more)

### Community 50 - "calculate_risk"
Cohesion: 0.07
Nodes (14): _calculate_blast_radius(), calculate_risk(), _calculate_test_impact(), _generate_summary(), RiskResult, _score_architecture(), _score_change_size(), _score_complexity() (+6 more)

### Community 51 - "RepoMind Phase 6–7 Complete Technical Walkthrough"
Cohesion: 0.07
Nodes (30): Executive Summary, Function: `chunk_text()`, Function: `embed_chunks()`, Part 10 — PostgreSQL + pgvector Internal Understanding, Part 12 — Phase 7 Overview, Part 13 — Phase 7 End-to-End Retrieval Flow, Part 14 — Retriever Code Deep Dive, Part 15 — Cosine Retrieval (+22 more)

### Community 52 - "Step 2: Apply Gap Detection Categories"
Cohesion: 0.08
Nodes (24): A. Entry and Exit Conditions, Analyzing Business Logic Gaps, B. State Definitions, C. State Transitions, Checklist for Quick Analysis, Common Gap Patterns, D. Exceptional Paths, E. Billing and Credit Rules (+16 more)

### Community 53 - "auth/routes.py"
Cohesion: 0.10
Nodes (39): bootstrap(), change_password_route(), format_auth_response(), get_me(), login(), logout(), onboard(), set_session_cookie() (+31 more)

### Community 54 - "history/routes.py"
Cohesion: 0.24
Nodes (18): ADRResponse, BugLessonResponse, ChangeComparisonItem, ChangeComparisonRequest, ChangeComparisonResponse, EvolutionMilestoneResponse, EvolutionOverviewResponse, HistoricalCommitResponse (+10 more)

### Community 55 - "json"
Cohesion: 0.13
Nodes (13): LLMOutputParseError, parse_llm_output(), main(), test_multi_stage_review_8_categories_validation(), test_parse_llm_output_empty_array(), test_parse_llm_output_invalid_confidence_negative(), test_parse_llm_output_invalid_confidence_too_high(), test_parse_llm_output_invalid_severity() (+5 more)

### Community 56 - "api.js"
Cohesion: 0.12
Nodes (35): App(), queryClient, RepositoryNav(), TeamManagement(), Badge(), RISK_STYLES, SEVERITY_STYLES, STATUS_STYLES (+27 more)

### Community 57 - "LLMProvider"
Cohesion: 0.13
Nodes (9): FallbackProvider, GeminiProvider, LLMProvider, test_gemini_provider_satisfies_protocol(), 6. Call LLM, Feature Summary, GeminiProvider, 4. LLM Security: System Prompt Separation (+1 more)

### Community 58 - "PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT"
Cohesion: 0.15
Nodes (12): 10. Defects and Fixes, 11. External Limitations, 12. Conclusion, 1. Objective and Scope, 2. Runtime and Initialization, 3. Authentication & RBAC, 5. Repository Discovery and Connection, 6. Webhook and Review Pipeline (E2E) (+4 more)

### Community 59 - "run_change_impact_analysis"
Cohesion: 0.12
Nodes (7): generate_impact_mermaid(), generate_test_recommendations(), run_change_impact_analysis(), ChangeImpactAnalysis, test_generate_test_recommendations(), test_mermaid_generation(), test_run_change_impact_analysis_engine()

### Community 60 - "db_session"
Cohesion: 0.22
Nodes (4): client(), db_session(), setup_test_db(), _verify_test_db_identity()

### Community 62 - "Multi-tenant Security Tests"
Cohesion: 0.29
Nodes (4): test_chat_session_creation_rejects_foreign_repository(), test_def_04_cross_tenant_chat_retrieval_prevented(), override_db(), override_user()

### Community 63 - "ReviewRun"
Cohesion: 0.05
Nodes (30): run_migrations_offline(), run_migrations_online(), GitHubCredential, GitHubIdentity, LinterResult, ReviewRun, _update_progress(), WebhookEvent (+22 more)

### Community 64 - "Final RBAC Parity & Feature Audit Report"
Cohesion: 0.10
Nodes (17): 4-Role RBAC Model, A. Exact backend roles discovered, B. Four-role mapping, C. Backend permission matrix, D. Frontend permission matrix, E. Feature parity matrix, F. Organization Admin coverage, Final RBAC Parity & Feature Audit Report (+9 more)

### Community 65 - "test_change_impact_analyzer.py"
Cohesion: 0.14
Nodes (6): make_client_for_user(), test_ast_change_detection_functions_and_classes(), test_database_model_column_dropped_is_breaking(), test_impact_api_tenant_isolation(), test_impact_api_trigger_and_get(), test_optional_parameter_addition_not_breaking()

### Community 66 - "RepoMind Intelligence 2.0 — Complete Technical Audit"
Cohesion: 0.20
Nodes (9): 2.1 Critical Runtime & Dependency Issues, 2.2 Model & Architectural Inconsistencies, 2.3 Mock & Incomplete Endpoints, 2.4 Frontend Test Failures, 2. Technical Audit Findings & Discrepancies, 3. Technology Stack Verification, 4. Conclusion & Audit Sign-Off, Executive Summary (+1 more)

### Community 67 - "intelligence/routes.py"
Cohesion: 0.19
Nodes (15): DependencyExtractor, get_architecture_diagram(), _get_authorized_repo(), get_repository_dependencies(), get_repository_graph(), get_repository_summary(), get_repository_symbols(), trigger_intelligence_indexing() (+7 more)

### Community 89 - "RepoMind — Environment Configuration"
Cohesion: 0.33
Nodes (5): Development, Production, RepoMind — Environment Configuration, Testing / CI, Variables

### Community 90 - "re"
Cohesion: 0.16
Nodes (7): extract_endpoints(), extract_files(), extract_pr_id(), extract_symbols(), QueryIntent, ReviewDecisionAction, test_entity_extraction_helpers()

### Community 91 - "RepoMind — Monitoring & Observability"
Cohesion: 0.15
Nodes (12): AI Failures, API Errors, Application Logs, Database Health, GitHub Integration Failures, ML Failures, Performance Metrics, RAG Failures (+4 more)

### Community 92 - "run_review"
Cohesion: 0.17
Nodes (8): AIAnalysis, _mark_failed(), _persist_conflicts(), _persist_risk(), run_review(), FallbackProvider, PART 14 — LLM REVIEW PIPELINE, PART 3 — REPOSITORY STRUCTURE

### Community 93 - "RepoMind — Architecture Decision Record"
Cohesion: 0.11
Nodes (17): ADR-001 — Modular Monolith Architecture, ADR-002 — Frontend: React + TypeScript + Tailwind, ADR-003 — Backend: FastAPI + Pydantic, ADR-004 — Database: PostgreSQL + SQLAlchemy + Alembic, ADR-005 — Vector Storage: pgvector (not a dedicated vector database), ADR-006 — Embeddings: sentence-transformers (local), ADR-007 — Retrieval Mechanism: pgvector Cosine Similarity, Repository-Scoped, ADR-008 — GitHub Integration Strategy: PAT + REST API (Phase 1) (+9 more)

### Community 94 - "Review Pipeline: 11 Stages"
Cohesion: 0.14
Nodes (13): 05 — Feature Flow: PR Review Pipeline (Full 11-Stage), Data Flow Diagram (Mermaid), Duplicate-Review Invariant, Review Pipeline: 11 Stages, Stage 11: Mark Completed, Stage 1: Resolve PR + Repository (DB Authoritative), Stage 2: Create ReviewRun (pending → running), Stage 3: Fetch PR Diff + Changed Files (+5 more)

### Community 95 - "sqlalchemy"
Cohesion: 0.08
Nodes (16): downgrade(), upgrade(), downgrade(), upgrade(), downgrade(), upgrade(), OrganizationMembership, test_bootstrap_flow() (+8 more)

### Community 96 - "requests"
Cohesion: 0.18
Nodes (3): get_auth_token(), test_oauth_routes(), test_phase3()

### Community 97 - "detector.py"
Cohesion: 0.19
Nodes (7): ChangedSymbol, detect_code_changes(), _detect_symbols_from_diff_hunks(), parse_diff_hunks(), PRDiffHunk, test_detect_breaking_signature_mutations(), L. Important Files and Modules to Reuse

### Community 98 - "CodeGraphNode"
Cohesion: 0.09
Nodes (20): PullRequestFile, CodeKnowledgeGraph, RepositoryIndexer, CodeGraphEdge, CodeGraphNode, PackageDependency, RepositoryScanSummary, Document (+12 more)

### Community 99 - "RepoMind — Development Guide"
Cohesion: 0.13
Nodes (14): Backend Setup (Python / FastAPI), Database Initialization and Migrations, Environment Variables, Frontend Setup, Linting and Formatting, No Docker, PostgreSQL Setup (Native), RepoMind — Development Guide (+6 more)

### Community 100 - "PullRequest"
Cohesion: 0.07
Nodes (26): get_organization_analytics(), ChatMessage, ChatSession, PullRequest, Finding, FindingEvidence, RiskAssessment, _setup_org_project_repo() (+18 more)

### Community 102 - "Finding"
Cohesion: 0.07
Nodes (39): evaluate_merge_policy(), AutomationAction, HumanDecision, 10 — Feature Flow: Human Review Approval Gate, 1. View Completed Review, 2. Trigger Approve/Reject, 3. Authorization Check, 4. Persist Decision (Upsert) (+31 more)

### Community 103 - "Key Architectural Facts (Quick Reference)"
Cohesion: 0.14
Nodes (14): Auth, Documentation Set, Documents, Feature Flows (Start-to-End Traces), GitHub, Key Architectural Facts (Quick Reference), ML, RAG (+6 more)

### Community 104 - "18 — Feature Flow: ML Prediction (PR Cycle Time)"
Cohesion: 0.11
Nodes (17): 18 — Feature Flow: ML Prediction (PR Cycle Time), 1. API Request, 2. Training Data Check, 3. Rule-Based Baseline, 4. Response, Current State (as observed in source), Data Model, Dataset Building (+9 more)

### Community 105 - "onboarding/service.py"
Cohesion: 0.13
Nodes (17): CautionZone, ExecutionFlows, ExecutionFlowStep, GlossaryItem, LLMBlueprintPayload, MilestoneItem, ReadingOrderItem, RequestFlowStep (+9 more)

### Community 106 - "test_pr_review_engine_upgrade.py"
Cohesion: 0.17
Nodes (6): extract_pr_analysis_context(), PRAnalysisContext, PRFileSummary, query_related_modules(), test_empty_diff_and_pure_deletion_handling(), test_pr_analysis_extraction_and_diff_hunks()

### Community 107 - "test_test_runner.py"
Cohesion: 0.17
Nodes (8): GeneratedTestCase, execute_generated_test(), IsolatedTestRunner, review_code_security(), test_runner_blocks_malicious_code_and_marks_error(), test_runner_captures_assertion_failure_without_false_pass(), test_runner_executes_safe_test_and_captures_pass(), test_security_review_detects_dangerous_calls()

### Community 108 - "testing/routes.py"
Cohesion: 0.19
Nodes (12): generate_test_case(), _get_authorized_repo(), get_pr_test_scenarios(), get_test_dashboard(), trigger_test_analysis(), ExistingTestFileSummary, GeneratedTestCaseResponse, TestExecutionResponse (+4 more)

### Community 109 - "_enqueue_review"
Cohesion: 0.06
Nodes (31): _enqueue_review(), github_webhook(), _resolve_repository(), _upsert_pr_from_webhook(), _setup_repo_and_pr(), test_gap_08_completed_historical_runs_are_preserved(), test_gap_08_concurrent_duplicate_webhooks_serialization(), deliver_webhook() (+23 more)

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

### Community 116 - "breaking.py"
Cohesion: 0.24
Nodes (6): BreakingChange, _check_signature_compatibility(), detect_breaking_changes(), _detect_breaking_from_diff_lines(), _detect_configuration_breaks(), _detect_database_schema_breaks()

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
Cohesion: 0.13
Nodes (15): Conflict, 08 — Feature Flow: Conflict Detection Engine, Conflict Lifecycle, DetectedConflict Dataclass, Detector 1: Mechanical Conflicts, Detector 2: Architecture Conflicts, Detector 3: Security Policy Conflicts, Detector 4: API Contract Conflicts (+7 more)

### Community 131 - "17 — Security Architecture"
Cohesion: 0.08
Nodes (25): _safe_join(), 06 — Feature Flow: Static Analysis (Ruff + Bandit), End-to-End Flow, Feature Summary, Key Files, Security Properties, Step 1: Entry Point, Step 2: Fetch PR File Metadata (+17 more)

### Community 133 - "ArchitectureDecisionRecord"
Cohesion: 0.18
Nodes (6): _extract_adrs_from_markdown(), _infer_modules_from_title_and_text(), parse_and_index_adrs(), ArchitectureDecisionRecord, test_adr_indexing_idempotence(), test_adr_parsing_from_docs()

### Community 134 - "RepoMind 2.0 — System Architecture"
Cohesion: 0.17
Nodes (11): AI Layer, API Communication, Authentication Flow, Backend, Database, Frontend, Overall Architecture, PR Review Flow (+3 more)

### Community 135 - "RepoMind — Troubleshooting"
Cohesion: 0.17
Nodes (12): AI / LLM, Authentication, Backend, Embeddings, Frontend, GitHub API, Linter Execution, Migrations (+4 more)

### Community 136 - "README.md"
Cohesion: 0.08
Nodes (19): 21 — Final Feature Status Matrix, AI Chat, Analytics, Core Features, GitHub Integration, ML Prediction, RAG Indexing, RepoMind 2.0 — Feature Implementation Status (+11 more)

### Community 137 - "MultiSourceContextRetriever"
Cohesion: 0.15
Nodes (9): classify_query(), ExtractedEntities, MultiSourceContextRetriever, test_dependency_graph_and_call_chain_retrieval(), test_multi_source_retriever_pulls_all_sources(), test_pr_review_rationale_retrieval(), test_query_classifier_all_8_categories(), test_test_coverage_retrieval() (+1 more)

### Community 138 - "chat/routes.py"
Cohesion: 0.07
Nodes (27): assert_org_permission(), check_org_permission(), get_role_permissions(), Permission, require_org_permission(), _check(), require_permission(), _check() (+19 more)

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

### Community 146 - "index_repository"
Cohesion: 0.12
Nodes (9): DocumentLoader, index_repository(), test_loader_exclusions(), test_loader_hashing(), Diagram — AI Review Pipeline (LLM), `backend/app/rag/loader.py`, Function: `_should_exclude_path()`, Part 6 — Hashing (+1 more)

### Community 148 - "RepoMind 2.0 — Project Overview"
Cohesion: 0.20
Nodes (9): Core Anti-Goals, Current Project Status, High-Level Workflow, Key Technologies, Main Capabilities, Problem Statement, RepoMind 2.0 — Project Overview, Target Users / Intended Usage (+1 more)

### Community 149 - "2. Analytics Queries"
Cohesion: 0.12
Nodes (16): 13 — Feature Flow: Analytics, 1. Frontend Request, 2. Analytics Queries, 3. Response, Base Query Setup, End-to-End Flow, Feature Summary, Key Files (+8 more)

### Community 150 - "run_linters"
Cohesion: 0.23
Nodes (6): _persist_failure(), _persist_result(), run_linters(), Stage 5: Run Static Analysis (Ruff + Bandit), Step 7: Persist Results, PART 11 — PULL REQUEST LIFECYCLE

### Community 151 - "RiskAssessmentResponse"
Cohesion: 0.07
Nodes (11): ConflictResponse, Config, FindingResponse, Config, HumanDecisionRequest, HumanDecisionResponse, Config, ReviewOutput (+3 more)

### Community 152 - "RepoMind — Git Workflow"
Cohesion: 0.22
Nodes (8): Branch Strategy, Commit Conventions, Handling AI Prompt / Model Changes, Handling Database Migrations, Merge Strategy, Pull Requests and Code Review, Release / Versioning Approach, RepoMind — Git Workflow

### Community 153 - "RepoMind — Test Plan"
Cohesion: 0.22
Nodes (8): AI / RAG, Component-Level, Feature-Level, Integration-Level, ML, RepoMind — Test Plan, Security, System-Level

### Community 154 - "RepoMind — Database Migrations"
Cohesion: 0.22
Nodes (9): Alembic Workflow, Applying Migrations, Migration Creation, Migration Review, Migration Testing, Production Migration Precautions, RepoMind — Database Migrations, Rollback Strategy (+1 more)

### Community 155 - "test_intelligence_routes.py"
Cohesion: 0.27
Nodes (8): make_client_for_user(), test_get_architecture_diagram(), test_get_dependencies(), test_get_graph_and_filtering(), test_get_summary_authorized(), test_get_summary_cross_tenant_forbidden(), test_get_symbols_search(), test_trigger_indexing_endpoint()

### Community 156 - "UserOnboardingProgress"
Cohesion: 0.28
Nodes (3): UserOnboardingProgress, UpdateProgressRequest, test_user_progress_isolated_and_updatable()

### Community 158 - "Vector"
Cohesion: 0.36
Nodes (3): _has_vector_extension(), Vector, process()

### Community 159 - "1. Project Discovery & Layer Inspection"
Cohesion: 0.22
Nodes (9): 1.10 Background Jobs & Worker Service, 1.11 Tests & Quality Assurance, 1.1 Frontend Structure, 1.2 Backend Structure, 1.3 Database Models & Schema, 1.4 Database Migrations, 1.5 API Routes & Endpoints, 1.7 GitHub Integration (+1 more)

### Community 160 - "RepoMind 2.0 — UI Design"
Cohesion: 0.25
Nodes (7): Application Shell, Design System, Navigation, Page Hierarchy / Route Structure, RepoMind 2.0 — UI Design, Reusable / Feature Components — PR Review Page Breakdown, State Management

### Community 161 - "_extract_py_signatures"
Cohesion: 0.36
Nodes (5): _extract_py_signatures(), _handle_func(), visit_AsyncFunctionDef(), visit_FunctionDef(), FunctionSignature

### Community 162 - "ReviewRunResponse"
Cohesion: 0.25
Nodes (6): ReviewRunResponse, Config, `GET /review-runs/{id}`, `POST /pull-requests/{id}/review`, `POST /review-runs/{id}/approve`, Review Endpoints

### Community 163 - "RepoMind — Implementation Plan"
Cohesion: 0.29
Nodes (6): Definition of Done (applies to every phase/feature), Dependency Graph, Parallelization Notes, Phase Overview, Recommended Build Order (condensed), RepoMind — Implementation Plan

### Community 164 - "RepoMind — Scope"
Cohesion: 0.29
Nodes (6): Conflicts Resolved — Which Scope Is "Current", Future Scope, In Scope (Current Phase — Scope B, Internal Company MVP), MVP vs. Production Boundary, Out of Scope (Current Phase), RepoMind — Scope

### Community 165 - "Local development environment"
Cohesion: 0.29
Nodes (6): Backend, Environment Configuration, Frontend, Local development environment, PostgreSQL & pgvector, Running the Application

### Community 166 - "_extract_py_symbols_with_lines"
Cohesion: 0.38
Nodes (4): _extract_py_symbols_with_lines(), _record_func(), visit_AsyncFunctionDef(), visit_FunctionDef()

### Community 167 - "RepoMind 2.0 — Requirements"
Cohesion: 0.33
Nodes (5): Core Mechanics, Functional Requirements, Non-Functional Requirements, RepoMind 2.0 — Requirements, Tech Stack Requirements

### Community 168 - "RepoMind 2.0 — API Design"
Cohesion: 0.33
Nodes (5): API Conventions, Authentication, Current APIs, Example — Review Run Response Shape, RepoMind 2.0 — API Design

### Community 169 - "RepoMind — Coding Standards"
Cohesion: 0.33
Nodes (5): AI / ML, Backend (Python / FastAPI), Frontend (TypeScript / React), General, RepoMind — Coding Standards

### Community 172 - "RepoMind 2.0 Feature Code Flow Walkthroughs"
Cohesion: 0.29
Nodes (6): 3. RAG Pipeline Flow (Repository Indexing, Chunking, Embedding), 3a. Ingestion Trigger & Job Queue, 3b. Fetch & Chunking, 3c. Embedding & Vector Storage, 4. Chat Assistant Flow (RAG Query Time), RepoMind 2.0 Feature Code Flow Walkthroughs

### Community 175 - "RepoMind 2.0 Complete Technical Guide"
Cohesion: 0.13
Nodes (14): 10. Manager 1-Minute Explanation, 11. Manager Q&A, 12. Known Limitations & Remaining Work, 1. Executive Summary & Product Problem, 2. Technology Stack & High-level Architecture, 4. Frontend Architecture, 6. Authentication, Security & Credential Expiry, 7. Repository Indexing, Chunking, and Embeddings (+6 more)

### Community 176 - "Diagram — PR Review Sequence"
Cohesion: 0.50
Nodes (3): Diagram — PR Review Sequence, Job State Machine, Re-analysis Sequence

### Community 177 - "Diagram — RAG Pipeline"
Cohesion: 0.50
Nodes (3): Diagram — RAG Pipeline, Indexing, Retrieval

### Community 186 - "build_user_content"
Cohesion: 0.33
Nodes (3): build_user_content(), test_f_prompt_injection_framing(), Stage 7: Build Prompt + Call LLM (with Retry)

### Community 187 - "_validate_single_finding"
Cohesion: 0.10
Nodes (7): _compute_relevance(), _find_linter_confirmation(), _find_supporting_chunks(), _validate_single_finding(), _verify_file_in_diff(), FindingSchema, test_explainable_7_factor_risk_score_with_actions()

### Community 189 - "GitHubAPIError"
Cohesion: 0.16
Nodes (5): GitHubAPIError, GitHubTransientError, TestRepositoryConnect, mock_get_repo_contents(), GitHub Client API Calls

### Community 191 - "ChangeImpactAnalysis"
Cohesion: 0.13
Nodes (11): _get_authorized_repo(), get_impact_analysis_by_id(), get_impact_graph(), get_latest_pr_impact(), trigger_impact_analysis(), AffectedComponentResponse, BreakingChangeResponse, ChangeImpactAnalysisResponse (+3 more)

### Community 192 - "TestScenario"
Cohesion: 0.21
Nodes (3): TestCodeGenerator, TestScenario, test_generator_creates_pending_test_case()

### Community 193 - "impact/engine.py"
Cohesion: 0.23
Nodes (6): DetectedCodeChanges, AffectedComponent, _fallback_traversal(), TraversalResult, traverse_dependencies(), test_reverse_dependency_traversal_hops()

### Community 197 - "RepoMind Intelligence — Current System Architecture"
Cohesion: 0.17
Nodes (11): 1. High-Level System Architecture, 2. Technology Stack Specifications, 4.1 Authentication & Session Handling, 4.2 Role-Based Access Control (RBAC), 4. API Communication & Security Architecture, 5. Existing AI Pipeline & Review Execution, 6. Repository Indexing & Vector Search Workflow, 7. GitHub Webhook Ingestion Workflow (+3 more)

### Community 198 - "End-to-End Flow"
Cohesion: 0.12
Nodes (15): 11 — Feature Flow: AI Chat Assistant, 1. Create a Chat Session, 2. Send a Message, 4. Build Evidence + System Prompt, 5. Build User Content with History, 7. Persist Messages, 8. Return Response, API Endpoints (+7 more)

### Community 204 - "FindingSchema"
Cohesion: 0.08
Nodes (26): validate_findings(), ValidatedFinding, compute_finding_fingerprint(), _persist_validated_findings(), is_match(), _make_validated_finding(), test_def_03_no_infinite_zombie_duplication_across_runs(), test_def_03_reopened_finding_lifecycle_on_regression() (+18 more)

### Community 206 - "16 — API Endpoint Reference"
Cohesion: 0.12
Nodes (14): get_org_analytics(), 16 — API Endpoint Reference, All Registered API Endpoints, Analytics Endpoints, Authentication Endpoints, Common Response Codes, CORS Configuration, `GET /auth/me` (+6 more)

### Community 207 - "get_current_user"
Cohesion: 0.08
Nodes (13): extract_token_from_request(), get_current_user(), _get_current_user_lazy(), get_db(), health_check(), FindingStatusUpdate, list_security_findings(), SecurityFindingResponse (+5 more)

### Community 213 - "make_client_for_user"
Cohesion: 0.25
Nodes (5): make_client_for_user(), test_generate_and_execute_test_case_endpoints(), test_get_pr_test_scenarios_and_filtering(), test_get_test_dashboard_endpoint(), test_trigger_test_analysis_endpoint()

### Community 218 - "Things I Must Not Misunderstand"
Cohesion: 0.33
Nodes (5): Learning Checklist, Part 26 — Developer Mental Model, Part 27 — Glossary, Things I Must Not Misunderstand, Verification Snapshot

## Knowledge Gaps
- **18 isolated node(s):** `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector`, `Per-User GitHub OAuth`, `Organization` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1701 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **97 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `github/routes.py` to `Project`, `organizations/service.py`, `RoleEnum`, `get`, `chat/routes.py`, `onboarding/routes.py`, `seed_demo_intelligence.py`, `test_review.py`, `test_architecture_intelligence.py`, `test_intelligence_routes.py`, `UserOnboardingProgress`, `test_historical_intelligence.py`, `review/router.py`, `Onboarding Authorization Tests`, `_get_authorized_repo`, `GitHubIdentity`, `PullRequest`, `RAGRepository`, `auth/routes.py`, `history/routes.py`, `GitHubAPIError`, `ChangeImpactAnalysis`, `ReviewRun`, `test_change_impact_analyzer.py`, `intelligence/routes.py`, `test_blueprint_persistence_and_api_roundtrip`, `16 — API Endpoint Reference`, `get_current_user`, `sqlalchemy`, `CodeGraphNode`, `PullRequest`, `Finding`, `onboarding/service.py`, `test_test_runner.py`, `testing/routes.py`, `Directory Deep Dive`?**
  _High betweenness centrality (0.180) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `User` (e.g. with `get_org_analytics()` and `create_architecture_rule()`) actually correct?**
  _`User` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.036653091447611995 - nodes in this community are weakly interconnected._
- **Why does `Key Files` connect `chat/routes.py` to `github/routes.py`, `App`, `02 — Feature Flow: Authentication`, `get_current_user`, `auth/routes.py`?**
  _High betweenness centrality (0.143) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `Repository` (e.g. with `get_organization_analytics()` and `_get_authorized_repo()`) actually correct?**
  _`Repository` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `typing` be split into smaller, more focused modules?**
  _Cohesion score 0.03279279279279279 - nodes in this community are weakly interconnected._