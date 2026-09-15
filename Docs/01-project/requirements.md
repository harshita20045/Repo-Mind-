# RepoMind 2.0 — Requirements

**Status: Completed**

## Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| FR-001 | Fetch PR diff and metadata from GitHub via the REST API | Completed |
| FR-002 | Fetch repository documentation for Code-Aware RAG | Completed |
| FR-003 | Chunk and embed repository documentation for retrieval via `pgvector` | Completed |
| FR-004 | Retrieve relevant documentation chunks strictly scoped to the repository | Completed |
| FR-005 | Run Risk Engine to calculate architectural risk and complexity | Completed |
| FR-006 | Run Conflict Engine to detect code/logic overlaps across concurrent PRs | Completed |
| FR-007 | Produce structured LLM review findings using Gemini API | Completed |
| FR-008 | Real-time AI Chat Assistant grounded in Code-Aware RAG | Completed |
| FR-009 | Multi-user authentication with Role-Based Access Control (RBAC) | Completed |
| FR-010 | Organization / Repository hierarchy, with strict data isolation | Completed |
| FR-011 | Human accept / reject / ignore feedback recorded per finding | Completed |
| FR-012 | Background/asynchronous processing for long-running AI jobs | Completed |
| FR-013 | Global Security Browser tracking vulnerabilities across the organization | Completed |
| FR-014 | Developer PR tracking dashboard | Completed |

### Core Mechanics

- **GitHub retrieval:** PR metadata and diffs are fetched via REST API using a read-only PAT.
- **Code-Aware RAG:** Repository documents are embedded and stored in PostgreSQL using `pgvector`. Retrieval is strictly isolated by `repository_id` to prevent cross-organization data leakage.
- **AI Code Review:** The Gemini API is given the diff, retrieved chunks, and linter output to return structured findings.
- **Risk & Conflict Assessment:** Proprietary engines calculate logical complexity and detect cross-PR merge conflicts.
- **Human Approval Gate:** A human always decides whether a PR merges. RepoMind is an advisory gate only.

## Non-Functional Requirements

| ID | Requirement | Status |
|---|---|---|
| NFR-001 | **Security** — secrets are never hardcoded; encrypted at rest. | Completed |
| NFR-002 | **Data isolation** — queries strictly scoped by `organization_id`/`repository_id`. | Completed |
| NFR-003 | **Explainability** — Findings must cite verifiable evidence and source code lines. | Completed |
| NFR-004 | **Performance** — Vite + React SPA architecture provides immediate client-side navigation. | Completed |
| NFR-005 | **No Docker** — Deployment strictly relies on standard Python virtual environments. | Completed |
| NFR-006 | **Fairness / No Scoring** — No entity computes or stores individual developer performance scores. | Completed (Strict Anti-Goal) |

## Tech Stack Requirements
- **Frontend**: React, Vite, TailwindCSS (v3.4.0), TanStack Query
- **Backend**: FastAPI (Python), SQLAlchemy, Alembic
- **Database**: PostgreSQL with `pgvector`
- **LLM**: Google Gemini API (`google-genai`)
