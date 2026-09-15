# RepoMind — Coding Standards

**Status: Confirmed / Proposed** (module-organization and validation principles are Confirmed from the source materials; specific style-guide minutiae not covered by the source materials are marked Proposed)

## Frontend (TypeScript / React)

- **TypeScript** throughout; no implicit `any`.
- **Component organization:** feature-oriented, matching the page/component breakdown in `03-design/ui-design.md` (e.g. `FindingCard`, `RiskPanel`, `ReviewTimeline` as discrete components under the PR review page).
- **State management:** server state via React Query (or equivalent) only; no Redux or other global state library — client/UI state stays local to the component that owns it (see `03-design/ui-design.md`).
- **API calls:** centralized in `frontend/src/lib/` (per the folder structure in `04-development/development-guide.md`), typed against the response shapes in `03-design/api-design.md`.
- **Error handling:** every data-fetching component must handle loading/empty/error states explicitly, per `03-design/ui-design.md` — no silent failures.
- **Type safety:** API response and request types are defined under `frontend/src/types/` and kept in sync with the backend Pydantic schemas.

## Backend (Python / FastAPI)

- **Pydantic models** for all request/response schemas — validation happens at the API boundary, not deep in business logic.
- **SQLAlchemy** for all database access; no raw SQL string-building for application queries (raw SQL is acceptable only within Alembic migrations where appropriate).
- **Module/service organization:** one Python package per backend module (`auth`, `organizations`, `github`, `rag`, `linter`, `review`, `ml`, `evaluation`, `feedback`, `audit`), each exposing `models.py`, `service.py`, `routes.py` (naming per the Implementation Blueprint's task breakdown, Part 25). Dependency direction is strictly one-way (see `02-architecture/system-architecture.md`) — `github` never imports from `rag`/`review`; `evaluation` is a leaf.
- **Validation:** input validation via Pydantic; domain-level validation (e.g. LLM output schema conformance) via a dedicated validator (`FindingValidator`, `OutputParser`) rather than inline checks scattered through the pipeline.
- **Exception handling:** pipeline failures map to the error-handling matrix in `06-testing/testing-strategy.md` — failures are surfaced with a clear status (e.g. job `FAILED`) and logged, never silently swallowed or retried indefinitely.
- **Logging:** structured logs per pipeline stage (fetch, retrieve, lint, LLM call, predict), with timing, per `08-operations/monitoring.md`. No raw source code retained in logs beyond a time-boxed debugging window.
- **Linting:** `ruff` is used both as the product's own static-analysis tool and as the backend codebase's lint tool.

## AI / ML

- **Reproducibility:** every LLM review call and every evaluation run records its prompt version, embedding version, retriever config (top-k), and dataset version (`review_run.prompt_version`, `evaluation_run.config`) — see `03-design/database-design.md`.
- **Prompt versioning:** prompt templates are versioned (`prompt_v1`, etc., per the folder structure `review/prompt_v1.py`); a prompt change is a versioned change, not an in-place edit that silently alters evaluation history.
- **Model versioning:** ML models are serialized to versioned `.pkl` files (`ml_prediction.model_version`); a new training run produces a new version rather than overwriting the previous one.
- **Evaluation discipline:** evaluation runs are triggered manually and kept logically separate from production inference traffic (see `02-architecture/diagrams/ai-review-pipeline.md`) — a prompt/RAG config change must not silently alter what an in-flight evaluation run is measuring.
- **Data leakage prevention (ML):** only PR features knowable at PR-open time are used; the train/test split is chronological, not random (see `02-architecture/diagrams/ml-pipeline.md`). A feature audit is a required task before training (see `02-architecture/architecture-decisions.md`, Risks in the Implementation Blueprint).
- **Deterministic behavior where applicable:** the rule-based baselines (for both delay classification and, where used, cycle-time comparison) must be deterministic and simple enough to serve as a meaningful floor for ML model comparison.
- **Structured LLM output:** the LLM is only ever asked to return the fixed JSON schema in `03-design/api-design.md`; invalid output triggers exactly one retry with a stricter instruction, then a `FAILED` job with the raw output logged (see ADR-011).
- **Prompt injection defense (coding-level):** repository content is passed to the LLM only inside a clearly delimited "untrusted evidence" section of the prompt, never concatenated into or near the system instruction. See `05-security/security.md`.

## General

- No enterprise design patterns (abstract factories, generic plugin frameworks, etc.) are introduced without a concrete, current need — this mirrors the project's explicit "do not over-engineer" constraint (see `01-project/scope.md`).
