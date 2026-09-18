# RepoMind 2.0 — Architecture Documentation Index

## Documentation Set

This directory contains the complete feature-by-feature technical architecture documentation for RepoMind 2.0, generated from direct inspection of the source code. No behavior is inferred from documentation alone.

---

## Documents

### System-Level

| Document | File | Contents |
|---|---|---|
| System Overview | [system_overview.md](./system_overview.md) | Architecture diagram, tech stack, directory map, runtime processes |
| API Endpoint Reference | [api_endpoint_reference.md](./api_endpoint_reference.md) | Every registered endpoint, request/response, permissions, notes |
| Database Schema (Model Cheat Sheet) | [model_cheat_sheet.md](./model_cheat_sheet.md) | Every SQLAlchemy model, every column, every table |
| Security Architecture | [security_architecture.md](./security_architecture.md) | All security mechanisms, invariants, and risk matrix |

### Feature Flows (Start-to-End Traces)

| Feature | Document | Key Files Traced |
|---|---|---|
| Authentication & RBAC | [feature_flow_authentication.md](./feature_flow_authentication.md) | `auth/router.py`, `auth/service.py`, `auth/permissions.py`, `usePermissions.js` |
| GitHub Connection & Sync | [feature_flow_github_connection.md](./feature_flow_github_connection.md) | `github/encryption.py`, `github/client.py`, `github/service.py` |
| RAG Indexing | [feature_flow_rag_indexing.md](./feature_flow_rag_indexing.md) | `rag/loader.py`, `rag/chunker.py`, `rag/embedder.py`, `rag/repository.py` |
| PR Review Pipeline (11 stages) | [feature_flow_review_pipeline.md](./feature_flow_review_pipeline.md) | `review/service.py`, `worker/worker.py`, all sub-components |
| Static Analysis (Ruff + Bandit) | [feature_flow_static_analysis.md](./feature_flow_static_analysis.md) | `linter/service.py`, `linter/tools.py` |
| LLM Provider (Groq/Gemini/Fallback) | [feature_flow_llm_provider.md](./feature_flow_llm_provider.md) | `review/provider.py`, `review/prompts.py`, `review/schemas.py` |
| Conflict Detection Engine | [feature_flow_conflict_detection.md](./feature_flow_conflict_detection.md) | `conflicts/engine.py` — 6 detectors |
| Risk Scoring Engine | [feature_flow_risk_scoring.md](./feature_flow_risk_scoring.md) | `risk/engine.py` — 7 weighted factors |
| Evidence Validation | [feature_flow_evidence_validation.md](./feature_flow_evidence_validation.md) | `review/evidence.py` — hallucination mitigation |
| Human Approval Gate | [feature_flow_human_approval.md](./feature_flow_human_approval.md) | `review/router.py` approve endpoint, `HumanDecision` model |
| AI Chat Assistant | [feature_flow_chat_assistant.md](./feature_flow_chat_assistant.md) | `chat/service.py`, `chat/models.py`, RAG integration |
| GitHub Webhook Automation | [feature_flow_webhooks.md](./feature_flow_webhooks.md) | `webhooks/routes.py` — HMAC, deduplication, enqueue |
| Analytics | [feature_flow_analytics.md](./feature_flow_analytics.md) | `analytics/service.py` — 5 aggregation queries |
| Background Worker | [feature_flow_background_worker.md](./feature_flow_background_worker.md) | `worker/worker.py` — SKIP LOCKED, crash recovery, parallel support |
| ML Prediction | [feature_flow_ml_prediction.md](./feature_flow_ml_prediction.md) | `ml/service.py`, `ml/trainer.py` — baseline vs. real ML |
| Frontend Application | [feature_flow_frontend.md](./feature_flow_frontend.md) | `App.jsx`, `lib/api.js`, `usePermissions.js`, all pages |

### Status & Summary

| Document | File | Contents |
|---|---|---|
| Final Feature Status Matrix | [final_feature_status_matrix.md](./final_feature_status_matrix.md) | All features, implementation status, production gaps |

---

## Key Architectural Facts (Quick Reference)

### Auth
- JWT HS256, 12-hour expiry, stored in HttpOnly cookie
- bcrypt 12 rounds for password hashing
- RBAC: 5 roles (developer / reviewer / tech_lead / org_admin + read_only)

### GitHub
- PATs encrypted with Fernet (AES-128-CBC) before DB storage
- httpx client with 30s timeout, Bearer token auth
- PAT decrypted in-process only, never logged, never returned to client

### RAG
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (384 dims, local)
- Chunk size: 256 tokens, 50-token overlap
- Storage: `pgvector` vector(384) column, cosine distance (`<=>` operator)
- Isolation: `repository_id` filter on EVERY vector query

### Review Pipeline
- 11 stages: Setup → Diff → RAG → Linters → Conflicts → LLM → Evidence → Risk → Persist → Complete
- LLM: Groq primary (qwen3), Gemini fallback, via `FallbackProvider`
- Prompt injection defense: system/user content structural separation
- Evidence: RAG + linter + diff cross-validation, confidence adjustment
- Risk: 7 weighted factors, 0-100 score, JSONB breakdown

### Worker
- Polling: PostgreSQL SELECT FOR UPDATE SKIP LOCKED, 5s interval
- No external message broker (no Redis, no Celery)
- Crash recovery: resets stale running/indexing jobs on startup
- Parallel: multiple workers supported via SKIP LOCKED

### ML
- Current: Rule-based baseline (`baseline-v1`), confidence always 0.5
- Future: LinearRegression + RandomForestClassifier (trainer.py exists, not active)
- Requirement: 50+ closed PRs with complete timestamps

---

## Source Code Truth Principles

> "Do not infer behavior merely from documentation."
> "Do not say 'this is handled by the backend' without identifying the exact file, class, function."

All documentation in this directory is grounded in direct source code inspection. Every claim is traceable to a specific file, class, and function.
