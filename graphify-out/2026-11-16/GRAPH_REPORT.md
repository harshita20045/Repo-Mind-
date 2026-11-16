# Graph Report - Repo-Mind-  (2026-11-16)

## Corpus Check
- 462 files · ~262,578 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 15 file(s) not represented in the graph (top: .bat 4, (none) 3, .ini 2)

## Summary
- 3787 nodes · 9841 edges · 227 communities (158 shown, 69 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 1276 edges (avg confidence: 0.93)
- Token cost: 152,469 input · 7,531 output

## Graph Freshness
- Built from commit: `d5914d76`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- CodeKnowledgeGraph
- Frontend Dependencies
- typing
- github/routes.py
- Repository
- test_review.py
- organizations/service.py
- RoleEnum
- PullRequest
- App.jsx
- chat/service.py
- analyzer.py
- test_gap09_worker_recovery.py
- WebhookEvent
- User
- 2.1 Domain 1: Authentication & Multi-Tenant Hierarchy
- ReviewPage.jsx
- GitHub API Client
- RAGRetriever
- re
- react
- OnboardingService
- Document
- test_review.py
- RepoMind Intelligence 2.0 — Development Handover Report
- RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough
- test_architecture_intelligence.py
- RawDebtIssue
- LanguageAwareParser
- 09 — Feature Flow: Risk Scoring Engine
- test_historical_intelligence.py
- RepositoryTopologyPage.jsx
- Organization API Schemas
- Permission Normalization Tests
- review/router.py
- tech_debt/routes.py
- Onboarding Authorization Tests
- App
- test_linter.py
- DashboardPage.jsx
- _get_authorized_repo
- encrypt_token
- test_onboarding_service.py
- re
- TextChunker
- api.js
- github/service.py
- GithubConnection
- GitHubAPIError
- test_pr_review_engine_upgrade.py
- RepoMind Phase 6–7 Complete Technical Walkthrough
- Step 2: Apply Gap Detection Categories
- auth/routes.py
- index_repository
- architecture/engine.py
- Button
- run_review
- PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT
- 10 — Feature Flow: Human Review Approval Gate
- logging
- Multi-tenant Security Tests
- 2. Detailed Endpoint Inventory & Contract Audit
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
- chat/routes.py
- RepoMind — Monitoring & Observability
- onboarding/models.py
- RepoMind — Architecture Decision Record
- Review Pipeline: 11 Stages
- sys
- 14 — Feature Flow: Background Worker
- test_change_impact_analyzer.py
- test_change_impact_analyzer.py
- RepoMind — Development Guide
- ReviewRun
- .run_analysis
- RepoMind 2.0 Complete System Architecture
- README.md
- 18 — Feature Flow: ML Prediction (PR Cycle Time)
- onboarding/service.py
- extract_pr_analysis_context
- RawDebtIssue
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
- Document
- test_intelligence_routes.py
- RepoMind 2.0 — System Architecture
- RepoMind — Troubleshooting
- 21 — Final Feature Status Matrix
- .retrieve
- react
- RepositoryScanner
- RepoMind — Authentication & Authorization
- RepoMind — Secrets Management
- RepoMind 2.0 — Deployment Guide (No Docker)
- 2. Phase-by-Phase Implementation Specifications
- sparsevec.h
- 4. Database Discrepancies & Audit Findings
- DocumentLoader
- inspect
- RepoMind 2.0 — Project Overview
- 2. Analytics Queries
- architecture/routes.py
- RiskAssessmentResponse
- RepoMind — Git Workflow
- RepoMind — Test Plan
- RepoMind — Database Migrations
- Code Connection Map
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
- SizeVisitor
- analyze_dead_code
- dataclasses
- Model Detail: Review
- Diagram — PR Review Sequence
- Diagram — RAG Pipeline
- CodeGraphEdge
- component-architecture.md
- data-flow.md
- deployment-architecture.md
- system-context.md
- test-cases.md
- 16 — API Endpoint Reference
- Key Files
- Settings
- encrypt_token
- ChangeImpactAnalysis
- 2.3 Domain 3: Review & Risk Engine
- process_automation_actions
- End-to-End Flow
- _setup_test_pr
- make_client_for_user
- `_validate_finding()` — Per-Finding Logic
- list_security_findings
- RepoMind 2.0 Feature Code Flow Walkthroughs
- ReviewRunResponse
- End-to-End Flow
- 03 — Feature Flow: GitHub Repository Connection & Sync
- Key Architectural Facts (Quick Reference)
- decide_review_run
- 2.2 Domain 2: GitHub Integration & Pull Requests
- 2.5 Domain 5: Collaboration & Developer Onboarding
- test_chat_api_route_e2e_grounded_response
- fixture
- PART 1 — EXECUTIVE EXPLANATION
- run_migrations_offline
- run_migrations_online
- health_check

## God Nodes (most connected - your core abstractions)
1. `User` - 199 edges
2. `Repository` - 150 edges
3. `Project` - 112 edges
4. `ReviewRun` - 108 edges
5. `PullRequest` - 106 edges
6. `Organization` - 102 edges
7. `OrganizationMembership` - 84 edges
8. `react` - 78 edges
9. `RoleEnum` - 75 edges
10. `run_review()` - 60 edges

## Surprising Connections (you probably didn't know these)
- `Key Files` --references--> `handleLoginSuccess()`  [INFERRED]
  Docs/architecture/feature_flow_authentication.md → frontend/src/App.jsx
- `4.1 Authentication & Session Handling` --references--> `apiRequest()`  [INFERRED]
  Docs/CURRENT_ARCHITECTURE.md → frontend/src/lib/api.js
- ``ChatMessage`` --references--> `ChatMessage`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- ``ChatSession`` --references--> `ChatSession`  [INFERRED]
  Docs/architecture/feature_flow_chat_assistant.md → backend/app/chat/models.py
- `5. repository_id Authority` --references--> `PullRequest`  [INFERRED]
  Docs/architecture/security_architecture.md → backend/app/github/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GitHub OAuth Identity Linking** — repomind_2_0_architecture_flow_github_oauth, backend_app_github_oauth_routes_github_oauth_callback, backend_app_github_oauth_service_upsert_github_identity [EXTRACTED 1.00]
- **Developer Onboarding Subsystem** — walkthrough_repository_blueprint, walkthrough_user_onboarding_progress, walkthrough_onboarding_service [EXTRACTED 1.00]
- **RAG Indexing Pipeline** — backend_app_rag_loader, backend_app_rag_chunker, backend_app_rag_embedder, backend_app_rag_repository, postgresql_pgvector [EXTRACTED 1.00]

## Communities (227 total, 69 thin omitted)

### Community 0 - "CodeKnowledgeGraph"
Cohesion: 0.18
Nodes (3): CodeKnowledgeGraph, test_knowledge_graph_construction_and_mermaid(), test_knowledge_graph_persistence()

### Community 1 - "Frontend Dependencies"
Cohesion: 0.04
Nodes (57): dependencies, mermaid@^12.3.0, react@^18.2.0, react-diff-viewer-continued@^4.4.0, react-dom@^18.2.0, react-markdown@^10.1.0, react-router-dom@^7.18.3, @tanstack/react-query@^5.102.8 (+49 more)

### Community 2 - "typing"
Cohesion: 0.04
Nodes (37): upgrade(), downgrade(), upgrade(), downgrade(), upgrade(), upgrade(), downgrade(), upgrade() (+29 more)

### Community 3 - "github/routes.py"
Cohesion: 0.06
Nodes (30): ProjectMergePolicy, _assert_repo_access(), connect_repository(), get_merge_policy(), get_pull_request(), get_pull_request_commits(), get_pull_request_conflicts(), get_pull_request_events() (+22 more)

### Community 4 - "Repository"
Cohesion: 0.06
Nodes (29): Project, ProjectMember, Repository, TeamMember, test_setup(), test_insufficient_evidence_explicit_disclosure(), _setup_repo_and_pr(), test_gap_08_completed_historical_runs_are_preserved() (+21 more)

### Community 5 - "test_review.py"
Cohesion: 0.06
Nodes (25): FallbackProvider, GeminiProvider, retry_if_transient_error(), get_llm_provider(), GroqProvider, LLMProvider, LLMProviderError, LocalProvider (+17 more)

### Community 6 - "organizations/service.py"
Cohesion: 0.10
Nodes (35): AuditLog, hash_invitation_token(), Team, create_organization(), create_project(), create_repository(), create_team(), get_organization() (+27 more)

### Community 7 - "RoleEnum"
Cohesion: 0.09
Nodes (24): extract_token_from_request(), get_current_user(), RoleEnum, run_decision_test(), test_approve_developer(), test_approve_org_admin(), test_approve_reviewer(), test_approve_team_lead() (+16 more)

### Community 8 - "PullRequest"
Cohesion: 0.07
Nodes (20): get_db(), GitHubComment, GitHubCredential, GitHubIdentity, GitHubRepositoryAccess, GitHubReview, HumanReview, PullRequest (+12 more)

### Community 9 - "App.jsx"
Cohesion: 0.13
Nodes (27): App(), handleLoginSuccess(), queryClient, RepositoryNav(), SEVERITY_STYLES, STATUS_STYLES, StatusBadge(), authApi (+19 more)

### Community 10 - "chat/service.py"
Cohesion: 0.16
Nodes (10): ChatMessage, _build_grounded_mock_response(), get_session_messages(), get_sessions(), send_message(), Chat Endpoints, `POST /chat/sessions/{id}/messages`, 3. RAG Context Retrieval (+2 more)

### Community 11 - "analyzer.py"
Cohesion: 0.14
Nodes (3): _extract_adrs_from_markdown(), _infer_modules_from_title_and_text(), TestIntelligenceAnalyzer

### Community 12 - "test_gap09_worker_recovery.py"
Cohesion: 0.10
Nodes (21): _setup_repo_and_pr(), test_gap_09_abandoned_job_exceeding_max_retries_fails(), test_gap_09_abandoned_job_with_superseded_sha_transitions_to_superseded(), test_gap_09_active_heartbeat_job_is_not_recovered(), test_gap_09_concurrent_worker_recovery_postgres_skip_locked(), worker_recovery_task(), test_gap_09_heartbeat_renewal_and_token_validation(), test_gap_09_stale_running_job_recovered_to_pending() (+13 more)

### Community 13 - "WebhookEvent"
Cohesion: 0.25
Nodes (7): WebhookEvent, 12 — Feature Flow: GitHub Webhook Automation, Configuration Required, Feature Summary, Key Files, Trigger Actions, Webhook Event Model

### Community 14 - "User"
Cohesion: 0.07
Nodes (38): Organization, OrganizationMembership, User, authenticate_user(), bootstrap_system(), change_password(), decode_access_token(), get_user_by_email() (+30 more)

### Community 15 - "2.1 Domain 1: Authentication & Multi-Tenant Hierarchy"
Cohesion: 0.13
Nodes (15): 2.1 Domain 1: Authentication & Multi-Tenant Hierarchy, 2.4 Domain 4: Code-Aware RAG & pgvector Storage, 2.6 Domain 6: Webhooks, Audit & ML, 2. Detailed Table Specifications & Relationships, `audit_log`, `document`, `document_chunk`, `ml_prediction` (+7 more)

### Community 16 - "ReviewPage.jsx"
Cohesion: 0.14
Nodes (18): ChatAssistant(), SOURCE_TYPE_STYLES, SUPPORTED_QUESTIONS, ConflictCard(), ConflictList(), EvidenceStatus(), FindingCard(), LifecycleBadge() (+10 more)

### Community 17 - "GitHub API Client"
Cohesion: 0.11
Nodes (4): GitHubClient, reconcile_pull_requests(), sync_pull_request_details(), main()

### Community 18 - "RAGRetriever"
Cohesion: 0.10
Nodes (11): RAGRetriever, retrieve_context(), test_empty_repository(), test_invalid_top_k(), test_relevant_retrieval(), test_repository_isolation(), test_top_k(), Part 23 — Git Checkpoints (+3 more)

### Community 19 - "re"
Cohesion: 0.20
Nodes (7): classify_query(), extract_endpoints(), extract_files(), extract_pr_id(), extract_symbols(), ExtractedEntities, test_entity_extraction_helpers()

### Community 20 - "react"
Cohesion: 0.11
Nodes (22): ArchitectureDashboard(), ArchitectureHealthOverview(), ArchitectureViolationsList(), CircularDependencyGraph(), FlowAnalysisViewer(), AffectedComponentList(), TIER_CONFIG, BreakingChangesList() (+14 more)

### Community 21 - "OnboardingService"
Cohesion: 0.13
Nodes (8): RepositoryBlueprint, OnboardingService, test_duplicate_concurrent_generation_prevention(), test_failed_regeneration_preserves_previous_valid_blueprint(), test_stale_pending_job_recovery(), test_grounding_filters_and_validates_smart_features(), test_snapshot_hash_changes_on_file_addition_and_removal(), test_snapshot_hash_changes_when_second_file_modified()

### Community 22 - "Document"
Cohesion: 0.06
Nodes (18): EmbedderError, LocalEmbedder, RAGRepository, embedder(), setup_test_repos(), test_embedding_dimension(), test_embedder_validation(), test_persistence_and_idempotency() (+10 more)

### Community 23 - "test_review.py"
Cohesion: 0.06
Nodes (27): derive_query_from_diff(), LLMOutputParseError, parse_llm_output(), ReviewDecisionAction, ReviewOutput, test_malformed_ai_output_parsing(), test_multi_stage_review_8_categories_validation(), test_c_schema_validation_failure_marks_failed() (+19 more)

### Community 24 - "RepoMind Intelligence 2.0 — Development Handover Report"
Cohesion: 0.06
Nodes (32): 10. AI Chat Assistant (`/chat`), 11. AI Test Intelligence (`/repositories/{id}/test-intelligence`, `/test-scenarios`, `/generated-tests`, `/test-intelligence`), 12. Technical Debt Intelligence (`/repositories/{id}/tech-debt`), 13. Security & Analytics (`/security`, `/analytics`), 1. Health & Core, 2. Authentication & Memberships (`/auth`), 3. Organizations & Projects (`/organizations`, `/projects`), 4. GitHub Integration & Webhooks (+24 more)

### Community 25 - "RepoMind — Developer Onboarding & Codebase Blueprint Walkthrough"
Cohesion: 0.05
Nodes (39): 10. Complete API Reference, 11. Role Hierarchy & Repository Authorization, 12. Private Progress & Anti-Surveillance Guarantees, 13. Frontend Component & Routing Architecture, 14. Mermaid Rendering Security, 15. Developer Onboarding User Journey, 16. Team Lead Refresh User Journey, 17. Testing Commands & Actual Results (+31 more)

### Community 26 - "test_architecture_intelligence.py"
Cohesion: 0.12
Nodes (15): check_architecture_rules(), GroundedViolation, _matches_pattern(), CircularDependency, detect_circular_dependencies(), FlowAnalysisResult, classify_layer(), get_layer_rank() (+7 more)

### Community 27 - "RawDebtIssue"
Cohesion: 0.16
Nodes (3): analyze_maintainability(), MaintainabilityVisitor, test_maintainability_analyzer_detects_parameter_bloat()

### Community 28 - "LanguageAwareParser"
Cohesion: 0.16
Nodes (6): CodeSymbol, LanguageAwareParser, ParsedCodeFile, test_js_ts_parsing(), test_parser_syntax_error_resilience(), test_python_ast_parsing()

### Community 29 - "09 — Feature Flow: Risk Scoring Engine"
Cohesion: 0.15
Nodes (12): 09 — Feature Flow: Risk Scoring Engine, Blast Radius and Test Impact, `_calculate_blast_radius(changed_files)` returns:, `calculate_risk()` Structure, `_calculate_test_impact(changed_files, diff)` returns:, Entry Point, Fairness Rule, Feature Summary (+4 more)

### Community 30 - "test_historical_intelligence.py"
Cohesion: 0.05
Nodes (45): PullRequestCommit, PullRequestFile, compute_and_index_hotspots(), mine_and_index_commits(), parse_and_index_adrs(), ArchitectureDecisionRecord, HistoricalCommitRecord, RecurringIssueHotspot (+37 more)

### Community 31 - "RepositoryTopologyPage.jsx"
Cohesion: 0.15
Nodes (19): InteractiveKnowledgeGraph(), Badge(), GraphNodeBadge(), SearchInput(), Select(), Table(), TableBody(), TableCell() (+11 more)

### Community 32 - "Organization API Schemas"
Cohesion: 0.17
Nodes (20): GithubConnectionBase, GithubConnectionCreate, GithubConnectionResponse, MemberBase, MemberInvite, MemberRoleUpdate, OrganizationBase, OrganizationCreate (+12 more)

### Community 33 - "Permission Normalization Tests"
Cohesion: 0.10
Nodes (7): test_def_02_action_casing_cannot_bypass_approve_permission(), override_db(), override_user(), test_def_02_arbitrary_unsupported_action_rejected(), test_def_02_lead_approve_normalized_and_triggers_merge_policy(), test_def_02_reject_permission_and_queue_worker(), test_def_06_missing_pull_request_returns_404_no_500()

### Community 34 - "review/router.py"
Cohesion: 0.10
Nodes (9): ConflictResponse, Config, FindingResponse, Config, HumanDecisionRequest, HumanDecisionResponse, Config, ReviewTriggerResponse (+1 more)

### Community 35 - "tech_debt/routes.py"
Cohesion: 0.14
Nodes (12): analyze_repository_tech_debt(), _get_authorized_repo(), get_tech_debt_dashboard(), get_tech_debt_trends(), list_tech_debt_issues(), update_issue_status(), TechnicalDebtAnalyzeRequest, TechnicalDebtDashboardResponse (+4 more)

### Community 36 - "Onboarding Authorization Tests"
Cohesion: 0.22
Nodes (16): cleanup_overrides(), make_client_for_user(), test_10_invalid_track_and_milestone_ids_are_rejected(), test_11_repository_access_enforced_across_all_endpoints(), test_12_active_generation_conflict_returns_409(), test_13_unindexed_repository_error_returns_400(), test_14_responses_do_not_leak_internal_prompts_or_traces(), test_1_authorized_user_can_retrieve_blueprint() (+8 more)

### Community 37 - "App"
Cohesion: 0.10
Nodes (28): 19 — Feature Flow: Frontend Application, `App.jsx` — Root Component, Application Entry Point, Feature Summary, Key Files Summary, Layout Structure, `lib/api.js` — API Wrapper, `ProtectedRoute` Component (+20 more)

### Community 38 - "test_linter.py"
Cohesion: 0.05
Nodes (36): _persist_failure(), _persist_result(), run_linters(), _safe_join(), BanditLinter, LinterTool, RuffLinter, _extract_linter_issues() (+28 more)

### Community 39 - "DashboardPage.jsx"
Cohesion: 0.15
Nodes (22): Page Components, HistoricalContextCard(), Card(), MetricCard(), SectionCard(), CardListSkeleton(), DashboardSkeleton(), MetricCardSkeleton() (+14 more)

### Community 40 - "_get_authorized_repo"
Cohesion: 0.13
Nodes (12): ArchitectureRule, create_architecture_rule(), delete_architecture_rule(), get_architecture_flows(), _get_authorized_repo(), get_circular_dependencies(), get_latest_architecture_analysis(), list_architecture_rules() (+4 more)

### Community 41 - "encrypt_token"
Cohesion: 0.12
Nodes (12): decrypt_token(), encrypt_token(), _get_fernet(), GithubConnection, test_token_refresh_lifecycle(), TestTokenEncryption, 1. Connect a GitHub Repository, 2. PR Sync (called after connect and on-demand) (+4 more)

### Community 42 - "test_onboarding_service.py"
Cohesion: 0.13
Nodes (7): LLMBlueprintPayload, sample_valid_llm_json(), test_generation_and_cache_hit(), test_pydantic_schema_invalid_mermaid_fails(), test_pydantic_schema_missing_tracks_fails(), test_pydantic_schema_validation_success(), test_schema_smart_features_validation()

### Community 43 - "re"
Cohesion: 0.15
Nodes (13): _detect_api_contract_conflicts(), _detect_architecture_conflicts(), _detect_configuration_conflicts(), detect_conflicts(), _detect_mechanical_conflicts(), _detect_security_policy_conflicts(), _detect_test_contract_conflicts(), DetectedConflict (+5 more)

### Community 44 - "TextChunker"
Cohesion: 0.15
Nodes (5): ASTChunk, ASTCodeChunker, TextChunker, test_chunker_determinism_and_overlap(), `backend/app/rag/chunker.py`

### Community 46 - "api.js"
Cohesion: 0.11
Nodes (22): ActivityLog(), ReviewStateIndicator(), TestCodeViewer(), TestExecutionResult(), CATEGORIES, TestIntelligenceDashboard(), CATEGORY_THEMES, PRIORITY_BADGES (+14 more)

### Community 47 - "github/service.py"
Cohesion: 0.12
Nodes (16): connect_repository(), get_decrypted_github_token_for_org(), get_decrypted_github_token_for_user(), get_github_connection_for_org(), get_github_repositories(), _get_org_id_for_repository(), get_pull_request_by_id(), get_pull_request_diff() (+8 more)

### Community 48 - "GithubConnection"
Cohesion: 0.10
Nodes (18): Index Trigger, 04 — Feature Flow: RAG Indexing, Crash Recovery, Database Tables, Detailed Step-by-Step, Embedding Model Details, Feature Summary, Manual Re-Index (+10 more)

### Community 49 - "GitHubAPIError"
Cohesion: 0.15
Nodes (4): GitHubAPIError, GitHubTransientError, test_run_linters_orchestration(), mock_get_repo_contents()

### Community 50 - "test_pr_review_engine_upgrade.py"
Cohesion: 0.03
Nodes (39): _compute_relevance(), _find_linter_confirmation(), _find_supporting_chunks(), validate_findings(), _validate_single_finding(), ValidatedFinding, _verify_file_in_diff(), FindingSchema (+31 more)

### Community 51 - "RepoMind Phase 6–7 Complete Technical Walkthrough"
Cohesion: 0.07
Nodes (29): Executive Summary, Learning Checklist, Part 10 — PostgreSQL + pgvector Internal Understanding, Part 12 — Phase 7 Overview, Part 13 — Phase 7 End-to-End Retrieval Flow, Part 14 — Retriever Code Deep Dive, Part 15 — Cosine Retrieval, Part 16 — top_k (+21 more)

### Community 52 - "Step 2: Apply Gap Detection Categories"
Cohesion: 0.08
Nodes (24): A. Entry and Exit Conditions, Analyzing Business Logic Gaps, B. State Definitions, C. State Transitions, Checklist for Quick Analysis, Common Gap Patterns, D. Exceptional Paths, E. Billing and Credit Rules (+16 more)

### Community 53 - "auth/routes.py"
Cohesion: 0.06
Nodes (51): bootstrap(), change_password_route(), format_auth_response(), get_me(), login(), logout(), onboard(), set_session_cookie() (+43 more)

### Community 54 - "index_repository"
Cohesion: 0.13
Nodes (11): index_repository(), test_loader_exclusions(), `backend/app/rag/loader.py`, Function: `chunk_text()`, Function: `embed_chunks()`, Function: `_should_exclude_path()`, Part 2 — Phase 6 Complete End-to-End Flow, Part 4 — Line-by-Line Code Teaching (+3 more)

### Community 55 - "architecture/engine.py"
Cohesion: 0.14
Nodes (9): calculate_architecture_health_score(), ensure_baseline_architecture_rules(), generate_architecture_mermaid(), run_architecture_analysis(), ArchitectureAnalysis, ArchitectureViolation, detect_architecture_pattern(), InferredPatternResult (+1 more)

### Community 56 - "Button"
Cohesion: 0.14
Nodes (21): ArchitectureRuleManager(), ROLE_LABELS, ROLES, TeamManagement(), Button(), SIZE, VARIANT, ConfirmDialog() (+13 more)

### Community 57 - "run_review"
Cohesion: 0.08
Nodes (17): AIAnalysis, _mark_failed(), _persist_risk(), run_review(), _update_progress(), test_gap_08_stale_worker_attempting_to_publish_while_requeued_run_is_inflight(), test_gap_08_superseded_worker_aborts_without_overwriting(), test_gap_08_worker_ownership_fencing_token_invalidation() (+9 more)

### Community 58 - "PHASE 20 — FINAL CLEAN REAL-DATA E2E ACCEPTANCE REPORT"
Cohesion: 0.15
Nodes (12): 10. Defects and Fixes, 11. External Limitations, 12. Conclusion, 1. Objective and Scope, 2. Runtime and Initialization, 3. Authentication & RBAC, 5. Repository Discovery and Connection, 6. Webhook and Review Pipeline (E2E) (+4 more)

### Community 59 - "10 — Feature Flow: Human Review Approval Gate"
Cohesion: 0.18
Nodes (11): 10 — Feature Flow: Human Review Approval Gate, 1. View Completed Review, 2. Trigger Approve/Reject, 3. Authorization Check, 4. Persist Decision (Upsert), End-to-End Flow, Feature Summary, HumanDecision Model (+3 more)

### Community 60 - "logging"
Cohesion: 0.17
Nodes (6): ChangedSymbol, detect_code_changes(), _detect_symbols_from_diff_hunks(), parse_diff_hunks(), PRDiffHunk, main()

### Community 62 - "Multi-tenant Security Tests"
Cohesion: 0.29
Nodes (4): test_chat_session_creation_rejects_foreign_repository(), test_def_04_cross_tenant_chat_retrieval_prevented(), override_db(), override_user()

### Community 63 - "2. Detailed Endpoint Inventory & Contract Audit"
Cohesion: 0.15
Nodes (12): 1. Master API Route Catalog, 2.10 Developer Onboarding Domain, 2.1 Health Domain, 2.5 Review & Decision Domain, 2.6 Webhook Receiver Domain, 2.7 Engineering Analytics Domain, 2.8 Security Browser Domain, 2.9 AI Assistant / Chat Domain (+4 more)

### Community 64 - "Final RBAC Parity & Feature Audit Report"
Cohesion: 0.10
Nodes (17): 4-Role RBAC Model, A. Exact backend roles discovered, B. Four-role mapping, C. Backend permission matrix, D. Frontend permission matrix, E. Feature parity matrix, F. Organization Admin coverage, Final RBAC Parity & Feature Audit Report (+9 more)

### Community 65 - "onboarding/routes.py"
Cohesion: 0.12
Nodes (12): _get_repo_and_verify_access(), get_repository_blueprint(), get_user_onboarding_progress(), refresh_repository_blueprint(), BlueprintGenerationError, GenerationInProgressError, GroundingValidationError, OnboardingServiceError (+4 more)

### Community 66 - "RepoMind Intelligence 2.0 — Complete Technical Audit"
Cohesion: 0.20
Nodes (9): 2.1 Critical Runtime & Dependency Issues, 2.2 Model & Architectural Inconsistencies, 2.3 Mock & Incomplete Endpoints, 2.4 Frontend Test Failures, 2. Technical Audit Findings & Discrepancies, 3. Technology Stack Verification, 4. Conclusion & Audit Sign-Off, Executive Summary (+1 more)

### Community 67 - "intelligence/routes.py"
Cohesion: 0.16
Nodes (15): DependencyExtractor, get_architecture_diagram(), _get_authorized_repo(), get_repository_dependencies(), get_repository_graph(), get_repository_summary(), get_repository_symbols(), trigger_intelligence_indexing() (+7 more)

### Community 89 - "RepoMind — Environment Configuration"
Cohesion: 0.33
Nodes (5): Development, Production, RepoMind — Environment Configuration, Testing / CI, Variables

### Community 90 - "chat/routes.py"
Cohesion: 0.06
Nodes (31): assert_org_permission(), check_org_permission(), _get_current_user_lazy(), get_role_permissions(), Permission, require_org_permission(), _check(), require_permission() (+23 more)

### Community 91 - "RepoMind — Monitoring & Observability"
Cohesion: 0.15
Nodes (12): AI Failures, API Errors, Application Logs, Database Health, GitHub Integration Failures, ML Failures, Performance Metrics, RAG Failures (+4 more)

### Community 92 - "onboarding/models.py"
Cohesion: 0.22
Nodes (3): UserOnboardingProgress, update_user_onboarding_progress(), test_user_progress_isolated_and_updatable()

### Community 93 - "RepoMind — Architecture Decision Record"
Cohesion: 0.11
Nodes (17): ADR-001 — Modular Monolith Architecture, ADR-002 — Frontend: React + TypeScript + Tailwind, ADR-003 — Backend: FastAPI + Pydantic, ADR-004 — Database: PostgreSQL + SQLAlchemy + Alembic, ADR-005 — Vector Storage: pgvector (not a dedicated vector database), ADR-006 — Embeddings: sentence-transformers (local), ADR-007 — Retrieval Mechanism: pgvector Cosine Similarity, Repository-Scoped, ADR-008 — GitHub Integration Strategy: PAT + REST API (Phase 1) (+9 more)

### Community 94 - "Review Pipeline: 11 Stages"
Cohesion: 0.13
Nodes (10): build_user_content(), test_f_prompt_injection_framing(), Review Pipeline: 11 Stages, Stage 11: Mark Completed, Stage 1: Resolve PR + Repository (DB Authoritative), Stage 2: Create ReviewRun (pending → running), Stage 3: Fetch PR Diff + Changed Files, Stage 7: Build Prompt + Call LLM (with Retry) (+2 more)

### Community 96 - "14 — Feature Flow: Background Worker"
Cohesion: 0.11
Nodes (19): 14 — Feature Flow: Background Worker, Configuration, Consecutive Error Tracking, Error Handling, Feature Summary, Job Lifecycle States, Key Files, LLM Provider Initialization (+11 more)

### Community 97 - "test_change_impact_analyzer.py"
Cohesion: 0.11
Nodes (14): BreakingChange, _check_signature_compatibility(), detect_breaking_changes(), _detect_breaking_from_diff_lines(), _detect_configuration_breaks(), _detect_database_schema_breaks(), _extract_py_signatures(), _handle_func() (+6 more)

### Community 98 - "test_change_impact_analyzer.py"
Cohesion: 0.11
Nodes (14): DetectedCodeChanges, generate_impact_mermaid(), generate_test_recommendations(), run_change_impact_analysis(), ChangeImpactAnalysis, AffectedComponent, _fallback_traversal(), TraversalResult (+6 more)

### Community 99 - "RepoMind — Development Guide"
Cohesion: 0.13
Nodes (14): Backend Setup (Python / FastAPI), Database Initialization and Migrations, Environment Variables, Frontend Setup, Linting and Formatting, No Docker, PostgreSQL Setup (Native), RepoMind — Development Guide (+6 more)

### Community 100 - "ReviewRun"
Cohesion: 0.09
Nodes (30): get_organization_analytics(), Conflict, Finding, FindingEvidence, ReviewRun, RiskAssessment, test_get_review_run(), test_get_review_run_cross_tenant() (+22 more)

### Community 101 - ".run_analysis"
Cohesion: 0.09
Nodes (12): analyze_duplication(), _normalize_line(), compute_issue_fingerprint(), re_split_spec(), TechnicalDebtEngine, aggregate_technical_debt_metrics(), calculate_maintainability_score(), TechnicalDebtIssue (+4 more)

### Community 102 - "RepoMind 2.0 Complete System Architecture"
Cohesion: 0.11
Nodes (26): AutomationAction, HumanDecision, PART 10 — WEBHOOK ARCHITECTURE, PART 11 — PULL REQUEST LIFECYCLE, PART 12 — REVIEW WORKER, PART 16 — HUMAN REVIEW DECISIONS, PART 17 — REQUEST CHANGES, PART 19 — MERGE (+18 more)

### Community 103 - "README.md"
Cohesion: 0.14
Nodes (7): Documentation Set, Documents, Feature Flows (Start-to-End Traces), RepoMind 2.0 — Architecture Documentation Index, Source Code Truth Principles, Status & Summary, System-Level

### Community 104 - "18 — Feature Flow: ML Prediction (PR Cycle Time)"
Cohesion: 0.11
Nodes (17): 18 — Feature Flow: ML Prediction (PR Cycle Time), 1. API Request, 2. Training Data Check, 3. Rule-Based Baseline, 4. Response, Current State (as observed in source), Data Model, Dataset Building (+9 more)

### Community 105 - "onboarding/service.py"
Cohesion: 0.28
Nodes (13): CautionZone, ExecutionFlows, ExecutionFlowStep, GlossaryItem, MilestoneItem, ReadingOrderItem, RepositoryBlueprintResponse, RequestFlowStep (+5 more)

### Community 106 - "extract_pr_analysis_context"
Cohesion: 0.17
Nodes (6): extract_pr_analysis_context(), PRAnalysisContext, PRFileSummary, query_related_modules(), test_empty_diff_and_pure_deletion_handling(), test_pr_analysis_extraction_and_diff_hunks()

### Community 107 - "RawDebtIssue"
Cohesion: 0.07
Nodes (14): analyze_complexity(), ComplexityVisitor, analyze_dependencies(), analyze_deprecation(), DeprecationVisitor, analyze_error_handling(), ErrorHandlingVisitor, RawDebtIssue (+6 more)

### Community 108 - "testing/routes.py"
Cohesion: 0.06
Nodes (32): run_test_intelligence_analysis(), TestCodeGenerator, GeneratedTestCase, TestScenario, execute_generated_test(), generate_test_case(), _get_authorized_repo(), get_pr_test_scenarios() (+24 more)

### Community 109 - "_enqueue_review"
Cohesion: 0.14
Nodes (10): _enqueue_review(), github_webhook(), _resolve_repository(), _upsert_pr_from_webhook(), test_gap_08_concurrent_duplicate_webhooks_serialization(), deliver_webhook(), Webhook Endpoint, Security Properties (+2 more)

### Community 110 - "2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0)"
Cohesion: 0.13
Nodes (14): 1.1 Complete Feature Classification Table, 1. Feature Audit & Classification Matrix, 2. Gap Analysis Against Target Capabilities (RepoMind Intelligence 2.0), Capability 10: Enterprise Security & Multi-tenant Isolation, Capability 1: Repository Intelligence Engine, Capability 2: AI Pull Request Review, Capability 3: Change Impact Analyzer, Capability 4: Architecture Intelligence (+6 more)

### Community 111 - "15 — Database Schema & Model Cheat Sheet"
Cohesion: 0.07
Nodes (26): 15 — Database Schema & Model Cheat Sheet, All SQLAlchemy Models, `audit_log`, `chat_message`, `chat_session`, `commit`, Database Configuration, `document` (+18 more)

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
Cohesion: 0.14
Nodes (14): 08 — Feature Flow: Conflict Detection Engine, Conflict Lifecycle, `detect_conflicts()` Orchestrator, DetectedConflict Dataclass, Detector 1: Mechanical Conflicts, Detector 2: Architecture Conflicts, Detector 3: Security Policy Conflicts, Detector 4: API Contract Conflicts (+6 more)

### Community 131 - "17 — Security Architecture"
Cohesion: 0.15
Nodes (13): 10. PAT Logging Policy, 11. No Auto-Merge Policy, 17 — Security Architecture, 1. Password Security, 2. JWT Session Security, 3. PAT Encryption, 4. LLM Security: System Prompt Separation, 5. repository_id Authority (+5 more)

### Community 132 - "Document"
Cohesion: 0.16
Nodes (8): DocMetadata, DocumentationIntelligence, RepositoryIndexer, Document, DocumentChunk, test_incremental_indexing_lifecycle(), Part 11 — Database Model, Key Files

### Community 133 - "test_intelligence_routes.py"
Cohesion: 0.21
Nodes (10): auth_context(), cleanup_overrides(), make_client_for_user(), test_get_architecture_diagram(), test_get_dependencies(), test_get_graph_and_filtering(), test_get_summary_authorized(), test_get_summary_cross_tenant_forbidden() (+2 more)

### Community 134 - "RepoMind 2.0 — System Architecture"
Cohesion: 0.17
Nodes (11): AI Layer, API Communication, Authentication Flow, Backend, Database, Frontend, Overall Architecture, PR Review Flow (+3 more)

### Community 135 - "RepoMind — Troubleshooting"
Cohesion: 0.17
Nodes (12): AI / LLM, Authentication, Backend, Embeddings, Frontend, GitHub API, Linter Execution, Migrations (+4 more)

### Community 136 - "21 — Final Feature Status Matrix"
Cohesion: 0.17
Nodes (12): 21 — Final Feature Status Matrix, AI Chat, Analytics, Core Features, GitHub Integration, ML Prediction, RAG Indexing, RepoMind 2.0 — Feature Implementation Status (+4 more)

### Community 137 - ".retrieve"
Cohesion: 0.18
Nodes (4): test_dependency_graph_and_call_chain_retrieval(), test_multi_source_retriever_pulls_all_sources(), test_pr_review_rationale_retrieval(), test_test_coverage_retrieval()

### Community 138 - "react"
Cohesion: 0.13
Nodes (15): LoginForm(), CATEGORY_META, DebtCategoryBreakdown(), DebtIssueTable(), SEVERITY_BADGES, STATUS_BADGES, DebtMetricsOverview(), DebtSeverityBar() (+7 more)

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

### Community 145 - "4. Database Discrepancies & Audit Findings"
Cohesion: 0.18
Nodes (10): 1.1 Domain Table Breakdown, 1. Complete Database Schema Inventory, 3. Complete Alembic Migration Chain (27 Revisions), 4.1 Target Database Unmigrated, 4.2 Missing `vector` Extension in Target Database, 4.3 Missing ORM Model for `ml_prediction`, 4.4 Redundant `WebhookEvent` Declarations, 4.5 Embedder Configuration Discrepancy (+2 more)

### Community 146 - "DocumentLoader"
Cohesion: 0.22
Nodes (3): DocumentLoader, test_loader_hashing(), Diagram — AI Review Pipeline (LLM)

### Community 147 - "inspect"
Cohesion: 0.22
Nodes (4): client(), db_session(), setup_test_db(), _verify_test_db_identity()

### Community 148 - "RepoMind 2.0 — Project Overview"
Cohesion: 0.20
Nodes (9): Core Anti-Goals, Current Project Status, High-Level Workflow, Key Technologies, Main Capabilities, Problem Statement, RepoMind 2.0 — Project Overview, Target Users / Intended Usage (+1 more)

### Community 149 - "2. Analytics Queries"
Cohesion: 0.12
Nodes (16): 13 — Feature Flow: Analytics, 1. Frontend Request, 2. Analytics Queries, 3. Response, Base Query Setup, End-to-End Flow, Feature Summary, Key Files (+8 more)

### Community 150 - "architecture/routes.py"
Cohesion: 0.36
Nodes (7): ArchitectureAnalysisResponse, ArchitectureRuleCreateRequest, ArchitectureRuleResponse, ArchitectureRuleUpdateRequest, ArchitectureViolationResponse, CircularDependencyResponse, FlowChainResponse

### Community 152 - "RepoMind — Git Workflow"
Cohesion: 0.22
Nodes (8): Branch Strategy, Commit Conventions, Handling AI Prompt / Model Changes, Handling Database Migrations, Merge Strategy, Pull Requests and Code Review, Release / Versioning Approach, RepoMind — Git Workflow

### Community 153 - "RepoMind — Test Plan"
Cohesion: 0.22
Nodes (8): AI / RAG, Component-Level, Feature-Level, Integration-Level, ML, RepoMind — Test Plan, Security, System-Level

### Community 154 - "RepoMind — Database Migrations"
Cohesion: 0.22
Nodes (9): Alembic Workflow, Applying Migrations, Migration Creation, Migration Review, Migration Testing, Production Migration Precautions, RepoMind — Database Migrations, Rollback Strategy (+1 more)

### Community 155 - "Code Connection Map"
Cohesion: 0.50
Nodes (3): 3. Repository Indexing Flow, 4. Chat & RAG Query Flow, Code Connection Map

### Community 157 - "1. Project Discovery & Layer Inspection"
Cohesion: 0.20
Nodes (10): 1.10 Background Jobs & Worker Service, 1.11 Tests & Quality Assurance, 1.1 Frontend Structure, 1.2 Backend Structure, 1.3 Database Models & Schema, 1.4 Database Migrations, 1.5 API Routes & Endpoints, 1.7 GitHub Integration (+2 more)

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

### Community 171 - "analyze_dead_code"
Cohesion: 0.15
Nodes (3): analyze_dead_code(), DeadCodeVisitor, test_dead_code_analyzer_detects_unreachable_and_unused_private()

### Community 172 - "dataclasses"
Cohesion: 0.29
Nodes (3): FlowChain, trace_architecture_flows(), test_flow_tracing_clean_vs_leaky()

### Community 175 - "Model Detail: Review"
Cohesion: 0.25
Nodes (8): `conflict`, `finding`, `finding_evidence`, `human_decision`, `linter_result`, Model Detail: Review, `review_run`, `risk_assessment`

### Community 176 - "Diagram — PR Review Sequence"
Cohesion: 0.50
Nodes (3): Diagram — PR Review Sequence, Job State Machine, Re-analysis Sequence

### Community 177 - "Diagram — RAG Pipeline"
Cohesion: 0.50
Nodes (3): Diagram — RAG Pipeline, Indexing, Retrieval

### Community 178 - "CodeGraphEdge"
Cohesion: 0.15
Nodes (14): CodeGraphEdge, CodeGraphNode, test_related_module_query_with_knowledge_graph(), 10. Repository-Aware AI Assistant Upgrade (`backend/app/chat/`, `frontend/src/components/Review/ChatAssistant.jsx`), 1. Repository Intelligence Engine (`backend/app/intelligence/`), 2. Advanced AI Pull Request Intelligence (`backend/app/review/analysis.py`, `service.py`, `evidence.py`), 3. Change Impact & Blast Radius Analyzer (`backend/app/impact/`), 4. Architecture Intelligence (`backend/app/architecture/`) (+6 more)

### Community 186 - "16 — API Endpoint Reference"
Cohesion: 0.12
Nodes (13): get_org_analytics(), 16 — API Endpoint Reference, All Registered API Endpoints, Analytics Endpoints, Common Response Codes, CORS Configuration, `GET /repositories/{id}/pull-requests`, Global API Base URL (+5 more)

### Community 187 - "Key Files"
Cohesion: 0.10
Nodes (11): get_review_run(), get_review_run_decisions(), list_review_runs(), _get_org_id_for_pr(), ReviewError, Key Files, _fail_run(), poll_and_execute() (+3 more)

### Community 189 - "encrypt_token"
Cohesion: 0.17
Nodes (5): test_connect_unexpected_pat_field(), test_connect_without_oauth_identity_fails(), _setup_user_and_org(), TestPullRequestEndpoints, TestRepositoryConnect

### Community 191 - "ChangeImpactAnalysis"
Cohesion: 0.16
Nodes (11): _get_authorized_repo(), get_impact_analysis_by_id(), get_impact_graph(), get_latest_pr_impact(), trigger_impact_analysis(), AffectedComponentResponse, BreakingChangeResponse, ChangeImpactAnalysisResponse (+3 more)

### Community 193 - "2.3 Domain 3: Review & Risk Engine"
Cohesion: 0.25
Nodes (8): 2.3 Domain 3: Review & Risk Engine, `conflict`, `finding`, `finding_evidence`, `human_decision`, `linter_result`, `review_run`, `risk_assessment`

### Community 198 - "End-to-End Flow"
Cohesion: 0.22
Nodes (8): 11 — Feature Flow: AI Chat Assistant, API Endpoints, `ChatMessage`, `ChatSession`, Data Models, Feature Summary, Grounding Rule, Permission Required

### Community 204 - "_setup_test_pr"
Cohesion: 0.43
Nodes (4): _make_validated_finding(), _setup_test_pr(), test_def_03_no_infinite_zombie_duplication_across_runs(), test_def_03_reopened_finding_lifecycle_on_regression()

### Community 205 - "make_client_for_user"
Cohesion: 0.29
Nodes (7): cleanup_overrides(), make_client_for_user(), test_api_circular_dependencies_endpoint(), test_api_flows_endpoint(), test_api_get_latest_analysis(), test_api_rule_governance_lifecycle(), test_api_trigger_analysis_post()

### Community 206 - "`_validate_finding()` — Per-Finding Logic"
Cohesion: 0.40
Nodes (5): Check 1: Diff Verification (Hallucination Detection), Check 2: RAG Chunk Support, Check 3: Linter Confirmation, Evidence Status Assignment, `_validate_finding()` — Per-Finding Logic

### Community 207 - "list_security_findings"
Cohesion: 0.33
Nodes (3): FindingStatusUpdate, SecurityFindingResponse, update_finding_status()

### Community 208 - "RepoMind 2.0 Feature Code Flow Walkthroughs"
Cohesion: 0.29
Nodes (6): 3. RAG Pipeline Flow (Repository Indexing, Chunking, Embedding), 3a. Ingestion Trigger & Job Queue, 3b. Fetch & Chunking, 3c. Embedding & Vector Storage, 4. Chat Assistant Flow (RAG Query Time), RepoMind 2.0 Feature Code Flow Walkthroughs

### Community 210 - "ReviewRunResponse"
Cohesion: 0.25
Nodes (6): ReviewRunResponse, Config, `GET /review-runs/{id}`, `POST /pull-requests/{id}/review`, `POST /review-runs/{id}/approve`, Review Endpoints

### Community 211 - "End-to-End Flow"
Cohesion: 0.29
Nodes (7): 1. Create a Chat Session, 2. Send a Message, 4. Build Evidence + System Prompt, 5. Build User Content with History, 6. Call LLM, 7. Persist Messages, End-to-End Flow

### Community 212 - "03 — Feature Flow: GitHub Repository Connection & Sync"
Cohesion: 0.29
Nodes (6): 03 — Feature Flow: GitHub Repository Connection & Sync, Database Tables Written, Feature Summary, GitHub Client API Calls, Manual Sync / Re-Sync, Security Properties

### Community 213 - "Key Architectural Facts (Quick Reference)"
Cohesion: 0.29
Nodes (7): Auth, GitHub, Key Architectural Facts (Quick Reference), ML, RAG, Review Pipeline, Worker

### Community 214 - "decide_review_run"
Cohesion: 0.33
Nodes (3): evaluate_merge_policy(), decide_review_run(), PART 18 — APPROVAL

### Community 218 - "2.2 Domain 2: GitHub Integration & Pull Requests"
Cohesion: 0.33
Nodes (6): 2.2 Domain 2: GitHub Integration & Pull Requests, `github_connection`, `github_identity` & `github_credential`, PR Detail Subtables, `pull_request`, `repository`

### Community 219 - "2.5 Domain 5: Collaboration & Developer Onboarding"
Cohesion: 0.50
Nodes (4): 2.5 Domain 5: Collaboration & Developer Onboarding, `chat_session` & `chat_message`, `repository_blueprint`, `user_onboarding_progress`

### Community 222 - "PART 1 — EXECUTIVE EXPLANATION"
Cohesion: 0.67
Nodes (3): 2-Minute Engineering Manager Explanation, 30-Second Manager Explanation, PART 1 — EXECUTIVE EXPLANATION

## Knowledge Gaps
- **18 isolated node(s):** `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector`, `Per-User GitHub OAuth`, `Organization` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1730 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **69 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `User` to `github/routes.py`, `Repository`, `test_intelligence_routes.py`, `organizations/service.py`, `RoleEnum`, `PullRequest`, `architecture/routes.py`, `Document`, `test_review.py`, `test_architecture_intelligence.py`, `test_historical_intelligence.py`, `tech_debt/routes.py`, `Onboarding Authorization Tests`, `_get_authorized_repo`, `encrypt_token`, `test_onboarding_service.py`, `github/service.py`, `test_pr_review_engine_upgrade.py`, `auth/routes.py`, `16 — API Endpoint Reference`, `Key Files`, `encrypt_token`, `ChangeImpactAnalysis`, `onboarding/routes.py`, `intelligence/routes.py`, `list_security_findings`, `decide_review_run`, `chat/routes.py`, `onboarding/models.py`, `test_change_impact_analyzer.py`, `ReviewRun`, `RepoMind 2.0 Complete System Architecture`, `onboarding/service.py`, `testing/routes.py`, `Directory Deep Dive`?**
  _High betweenness centrality (0.220) - this node is a cross-community bridge._
- **Are the 86 inferred relationships involving `User` (e.g. with `get_org_analytics()` and `create_architecture_rule()`) actually correct?**
  _`User` has 86 INFERRED edges - model-reasoned connections that need verification._
- **What connects `RepoMind Index`, `Alembic Reset Procedure`, `PostgreSQL pgvector` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.04117063492063492 - nodes in this community are weakly interconnected._
- **Why does `Key Files` connect `chat/routes.py` to `App`, `RoleEnum`, `App.jsx`, `User`, `auth/routes.py`?**
  _High betweenness centrality (0.193) - this node is a cross-community bridge._
- **Are the 47 inferred relationships involving `Repository` (e.g. with `get_organization_analytics()` and `_get_authorized_repo()`) actually correct?**
  _`Repository` has 47 INFERRED edges - model-reasoned connections that need verification._
- **Should `typing` be split into smaller, more focused modules?**
  _Cohesion score 0.03696969696969697 - nodes in this community are weakly interconnected._