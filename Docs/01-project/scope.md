# RepoMind — Scope

**Status: Confirmed**

## Conflicts Resolved — Which Scope Is "Current"

The provided project materials describe RepoMind at three different points of evolution:

1. **AI Research MVP** (`RepoMind_End_to_End_Guide.md`, most of `RepoMind_PROJECT.md`): Streamlit UI, JSON/file storage, no auth, no database, single developer usage. This validated the core RAG/LLM/ML approach.
2. **Team-workflow critique** (`RepoMind_Team_Workflow_Analysis.md`): largely confirms and lightly extends the Research MVP (adds the accept/reject feedback record), explicitly recommends *not* building auth, roles, or a database yet.
3. **Company Implementation Blueprint** (`RepoMind_Implementation_Blueprint.md`): explicitly and deliberately supersedes decisions 1 and 2 for a shared, multi-team company deployment — adding authentication, an Organization/Project/Repository hierarchy, PostgreSQL + pgvector, a React frontend, and background workers, "because a shared internal tool has different requirements than a solo research prototype."

Per the instruction to **prefer the latest explicit decision when materials conflict**, this documentation set treats the **Company Implementation Blueprint's scope ("Scope B — Internal Company MVP") as the current, confirmed target** for the sections describing architecture, database, API, frontend, security, testing, and deployment. The Research MVP's AI logic (RAG pipeline, prompt design, evaluation methodology, ML approach) is **not discarded** — it ports directly into the corresponding modules of the company scope, as the Implementation Blueprint itself states.

One additional override applies throughout this documentation regardless of source-material recommendations: **Docker is explicitly excluded from this project** per direct project-owner instruction, even though the Implementation Blueprint recommends Docker Compose for deployment. All setup and deployment documentation in this project uses native (non-Docker) tooling. See `07-deployment/deployment-guide.md`.

## In Scope (Current Phase — Scope B, Internal Company MVP)

- Organization → Project → Repository data hierarchy.
- Session-based multi-user authentication with 4 roles: `developer`, `reviewer`, `team_lead`, `org_admin`.
- GitHub repository connection via a read-only Personal Access Token (PAT) and the GitHub REST API.
- Repository documentation indexing: discovery, filtering, chunking, embedding (sentence-transformers), and storage in PostgreSQL via `pgvector`, scoped per repository.
- PR review pipeline: diff fetch → repository-scoped RAG retrieval → static analysis (ruff/bandit) → LLM review → schema-validated structured findings.
- Manual review trigger (paste/select a PR) creating an asynchronous background job.
- Background job processing via a database-backed job table and a polling worker process.
- Re-analysis of a PR on new commits, with NEW / PERSISTENT / RESOLVED finding reconciliation.
- Human accept / reject / ignore feedback per finding, persisted per user.
- ML pipeline: PR cycle-time regression and delay-probability classification, each benchmarked against a rule-based baseline, trained on historical PR metadata with leakage-safe, chronologically-split features.
- Evaluation framework: manually-triggered, reproducible 3-way comparison (generic LLM / LLM+linter / LLM+linter+RAG), scored with precision, recall, F1, false-positive rate, and groundedness against a labeled answer-key test set.
- React + TypeScript frontend, 9 pages (see `03-design/ui-design.md`).
- FastAPI backend, modular monolith, PostgreSQL + pgvector.
- Basic security hardening: encrypted-at-rest secrets, audit logging of sensitive actions, prompt-injection defenses, repository isolation guarantees.
- Native (non-Docker) local development and deployment.

## Out of Scope (Current Phase)

- GitHub App, OAuth install flow, and webhooks (automatic triggering).
- Inline PR review comments posted back to GitHub.
- Team/repository-level analytics dashboards.
- Enterprise SSO.
- Advanced RBAC beyond the 4 defined roles.
- A dedicated vector database service (e.g. Qdrant/Pinecone) — `pgvector` inside the existing PostgreSQL instance is the confirmed choice.
- Redis, Celery, or any message broker — the background job tier is a simple database table with a polling worker.
- Kubernetes or any container-orchestration platform.
- Docker or Docker Compose, in any form, for local development or deployment (explicit project-owner exclusion — see "Conflicts Resolved" above).
- Microservices decomposition of any kind.
- Individual developer performance scoring, ranking, or a `developer_score` entity — deliberately absent from the data model, not merely unbuilt (see `01-project/requirements.md`, NFR-010).
- Slack/Teams or other chat-platform integrations.
- Fine-tuning or self-hosting an LLM (a configurable-provider LLM client with Claude API as default is in scope; self-hosting is a documented future option, not a current requirement).
- Full APM/distributed-tracing observability stack.
- High availability / multi-region deployment.

## Future Scope

The following are explicitly identified in the source materials as planned or reasonably anticipated future work, **not** current requirements:

- **GitHub Actions bridge** (Phase 2 of GitHub integration): a workflow file that calls RepoMind's API on `pull_request` events — lighter-weight automation than a full GitHub App, considered the next automation step after the internal MVP is proven.
- **GitHub App + webhooks** (Phase 3, P3): full automatic triggering and inline PR comments, reserved for the point where cross-repo, centrally-managed inline comments become an actual, requested production need.
- **Team/repository-level analytics** (P2): trend views only, explicitly never individual ranking; to be built last, and only on a real, specific request.
- **Vector search evolution**: move from `pgvector` to a dedicated vector database only if chunk volume growth genuinely justifies the operational overhead.
- **Background jobs evolution**: move from the polling job table to Celery/RQ only if job volume grows substantially.
- **Advanced ML**: drift detection and retraining pipelines.
- **Enterprise SSO** and advanced RBAC, if/when multiple external organizations or stricter compliance needs arise.
- **Local/self-hosted LLM option**, for organizations where sending private code to a third-party LLM API is not acceptable.
- **Managed PostgreSQL / higher-availability database**, once uptime requirements exceed what a single-instance database provides.

## MVP vs. Production Boundary

| Aspect | Current Phase (Scope B) | Future / Production |
|---|---|---|
| GitHub trigger | Manual, PAT-based | GitHub Actions → GitHub App + webhooks |
| Findings delivery | In-app review page | PR summary comment → inline PR comments |
| Auth | Session-based, 4 roles | + Enterprise SSO, advanced RBAC |
| Vector storage | pgvector in the primary PostgreSQL instance | Dedicated vector DB, only if scale demands |
| Background jobs | DB job table + polling worker | Celery/RQ, only if job volume demands |
| Analytics | None | Team/repo trend dashboard (P2) |
| Deployment | Native process management, single host | TBD — still no Docker/Kubernetes assumed unless a future decision changes this |
