# RepoMind — Architecture Decision Record

Each decision below is drawn directly from the provided project materials. Where the materials show an evolution of a decision (research MVP → company blueprint), the company-blueprint decision is recorded as **Confirmed**, and the earlier value is noted under "Superseded Alternative" per the project's "prefer the latest explicit decision" instruction. See `01-project/scope.md` for the full conflict-resolution rationale.

---

### ADR-001 — Modular Monolith Architecture

- **Decision:** Build RepoMind as a modular monolith, evolving to a modular monolith + background worker tier for asynchronous AI processing.
- **Context:** RepoMind has one deploy target, one team, and no component with an independent scaling profile.
- **Options Considered:** single script/monolith, modular monolith, layered architecture, clean/hexagonal architecture, microservices, event-driven, serverless.
- **Chosen Approach:** Modular monolith with clear internal module boundaries; a separate worker process (not a service) for long-running AI calls.
- **Reason:** Microservices add network calls, service discovery, and distributed debugging overhead not justified by any current scaling need. Serverless has cold-start issues for LLM/embedding latency and is awkward for a stateful RAG index.
- **Consequences:** All modules share a runtime; a module can be extracted into a service later if a genuine independent-scaling need appears.
- **Status:** Confirmed

---

### ADR-002 — Frontend: React + TypeScript + Tailwind

- **Decision:** React + TypeScript + Tailwind CSS, 9 routes, no global state library.
- **Context:** A shared, multi-team internal tool needs real navigation across organizations/projects/repositories/PRs, not a single form.
- **Options Considered:** Streamlit (single-page prototype), React, Next.js.
- **Chosen Approach:** React + TypeScript + Tailwind.
- **Reason:** Next.js's SSR/SEO capability is unneeded behind authentication. React Query (or equivalent) covers server-state needs without a global state library.
- **Consequences:** More frontend engineering effort than a single Streamlit page, in exchange for multi-page, multi-team usability.
- **Superseded Alternative:** The research-MVP scope used a single Streamlit page with no routing — sufficient for a solo prototype but insufficient for a shared company tool.
- **Status:** Confirmed

---

### ADR-003 — Backend: FastAPI + Pydantic

- **Decision:** FastAPI with Pydantic for request/response validation.
- **Options Considered:** FastAPI, Django.
- **Chosen Approach:** FastAPI.
- **Reason:** Django's ORM/admin-first design solves problems RepoMind does not have; FastAPI's typing and validation fit an API-first, AI-heavy backend more directly.
- **Status:** Confirmed

---

### ADR-004 — Database: PostgreSQL + SQLAlchemy + Alembic

- **Decision:** PostgreSQL as the relational store, SQLAlchemy as the ORM, Alembic for migrations.
- **Context:** Multiple users writing feedback concurrently, and review history needed for evaluation over time, exceed what file-based storage supports.
- **Options Considered:** JSON/SQLite files, PostgreSQL, MongoDB.
- **Chosen Approach:** PostgreSQL.
- **Reason:** RepoMind's data (orgs, projects, repos, PRs, findings, feedback) is inherently relational.
- **Superseded Alternative:** The research-MVP scope used JSON/flat files with no database — correct for a single developer's test PRs, not for a shared tool.
- **Status:** Confirmed

---

### ADR-005 — Vector Storage: pgvector (not a dedicated vector database)

- **Decision:** Store and query embeddings using the `pgvector` extension inside the primary PostgreSQL instance.
- **Options Considered:** NumPy cosine similarity in-process (research MVP), pgvector, dedicated vector database (Qdrant/Pinecone).
- **Chosen Approach:** pgvector.
- **Reason:** Operational overhead of a separate vector database service is not justified at current chunk volume; pgvector keeps embeddings transactionally consistent with the relational data they're joined against (`repository_id` isolation).
- **Consequences:** If chunk volume grows substantially, a dedicated vector database may be reconsidered (see `01-project/scope.md`, Future Scope) — not a current requirement.
- **Superseded Alternative:** The research MVP used an in-process NumPy array with cosine similarity, sufficient for a few hundred chunks with no concurrent multi-user access.
- **Status:** Confirmed

---

### ADR-006 — Embeddings: sentence-transformers (local)

- **Decision:** Generate document-chunk embeddings locally using sentence-transformers (e.g. `all-MiniLM-L6-v2`).
- **Options Considered:** local sentence-transformers, API-based embeddings.
- **Chosen Approach:** local sentence-transformers.
- **Reason:** Avoids sending repository documentation content to a third-party embeddings API, and avoids a per-call cost.
- **Status:** Confirmed

---

### ADR-007 — Retrieval Mechanism: pgvector Cosine Similarity, Repository-Scoped

- **Decision:** Retrieve the top-k (3–5) most similar chunks via cosine similarity, with a mandatory `repository_id` filter on every query.
- **Context:** Cross-repository leakage of documentation context would undermine both correctness and the project's isolation guarantee.
- **Chosen Approach:** `WHERE repository_id = :id` on every retrieval query, not merely an assumption from separate embedding runs.
- **Reason:** Query-level enforcement is testable and auditable; assumption-based isolation is not.
- **Consequences:** Every retrieval code path must include this filter; this is covered by a dedicated automated test (see `06-testing/test-cases.md`, TC-011).
- **Status:** Confirmed

---

### ADR-008 — GitHub Integration Strategy: PAT + REST API (Phase 1)

- **Decision:** Use a read-only Personal Access Token and the GitHub REST API for the current phase; defer GitHub Actions bridging and a full GitHub App.
- **Options Considered:** PR URL + REST API/PAT, GitHub App (OAuth + webhooks), GitHub Actions workflow bridge.
- **Chosen Approach:** PAT + REST API now; GitHub Actions next; GitHub App deferred (P3).
- **Reason:** A GitHub App buys automation, not AI quality, and the project's central research question (does RAG improve review quality?) can be fully answered without it. The engineering cost (OAuth, webhook hosting, secrets, App-install UX) is not justified before the AI pipeline is proven.
- **Consequences:** No automatic triggering on PR open/update in the current phase; users manually trigger a review.
- **Status:** Confirmed

---

### ADR-009 — PR Input Method: Manual Trigger from the UI (current), not PR URL Free-Text (research MVP)

- **Decision:** In the company scope, a PR is selected/triggered from within the connected-repository UI (`POST /pull-requests/{id}/review`) rather than a free-text PR URL paste box.
- **Context:** The research MVP used a Streamlit text box for a PR URL; the company scope has a Repository → Pull Request hierarchy already modeled in the database and UI.
- **Chosen Approach:** Trigger review from the PR detail page in the app.
- **Reason:** Once PRs are already fetched and listed per repository, re-parsing a pasted URL is redundant.
- **Superseded Alternative:** The research MVP's PR-URL-paste flow (`github/parser.py` extracting owner/repo/PR number from a pasted URL) — this parsing logic is still useful internally for the initial GitHub Actions bridge step (future).
- **Status:** Confirmed

---

### ADR-010 — Separation of AI, Integration, and Business Logic

- **Decision:** Enforce a strict, one-way module dependency direction: `github` (pure adapter, zero AI dependencies) → `rag`/`linter` → `review` → `evaluation` (leaf, nothing depends on it).
- **Reason:** Keeps the GitHub adapter testable in isolation and keeps evaluation logic from silently affecting production inference behavior.
- **Status:** Confirmed

---

### ADR-011 — Structured LLM Output with Schema Validation

- **Decision:** The LLM must return only a JSON array/object of findings conforming to a fixed schema (severity, category, file, line, title, problem, evidence, repository_rule, recommendation, confidence). Invalid JSON is retried once with a stricter instruction; if still invalid, the review job is marked `FAILED` with the raw output logged, never silently dropped.
- **Reason:** Structured, validated output is required to reliably display findings, score them against an answer key, and detect hallucinated/unsupported findings.
- **Status:** Confirmed

---

### ADR-012 — ML Prediction Architecture: Classical ML, Chronological Split, Versioned Models

- **Decision:** Use scikit-learn models (Linear Regression → Random Forest → Gradient Boosting for cycle-time regression; Logistic Regression → Random Forest for delay classification), trained on a chronological (not random) train/test split, using only features knowable at PR-open time. Models are serialized to versioned `.pkl` files and loaded for fast synchronous inference.
- **Reason:** Chronological splitting and open-time-only features prevent temporal/data leakage that would invalidate the evaluation. A rule-based baseline is required for comparison in both tasks.
- **Status:** Confirmed

---

### ADR-013 — Background Jobs: DB Table + Polling Worker (not Celery/Redis)

- **Decision:** Use a `job` database table with status enum (`pending`/`running`/`completed`/`failed`/`cancelled`) and a polling worker process, instead of Celery + Redis.
- **Reason:** Redis+broker overhead is not justified at the current internal job volume.
- **Consequences:** May be revisited (Celery/RQ) only if job volume grows substantially — a future, not current, decision.
- **Status:** Confirmed

---

### ADR-014 — No Docker (Explicit Project Exclusion)

- **Decision:** Docker and Docker Compose are excluded from this project's documentation, local development setup, and deployment instructions, despite being recommended in the Architecture Blueprint and Implementation Blueprint source materials.
- **Context:** This is a direct, explicit instruction from the project owner, overriding the source materials' own recommendation.
- **Chosen Approach:** Native development and deployment: Python virtual environment for the backend/worker, Node.js/npm for the frontend, a natively-installed PostgreSQL instance with the `pgvector` extension enabled.
- **Reason:** Explicit project-owner requirement; not derived from a technical argument in the source materials.
- **Status:** Confirmed (project-owner override — see `07-deployment/deployment-guide.md`)

---

### ADR-015 — Authentication and Roles

- **Decision:** Session-based authentication with 4 roles (`developer`, `reviewer`, `team_lead`, `org_admin`).
- **Options Considered:** no auth (research MVP, sufficient for one local developer), session-based auth with roles, full enterprise SSO/RBAC.
- **Chosen Approach:** Session-based auth, 4 roles.
- **Reason:** A shared company tool must know who is submitting feedback and must scope org-admin actions (connecting repos, managing membership) — a single developer running it locally did not need this.
- **Superseded Alternative:** Research MVP explicitly recommended 0 RepoMind-specific roles, relying on GitHub's own author/reviewer/admin roles.
- **Status:** Confirmed

---

### Open Decisions

- **LLM provider configuration details** (which providers are supported beyond the Claude API default, and how provider selection is exposed in configuration) are described only at a high level ("configurable provider") in the source materials. Exact provider abstraction is an **Open Decision**.
- **Local/self-hosted LLM option** for private-repo policy compliance is mentioned as a future possibility, not a committed current design. **Open Decision / Future.**
- **Managed vs. self-managed PostgreSQL** in production is explicitly left open ("managed PostgreSQL optional once uptime matters more than cost"). **Open Decision.**
- **Exact deployment host / process manager** for the native (non-Docker) setup is not specified in the source materials beyond "single small VM" and is filled in as a reasonable assumption in `07-deployment/deployment-guide.md`. **Proposed**, not confirmed by source materials.
