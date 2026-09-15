# RepoMind — Requirements

**Status: Confirmed** (unless individually marked otherwise)

Requirement IDs below follow the source materials' own numbering where an explicit ID existed (`R-xx`), and are additionally given `FR-xxx`/`NFR-xxx` IDs for structure. Priorities (P0/P1/P2/P3) and MVP flags are preserved from the source materials.

## Functional Requirements

| ID | Requirement | Priority | MVP (current phase)? | Depends on |
|---|---|---|---|---|
| FR-001 (R-01) | Fetch PR diff and metadata from GitHub via the REST API | P0 | Yes | — |
| FR-002 (R-02) | Fetch repository documentation (README, CONTRIBUTING, ARCHITECTURE, coding-standards docs, etc.) | P0 | Yes | FR-001 |
| FR-003 (R-03) | Chunk and embed repository documentation for retrieval | P0 | Yes | FR-002 |
| FR-004 (R-04) | Retrieve the top-k relevant documentation chunks for a given PR, strictly scoped to that PR's repository | P0 | Yes | FR-003 |
| FR-005 (R-05) | Run static analysis (linting, security scanning) on changed files | P0 | Yes | — |
| FR-006 (R-06) | Produce structured LLM review findings from diff + retrieved context + linter output | P0 | Yes | FR-004, FR-005 |
| FR-007 (R-07) | Validate LLM output against a fixed JSON schema; retry once on invalid output, then fail the job | P0 | Yes | FR-006 |
| FR-008 (R-08) | Predict PR cycle time via a regression model | P0 | Yes | Historical PR data |
| FR-009 (R-09) | Predict PR delay probability via a classification model | P0 | Yes | Historical PR data |
| FR-010 (R-10) | Provide rule-based baselines for both ML tasks, to compare ML performance against | P0 | Yes | FR-008, FR-009 |
| FR-011 (R-11) | Run and score a generic-LLM / LLM+linter / LLM+linter+RAG comparison | P0 | Yes | FR-006 |
| FR-012 (R-12) | Persist review history (not just the latest run) | P1 — new for company scope | Yes | Database |
| FR-013 (R-13) | Multi-user authentication | P1 — new for company scope | Yes | Database |
| FR-014 (R-14) | Organization / Project / Repository hierarchy, with data scoped to it | P1 — new for company scope | Yes | FR-013 |
| FR-015 (R-15) | Human accept / reject / ignore feedback recorded per finding | P0 | Yes | FR-006 |
| FR-016 (R-16) | Background/asynchronous processing for slow AI review jobs | P1 — new for company scope | Yes | Database |
| FR-017 (R-17) | Re-analysis of a PR on new commits, with findings reconciled as NEW / PERSISTENT / RESOLVED | P1 | Yes | FR-006, FR-012 |
| FR-018 (R-18) | GitHub App / webhooks / automatic trigger on PR events | P3 | **No — deferred** | — |
| FR-019 (R-19) | Inline PR review comments posted back to GitHub | P3 | **No — deferred** | FR-018 |
| FR-020 (R-20) | Team/repository-level analytics (never individual developer ranking) | P2 | **No — deferred, build last, only on explicit request** | FR-012 |
| FR-021 (R-21) | Enterprise SSO | P3 | **No — deferred** | — |

### Functional Requirement Detail — Confirmed Core Pipeline

- **GitHub retrieval:** PR metadata (title, author, timestamps, state, additions/deletions, files changed), the PR diff, and repository documentation are fetched read-only via the GitHub REST API using a Personal Access Token. No developer manual re-entry of information GitHub already tracks.
- **Repository-aware RAG:** repository documents are discovered, filtered (documentation files only; generated/vendor directories excluded), chunked, embedded, and stored per repository. Retrieval is always filtered by `repository_id` — this is a hard, tested requirement (see FR-011a below and `06-testing/test-cases.md`, TC-011).
- **AI code review:** the LLM is given the diff, the retrieved chunks (with source tags), and linter output, and asked to return only a JSON array of findings. Findings not grounded in retrieved context or linter output must not be invented.
- **Finding categories (Confirmed):** `bug`, `security`, `missing_test`, `standards_violation`, `maintainability`. The `standards_violation` category is the one most dependent on repository-specific retrieval and is treated as the demonstration case for the project's core value proposition.
- **Historical PR analysis / ML predictions:** cycle time (regression) and delay probability (classification), computed from PR metadata features knowable at PR-open time only (no leakage from post-open data such as `merged_at` or final review counts).
- **Evaluation framework:** a reproducible, manually-triggered comparison of the three review configurations against a hand-labeled answer-key test set, and a comparison of ML models against rule-based baselines.
- **Review feedback:** every displayed finding has an accept/reject/ignore action; each decision is persisted with user, timestamp, and (optionally) a reason.

### FR-011a — Repository Isolation (Confirmed, elevated to explicit requirement)

Given two connected repositories with different documented rules, a review of a PR in one repository must never retrieve or cite documentation chunks from the other. This is enforced at the query level (a `repository_id` filter on every retrieval query, not merely an assumption from separate embedding runs) and is covered by a dedicated automated test (see `06-testing/test-cases.md`, TC-011).

## Non-Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| NFR-001 | **Security** — secrets (GitHub PAT, LLM API keys) are never hardcoded or committed; encrypted at rest per organization; never logged. | Confirmed |
| NFR-002 | **Data isolation** — all queries are scoped by `organization_id`/`repository_id` derived from the authenticated session, never trusted from client input; repository documentation chunks are isolated per repository. | Confirmed |
| NFR-003 | **Explainability / groundedness** — every `standards_violation` finding must cite a specific source and quoted rule; findings without verifiable evidence are visually flagged as "unverified citation" rather than silently trusted. | Confirmed |
| NFR-004 | **Reproducibility** — every evaluation run records its variant config, dataset version, prompt version, embedding version, and retriever config, so results can be reproduced. | Confirmed |
| NFR-005 | **Reliability** — transient GitHub/LLM failures are retried once with backoff; failures are surfaced clearly, never silently dropped or retried indefinitely. | Confirmed |
| NFR-006 | **Maintainability** — one-way module dependency direction (e.g. `github` never imports from `rag`/`review`; `evaluation` is a leaf module); no framework-level abstraction layers not justified by current size. | Confirmed |
| NFR-007 | **Scalability** — architecture is a modular monolith with a background worker tier for slow AI calls; no independent-scaling component is introduced without a concrete, present need. | Confirmed |
| NFR-008 | **Observability** — structured logs per pipeline stage (fetch, retrieve, lint, LLM call, predict) with timing; LLM token/cost tracking; job status history. No full APM/tracing stack introduced without a specific requirement. | Confirmed |
| NFR-009 | **Performance** — ML inference is synchronous and fast (<100ms, loaded from serialized `.pkl` models); AI review jobs run asynchronously so they never block the API. | Confirmed |
| NFR-010 | **Fairness / no individual scoring** — no entity or feature in the system computes or stores an individual developer performance score; team/repo-level analytics are the only aggregate view, and only once requested. | Confirmed (explicit constraint, not merely deferred) |

## Requirements Explicitly Not Invented

The following were considered in earlier drafts of the source materials but are **not** included as current requirements, per the "do not invent" instruction and the confirmed scope boundary: Redis/caching, a message broker (Kafka/RabbitMQ/Celery), Kubernetes, a dedicated vector database service, complex RBAC beyond the 4 defined roles, employee/individual performance scoring, chat/notification systems, and Docker-based deployment (see `01-project/scope.md` for the full Out-of-Scope list and the Docker exclusion rationale).
