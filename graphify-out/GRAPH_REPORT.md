# Graph Report - repo  (2026-11-13)

## Corpus Check
- 291 files · ~149,417 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 11 file(s) not represented in the graph (top: (none) 3, .bat 3, .ini 2)

## Summary
- 1647 nodes · 4962 edges · 128 communities (62 shown, 66 thin omitted)
- Extraction: 88% EXTRACTED · 12% INFERRED · 0% AMBIGUOUS · INFERRED: 609 edges (avg confidence: 0.93)
- Token cost: 152,469 input · 7,531 output

## Community Hubs (Navigation)
- Database Migrations
- Frontend Dependencies
- Database Configuration
- Organization Management
- Automation and Credentials
- LLM Provider Integration
- GitHub Repository Service
- Analytics and Permissions
- Auth Models and Seeding
- Frontend App Layout
- AI Chat Service
- LLM Review Prompts
- Review Run Lifecycle
- Risk and Findings Service
- Review Pipeline Orchestration
- Database Maintenance Scripts
- Conflict Detection Engine
- GitHub API Client
- RAG Embedding and Retrieval
- Risk Assessment Engine
- Review UI Components
- Onboarding Prompt Templates
- RAG Document Storage
- GitHub Webhook Handling
- Authentication Routes
- Codebase Blueprint Service
- Onboarding API Routes
- Review API Schemas
- Schema Extensions
- Evidence Validation Layer
- Team Management UI
- RBAC Authorization Tests
- Organization API Schemas
- Permission Normalization Tests
- Human Review Decisions
- Static Analysis Service
- Onboarding Authorization Tests
- Chat and Mermaid UI
- Ruff Linter Integration
- Analytics Dashboard UI
- GitHub API Operations
- GitHub Integration Tests
- Bandit Linter Integration
- Onboarding Validation Tests
- Text Chunking Service
- OAuth and E2E Tests
- Review Page UI
- Token Encryption Service
- GitHub Data Models
- Document Loading Service
- Finding Persistence Logic
- GitHub Sync Service
- Onboarding Data Models
- User Auth Service
- RAG Data Models
- Review API Tests
- Test Database Setup
- Repository Management UI
- App Entry Point
- Review Comment Tests
- GitHub API Schemas
- Multi-tenant Security Tests
- Technical Documentation
- RBAC Audit Reports
- Review Trigger Endpoint
- Webhook Test Fixtures
- GitHub OAuth Identity
- ML Training Service
- Background Workers
- Merge Policy Logic
- Repository Blueprinting
- Environment Config
- Technical Walkthroughs
- Monitoring and Observability
- Code Connection Map
- Feature Flow Guides
- Analytics Flow
- Authentication Flow
- Background Worker Flow
- AI Chat Flow
- Conflict Detection Flow
- Evidence Validation Flow
- Frontend Application Flow
- GitHub Sync Integration
- Human Approval Gate
- LLM Provider Integration
- ML Prediction Flow
- RAG Indexing Pipeline
- PR Review Pipeline
- Risk Scoring Engine
- Static Analysis Flow
- GitHub Webhook Automation
- Feature Status Matrix
- Database Schema Reference
- Project Architecture Map
- Architecture Documentation Index
- Technical Documentation Guide
- Security Architecture
- System Overview
- E2E Testing Matrix
- Project Index
- Database Migration Reset
- Vector Database Storage
- GitHub OAuth Authentication
- Organization Management
- Organization Creation API
- User Onboarding Flow

## God Nodes (most connected - your core abstractions)
1. `User` - 122 edges
2. `Repository` - 100 edges
3. `PullRequest` - 85 edges
4. `ReviewRun` - 77 edges
5. `Project` - 70 edges
6. `Organization` - 65 edges
7. `RoleEnum` - 59 edges
8. `OrganizationMembership` - 57 edges
9. `GitHubClient` - 52 edges
10. `run_review()` - 51 edges

## Surprising Connections (you probably didn't know these)
- `check_db()` --uses--> `RoleEnum`  [INFERRED]
  check_db_state.py → backend/app/auth/models.py
- `get_or_create_target_user()` --uses--> `RoleEnum`  [INFERRED]
  check_rbac.py → backend/app/auth/models.py
- `repair()` --uses--> `RoleEnum`  [INFERRED]
  repair_role.py → backend/app/auth/models.py
- `run_e2e()` --uses--> `User`  [INFERRED]
  e2e_phase20.py → backend/app/auth/models.py
- `verify()` --uses--> `User`  [INFERRED]
  verify_oauth.py → backend/app/auth/models.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Developer Onboarding Subsystem** — walkthrough_repository_blueprint, walkthrough_user_onboarding_progress, walkthrough_onboarding_service [EXTRACTED 1.00]
- **GitHub OAuth Identity Linking** — repomind_2_0_architecture_flow_github_oauth, backend_app_github_oauth_routes_github_oauth_callback, backend_app_github_oauth_service_upsert_github_identity [EXTRACTED 1.00]
- **RAG Indexing Pipeline** — backend_app_rag_loader, backend_app_rag_chunker, backend_app_rag_embedder, backend_app_rag_repository, postgresql_pgvector [EXTRACTED 1.00]

## Communities (128 total, 66 thin omitted)

### Community 0 - "Database Migrations"
Cohesion: 0.05
Nodes (19): downgrade(), upgrade(), downgrade(), upgrade(), upgrade(), downgrade(), upgrade(), downgrade() (+11 more)

### Community 1 - "Frontend Dependencies"
Cohesion: 0.05
Nodes (49): dependencies, mermaid@^12.3.0, react@^18.2.0, react-diff-viewer-continued@^4.4.0, react-dom@^18.2.0, react-markdown@^10.1.0, react-router-dom@^7.18.3, @tanstack/react-query@^5.102.8 (+41 more)

### Community 2 - "Database Configuration"
Cohesion: 0.08
Nodes (11): run_migrations_offline(), run_migrations_online(), Settings, WebhookEvent, _verify_github_signature(), compute_signature(), test_concurrent_requests_with_same_delivery_id_handled_safely(), test_different_delivery_ids_processed_independently() (+3 more)

### Community 3 - "Organization Management"
Cohesion: 0.10
Nodes (36): AuditLog, hash_invitation_token(), _get_org_id_for_repository(), Team, create_organization(), create_project(), create_repository(), create_team() (+28 more)

### Community 4 - "Automation and Credentials"
Cohesion: 0.12
Nodes (21): get_db(), _get_token_for_identity(), process_automation_actions(), AutomationAction, GitHubCredential, GitHubIdentity, ProjectMergePolicy, reconcile_pull_requests() (+13 more)

### Community 5 - "LLM Provider Integration"
Cohesion: 0.06
Nodes (16): FallbackProvider, GeminiProvider, retry_if_transient_error(), get_llm_provider(), GroqProvider, LLMProvider, LLMProviderError, LocalProvider (+8 more)

### Community 6 - "GitHub Repository Service"
Cohesion: 0.10
Nodes (21): _assert_repo_access(), connect_repository(), get_merge_policy(), get_pull_request(), get_pull_request_commits(), get_pull_request_conflicts(), get_pull_request_events(), get_pull_request_files() (+13 more)

### Community 7 - "Analytics and Permissions"
Cohesion: 0.09
Nodes (15): get_org_analytics(), extract_token_from_request(), get_current_user(), assert_org_permission(), check_org_permission(), _get_current_user_lazy(), get_role_permissions(), Permission (+7 more)

### Community 8 - "Auth Models and Seeding"
Cohesion: 0.15
Nodes (19): Organization, OrganizationMembership, User, bootstrap_system(), hash_password(), reset_database(), seed_database(), test_bootstrap_flow() (+11 more)

### Community 9 - "Frontend App Layout"
Cohesion: 0.12
Nodes (22): App(), ProtectedRoute(), queryClient, AppLayout(), Icons, NavItem(), NavSection(), Sidebar() (+14 more)

### Community 10 - "AI Chat Service"
Cohesion: 0.12
Nodes (15): ChatMessage, ChatSession, ChatMessageRequest, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse, get_chat_history(), list_chat_sessions() (+7 more)

### Community 11 - "LLM Review Prompts"
Cohesion: 0.10
Nodes (18): derive_query_from_diff(), build_user_content(), LLMOutputParseError, parse_llm_output(), ReviewDecisionAction, ReviewOutput, test_derive_query_extracts_paths(), test_derive_query_max_length() (+10 more)

### Community 12 - "Review Run Lifecycle"
Cohesion: 0.12
Nodes (16): ReviewRun, _update_progress(), _setup_repo_and_pr(), test_gap_09_abandoned_job_exceeding_max_retries_fails(), test_gap_09_abandoned_job_with_superseded_sha_transitions_to_superseded(), test_gap_09_active_heartbeat_job_is_not_recovered(), test_gap_09_concurrent_worker_recovery_postgres_skip_locked(), worker_recovery_task() (+8 more)

### Community 13 - "Risk and Findings Service"
Cohesion: 0.14
Nodes (13): get_organization_analytics(), PullRequest, Finding, RiskAssessment, FindingStatusUpdate, list_security_findings(), SecurityFindingResponse, update_finding_status() (+5 more)

### Community 14 - "Review Pipeline Orchestration"
Cohesion: 0.09
Nodes (14): Conflict, _mark_failed(), _persist_conflicts(), _persist_risk(), run_review(), FakeProvider, test_a_valid_output_creates_completed_run(), test_b_malformed_json_both_attempts_fail() (+6 more)

### Community 15 - "Database Maintenance Scripts"
Cohesion: 0.11
Nodes (3): main(), test_invalid_webhook_signature_rejected(), reset_db()

### Community 16 - "Conflict Detection Engine"
Cohesion: 0.14
Nodes (11): _detect_api_contract_conflicts(), _detect_architecture_conflicts(), _detect_configuration_conflicts(), detect_conflicts(), _detect_mechanical_conflicts(), _detect_security_policy_conflicts(), _detect_test_contract_conflicts(), DetectedConflict (+3 more)

### Community 18 - "RAG Embedding and Retrieval"
Cohesion: 0.11
Nodes (10): LocalEmbedder, RAGRetriever, embedder(), test_embedding_dimension(), test_empty_repository(), test_invalid_top_k(), test_relevant_retrieval(), test_repository_isolation() (+2 more)

### Community 19 - "Risk Assessment Engine"
Cohesion: 0.11
Nodes (13): ValidatedFinding, _calculate_blast_radius(), calculate_risk(), _calculate_test_impact(), _generate_summary(), RiskResult, _score_architecture(), _score_change_size() (+5 more)

### Community 20 - "Review UI Components"
Cohesion: 0.14
Nodes (20): ConflictCard(), ConflictList(), EvidenceStatus(), FindingCard(), FindingList(), SEV_ORDER, RiskAssessment(), RiskVector() (+12 more)

### Community 21 - "Onboarding Prompt Templates"
Cohesion: 0.14
Nodes (11): build_onboarding_user_content(), CautionZone, MilestoneItem, ReadingOrderItem, RequestFlowStep, SafeStarterArea, SubsystemItem, TrackPlan (+3 more)

### Community 22 - "RAG Document Storage"
Cohesion: 0.11
Nodes (5): RAGRepository, index_repository(), setup_test_repos(), test_persistence_and_idempotency(), test_service_integration()

### Community 23 - "GitHub Webhook Handling"
Cohesion: 0.13
Nodes (12): _enqueue_review(), github_webhook(), _resolve_repository(), _upsert_pr_from_webhook(), _setup_repo_and_pr(), test_gap_08_completed_historical_runs_are_preserved(), test_gap_08_concurrent_duplicate_webhooks_serialization(), deliver_webhook() (+4 more)

### Community 24 - "Authentication Routes"
Cohesion: 0.21
Nodes (17): bootstrap(), change_password_route(), format_auth_response(), get_me(), login(), logout(), onboard(), set_session_cookie() (+9 more)

### Community 25 - "Codebase Blueprint Service"
Cohesion: 0.14
Nodes (9): RepositoryBlueprintResponse, BlueprintGenerationError, OnboardingService, test_failed_regeneration_preserves_previous_valid_blueprint(), test_generation_and_cache_hit(), test_grounding_rejects_fabricated_request_flow_path(), test_stale_pending_job_recovery(), test_blueprint_reuse_and_invalidation() (+1 more)

### Community 26 - "Onboarding API Routes"
Cohesion: 0.15
Nodes (9): _get_repo_and_verify_access(), get_repository_blueprint(), get_user_onboarding_progress(), refresh_repository_blueprint(), update_user_onboarding_progress(), GenerationInProgressError, GroundingValidationError, OnboardingServiceError (+1 more)

### Community 27 - "Review API Schemas"
Cohesion: 0.08
Nodes (10): FindingResponse, Config, HumanDecisionRequest, HumanDecisionResponse, Config, ReviewRunResponse, Config, ReviewTriggerResponse (+2 more)

### Community 28 - "Schema Extensions"
Cohesion: 0.09
Nodes (6): upgrade(), upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 29 - "Evidence Validation Layer"
Cohesion: 0.14
Nodes (7): _compute_relevance(), _find_linter_confirmation(), _find_supporting_chunks(), validate_findings(), _validate_single_finding(), _verify_file_in_diff(), FindingSchema

### Community 30 - "Team Management UI"
Cohesion: 0.19
Nodes (17): MemberManagement(), fetchMembers(), handleInvite(), handleRemoveConfirmed(), handleUpdateRole(), ROLE_LABELS, ROLES, TeamManagement() (+9 more)

### Community 31 - "RBAC Authorization Tests"
Cohesion: 0.17
Nodes (15): RoleEnum, run_decision_test(), test_approve_developer(), test_approve_org_admin(), test_approve_reviewer(), test_approve_team_lead(), test_reject_developer(), test_reject_org_admin() (+7 more)

### Community 32 - "Organization API Schemas"
Cohesion: 0.17
Nodes (20): GithubConnectionBase, GithubConnectionCreate, GithubConnectionResponse, MemberBase, MemberInvite, MemberRoleUpdate, OrganizationBase, OrganizationCreate (+12 more)

### Community 33 - "Permission Normalization Tests"
Cohesion: 0.10
Nodes (7): test_def_02_action_casing_cannot_bypass_approve_permission(), override_db(), override_user(), test_def_02_arbitrary_unsupported_action_rejected(), test_def_02_lead_approve_normalized_and_triggers_merge_policy(), test_def_02_reject_permission_and_queue_worker(), test_def_06_missing_pull_request_returns_404_no_500()

### Community 34 - "Human Review Decisions"
Cohesion: 0.19
Nodes (9): evaluate_merge_policy(), HumanReview, HumanDecision, decide_review_run(), get_review_run(), get_review_run_decisions(), list_review_runs(), _get_org_id_for_pr() (+1 more)

### Community 35 - "Static Analysis Service"
Cohesion: 0.18
Nodes (8): _persist_failure(), _persist_result(), run_linters(), _safe_join(), LinterResult, _setup_pr(), test_run_linters_fetch_error(), test_run_linters_orchestration()

### Community 36 - "Onboarding Authorization Tests"
Cohesion: 0.22
Nodes (16): cleanup_overrides(), make_client_for_user(), test_10_invalid_track_and_milestone_ids_are_rejected(), test_11_repository_access_enforced_across_all_endpoints(), test_12_active_generation_conflict_returns_409(), test_13_unindexed_repository_error_returns_400(), test_14_responses_do_not_leak_internal_prompts_or_traces(), test_1_authorized_user_can_retrieve_blueprint() (+8 more)

### Community 37 - "Chat and Mermaid UI"
Cohesion: 0.20
Nodes (15): MermaidViewer(), ChatAssistant(), PageLoader(), Spinner(), chatApi, onboardingApi, orgApi, ChatPage() (+7 more)

### Community 38 - "Ruff Linter Integration"
Cohesion: 0.16
Nodes (8): RuffLinter, _extract_linter_issues(), test_empty_linter_findings(), test_malformed_and_unexpected_linter_output(), test_ruff_canonical_schema_with_findings(), test_linter_invalid_json(), test_linter_timeout(), test_ruff_linter_success()

### Community 39 - "Analytics Dashboard UI"
Cohesion: 0.19
Nodes (17): MetricCard(), CardListSkeleton(), DashboardSkeleton(), MetricCardSkeleton(), SidebarSkeleton(), Skeleton(), analyticsApi, AnalyticsPage() (+9 more)

### Community 40 - "GitHub API Operations"
Cohesion: 0.12
Nodes (4): GitHubAPIError, GitHubTransientError, connect_repository(), mock_get_repo_contents()

### Community 41 - "GitHub Integration Tests"
Cohesion: 0.18
Nodes (5): test_connect_unexpected_pat_field(), test_connect_without_oauth_identity_fails(), _setup_user_and_org(), TestPullRequestEndpoints, TestRepositoryConnect

### Community 42 - "Bandit Linter Integration"
Cohesion: 0.14
Nodes (5): BanditLinter, LinterTool, test_bandit_canonical_schema_with_findings(), test_failed_tool_execution_preserves_error_signal(), test_bandit_linter_success()

### Community 43 - "Onboarding Validation Tests"
Cohesion: 0.16
Nodes (8): LLMBlueprintPayload, indexed_test_repo(), sample_valid_llm_json(), test_duplicate_concurrent_generation_prevention(), test_pydantic_schema_invalid_mermaid_fails(), test_pydantic_schema_missing_tracks_fails(), test_pydantic_schema_validation_success(), test_unindexed_repository_raises_error()

### Community 44 - "Text Chunking Service"
Cohesion: 0.18
Nodes (4): GithubConnection, TextChunker, EmbedderError, test_chunker_determinism_and_overlap()

### Community 45 - "OAuth and E2E Tests"
Cohesion: 0.16
Nodes (4): get_auth_token(), test_oauth_routes(), run_test(), test_phase3()

### Community 46 - "Review Page UI"
Cohesion: 0.21
Nodes (11): ActivityLog(), ReviewStateIndicator(), SectionCard(), reviewApi, ApprovalModal(), DetailRow(), ReviewPage(), RiskGauge() (+3 more)

### Community 47 - "Token Encryption Service"
Cohesion: 0.18
Nodes (6): decrypt_token(), encrypt_token(), _get_fernet(), upsert_github_identity(), TestTokenEncryption, verify()

### Community 48 - "GitHub Data Models"
Cohesion: 0.30
Nodes (10): GitHubComment, GitHubRepositoryAccess, GitHubReview, PullRequestCheck, PullRequestCommit, PullRequestEvent, PullRequestFile, WebhookEvent (+2 more)

### Community 49 - "Document Loading Service"
Cohesion: 0.16
Nodes (3): DocumentLoader, test_loader_exclusions(), test_loader_hashing()

### Community 50 - "Finding Persistence Logic"
Cohesion: 0.26
Nodes (6): FindingEvidence, _persist_validated_findings(), _make_validated_finding(), _setup_test_pr(), test_def_03_no_infinite_zombie_duplication_across_runs(), test_def_03_reopened_finding_lifecycle_on_regression()

### Community 51 - "GitHub Sync Service"
Cohesion: 0.23
Nodes (6): get_decrypted_github_token_for_user(), get_github_connection_for_org(), get_github_repositories(), get_pull_request_diff(), get_pull_requests_for_repository(), sync_pull_requests()

### Community 52 - "Onboarding Data Models"
Cohesion: 0.26
Nodes (5): RepositoryBlueprint, UserOnboardingProgress, test_repository_blueprint_creation_and_query(), test_repository_blueprint_uniqueness_per_repository(), test_user_onboarding_progress_creation_and_privacy()

### Community 53 - "User Auth Service"
Cohesion: 0.33
Nodes (6): authenticate_user(), change_password(), decode_access_token(), get_user_by_email(), onboard_user(), verify_password()

### Community 54 - "RAG Data Models"
Cohesion: 0.27
Nodes (4): Document, DocumentChunk, onboarding_repo_fixture(), test_snapshot_hash_changes_on_file_addition_and_removal()

### Community 55 - "Review API Tests"
Cohesion: 0.20
Nodes (6): auth_client(), auth_client2(), test_get_review_run(), test_get_review_run_cross_tenant(), test_trigger_review_creates_pending_job_and_returns_202(), test_trigger_review_duplicate_returns_idempotent()

### Community 56 - "Test Database Setup"
Cohesion: 0.22
Nodes (4): client(), db_session(), setup_test_db(), _verify_test_db_identity()

### Community 57 - "Repository Management UI"
Cohesion: 0.44
Nodes (7): Modal(), githubApi, MergePolicyModal(), Field(), IndexStatusBadge(), RepositoriesPage(), TextInput()

### Community 59 - "Review Comment Tests"
Cohesion: 0.36
Nodes (3): _setup_repo_and_pr(), test_review_comment_does_not_reset_completed_run_and_preserves_metrics(), test_valid_zero_metrics_not_ignored()

### Community 61 - "GitHub API Schemas"
Cohesion: 0.36
Nodes (4): GitHubConnectRequest, PullRequestListResponse, PullRequestResponse, RepositoryConnectResponse

### Community 62 - "Multi-tenant Security Tests"
Cohesion: 0.29
Nodes (4): test_chat_session_creation_rejects_foreign_repository(), test_def_04_cross_tenant_chat_retrieval_prevented(), override_db(), override_user()

### Community 63 - "Technical Documentation"
Cohesion: 0.33
Nodes (6): Testing Strategy, Database Migrations, Deployment Guide, Operational Runbook, Troubleshooting, API Endpoint Reference

### Community 64 - "RBAC Audit Reports"
Cohesion: 0.50
Nodes (4): 4-Role RBAC Model, Feature Parity & Gap Matrix, Final RBAC Parity & Feature Audit Report, Four-Role Permission Matrix

## Knowledge Gaps
- **51 isolated node(s):** `Organization`, `Per-User GitHub OAuth`, `POST /organizations`, `Decision Endpoint`, `Merge Policy` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 611 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **66 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `User` connect `Auth Models and Seeding` to `Database Configuration`, `Organization Management`, `Automation and Credentials`, `GitHub Repository Service`, `Analytics and Permissions`, `AI Chat Service`, `LLM Review Prompts`, `Risk and Findings Service`, `Onboarding Prompt Templates`, `RAG Document Storage`, `Authentication Routes`, `Onboarding API Routes`, `RBAC Authorization Tests`, `Human Review Decisions`, `Onboarding Authorization Tests`, `GitHub Integration Tests`, `Onboarding Validation Tests`, `Text Chunking Service`, `GitHub Data Models`, `Onboarding Data Models`, `User Auth Service`, `RAG Data Models`, `Review API Tests`, `Review Trigger Endpoint`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **Are the 71 inferred relationships involving `User` (e.g. with `get_org_analytics()` and `get_current_user()`) actually correct?**
  _`User` has 71 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Organization`, `Per-User GitHub OAuth`, `POST /organizations` to the rest of the system?**
  _51 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Database Migrations` be split into smaller, more focused modules?**
  _Cohesion score 0.0523532522474881 - nodes in this community are weakly interconnected._
- **Why does `Repository` connect `Automation and Credentials` to `Database Configuration`, `Organization Management`, `Auth Models and Seeding`, `AI Chat Service`, `LLM Review Prompts`, `Review Run Lifecycle`, `Risk and Findings Service`, `Review Pipeline Orchestration`, `Conflict Detection Engine`, `RAG Embedding and Retrieval`, `Onboarding Prompt Templates`, `RAG Document Storage`, `GitHub Webhook Handling`, `Codebase Blueprint Service`, `Onboarding API Routes`, `RBAC Authorization Tests`, `Human Review Decisions`, `Static Analysis Service`, `Onboarding Authorization Tests`, `GitHub API Operations`, `GitHub Integration Tests`, `Onboarding Validation Tests`, `Text Chunking Service`, `GitHub Data Models`, `Finding Persistence Logic`, `GitHub Sync Service`, `Onboarding Data Models`, `RAG Data Models`, `Review API Tests`, `Review Comment Tests`, `Webhook Test Fixtures`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 36 inferred relationships involving `Repository` (e.g. with `get_organization_analytics()` and `list_chat_sessions()`) actually correct?**
  _`Repository` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Should `Frontend Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.05203619909502263 - nodes in this community are weakly interconnected._