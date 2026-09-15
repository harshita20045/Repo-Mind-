# RepoMind — Project Overview


## What is RepoMind?

RepoMind is a repository-aware AI code review system. It takes a GitHub Pull Request (PR), retrieves the target repository's own documentation and engineering rules (README, CONTRIBUTING, ARCHITECTURE, coding standards), identifies the rules relevant to the changed code using Retrieval-Augmented Generation (RAG), combines that context with static-analysis/linter results, and asks an LLM to produce structured, evidence-backed review findings. A separate machine-learning pipeline analyzes historical PR metadata to predict PR cycle time and the probability that a PR will be delayed. An evaluation framework compares three review configurations to measure whether repository-specific context actually improves review quality.

## Problem Statement

Generic AI code reviewers can give useful, generic recommendations, but they typically don't know a specific repository's own engineering conventions. For example, a repository's `ARCHITECTURE.md` might state that "controllers must only handle HTTP concerns; business logic belongs in service classes." A generic LLM may notice that a controller looks overloaded without knowing this is an explicit, documented rule of that repository. RepoMind is designed to produce a more specific, explainable finding that cites the exact rule and its source document.

## Motivation / Core Research Question

The project is not simply an AI demo. Its central purpose is to answer a measurable question:

> **Does repository-specific RAG context improve the quality and groundedness of LLM-based code review, compared with a generic LLM reviewer?**

This is tested by a controlled, three-way comparison (Generic LLM → LLM + Linter → LLM + Linter + RAG), scored against a hand-labeled answer-key test set using precision, recall, F1, false-positive rate, and groundedness.

## Target Users / Intended Usage

RepoMind is an internal engineering tool intended for use by a company's development teams (Scope B — see `implementation-plan.md`). It is organized around an Organization → Project → Repository hierarchy, so multiple teams can each connect their own repositories, review their own PRs, and see only their own review history and repository knowledge base (data isolation is a confirmed requirement — see `05-security/security.md`).

Primary users:
- **Developer** — opens PRs as normal; sees RepoMind findings alongside standard GitHub review.
- **Reviewer** — reviews findings, accepts/rejects/ignores them, still makes the actual merge decision on GitHub.
- **Team Lead** — can trigger evaluation runs, review team/repo-level results.
- **Org Admin** — connects repositories, manages GitHub credentials and org membership.

A human always decides whether a PR merges. RepoMind is advisory only.

## Main Capabilities

- Fetch PR metadata and diffs from GitHub (read-only).
- Fetch and index a connected repository's own documentation for RAG.
- Retrieve the documentation chunks relevant to a specific PR's changed code.
- Run static analysis (linting/security scanning) on changed files.
- Call an LLM with the diff, retrieved repository rules, and linter output to produce structured, categorized findings with citations.
- Predict PR cycle time (regression) and delay probability (classification) from historical PR metadata.
- Record human accept/reject/ignore feedback per finding.
- Run a reproducible three-way evaluation comparing review configurations.
- Re-analyze a PR when new commits are pushed and classify findings as NEW / PERSISTENT / RESOLVED.

## High-Level Workflow

1. An Org Admin connects a GitHub repository (read-only Personal Access Token).
2. RepoMind indexes the repository's documentation (chunk → embed → store).
3. A user triggers a review for a specific PR (MVP: manual trigger from the UI).
4. RepoMind fetches the PR diff, retrieves the top relevant repository-rule chunks (filtered strictly to that repository), runs linters, and calls the LLM.
5. The LLM returns structured findings with category, severity, file/line, evidence, and a recommendation.
6. ML models predict cycle time and delay probability from PR metadata.
7. The reviewer sees findings and predictions in the PR review page and accepts/rejects each finding.
8. New commits can trigger re-analysis; findings are reconciled against the prior run.
9. Periodically, an evaluation run scores the review pipeline against a labeled test set.

The detailed login, repository-onboarding, feedback, and evaluation sequences are documented in `02-architecture/system-architecture.md`.

## Key Technologies

- **Frontend:** React + TypeScript + Tailwind CSS
- **Backend:** FastAPI (Python) + Pydantic
- **ORM / Migrations:** SQLAlchemy + Alembic
- **Database:** PostgreSQL, with the `pgvector` extension used for embedding storage/search in the same database
- **Embeddings:** sentence-transformers (local model, e.g. `all-MiniLM-L6-v2`)
- **LLM:** configurable provider, Claude API as the default
- **Static analysis:** ruff, bandit (Python; language-specific tools selected by file extension)
- **ML:** scikit-learn (Linear Regression / Random Forest / Gradient Boosting for cycle time; Logistic Regression / Random Forest for delay classification)
- **Background processing:** a simple database-backed job table with a polling worker process (no message broker)

See `02-architecture/architecture-decisions.md` for the full rationale behind each choice.

## AI/ML Capabilities

RepoMind combines three distinct AI/ML techniques:
- **Embeddings + semantic retrieval** — grounding review in repository-specific documentation (RAG).
- **LLM reasoning** — generating structured, evidence-backed review findings.
- **Classical ML** — predicting PR cycle time and delay risk from historical metadata.

## GitHub Integration

MVP integration uses a read-only Personal Access Token (PAT) and the GitHub REST API — no GitHub App, OAuth flow, or webhook hosting is required at this stage. See `02-architecture/system-architecture.md` and `05-security/authentication-authorization.md` for details, and `01-project/scope.md` for what is explicitly deferred.

## RAG Capability

Repository documentation is discovered, filtered, chunked (500–800 tokens with 50–100 token overlap), embedded locally with sentence-transformers, and stored in PostgreSQL via `pgvector`, tagged with `repository_id`. Retrieval always filters by `repository_id`, so one repository's rules can never leak into another repository's review. See `02-architecture/diagrams/rag-pipeline.md`.

## Expected Outcomes

- A working internal review tool that produces evidence-backed findings for real PRs.
- A reproducible evaluation table showing whether RAG measurably improves review quality over a generic LLM and over LLM+linter.
- A working cycle-time/delay-risk prediction pipeline, benchmarked against a simple rule-based baseline.
- A persisted feedback loop (accept/reject) that makes the system's quality measurable over time, not just at launch.

## Current Project Status

**Status: Planned / Pre-implementation.** Per the project owner's instruction, this documentation set establishes the authoritative plan; no application code has been generated as part of this documentation task. An earlier, smaller research-prototype scope (Streamlit, file-based storage, no auth) was explored and validated the core RAG/LLM/ML approach; the current, confirmed target for implementation is the larger internal-company scope described throughout these documents (see `01-project/scope.md`, "Conflicts Resolved" section).

## Future Direction

Beyond the current scope, later phases may introduce GitHub Actions-based automatic triggering, a GitHub App with webhooks and inline PR comments, team/repository-level analytics dashboards, and advanced ML (drift detection, retraining pipelines) — all explicitly deferred until a concrete need arises. See `01-project/scope.md` (Future Scope) for the complete list.
