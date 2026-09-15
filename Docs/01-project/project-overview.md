# RepoMind 2.0 — Project Overview

## What is RepoMind 2.0?

RepoMind 2.0 is an advanced engineering intelligence system. Its core philosophy is strictly defined:
**RepoMind -> PR Review/Risk Engine/AI Assistant -> Engineering Intelligence -> Human Approval Gate.**

It is NOT a generic chatbot, NOT just RAG, NOT just a Code Reviewer, and NOT a developer ranking tool. It retrieves the target repository's own documentation and engineering rules, combines that context with static-analysis results, runs conflict and risk engines, and uses Google's Gemini LLM to produce structured, evidence-backed review findings and allow the developer to interact with an AI Assistant.

## Problem Statement

Generic AI code reviewers give useful, generic recommendations, but they typically don't know a specific repository's own engineering conventions. RepoMind 2.0 solves this by strictly grounding all AI findings and Chat interactions in Code-Aware RAG. If a rule exists in the repository, RepoMind cites it. If it doesn't, RepoMind admits it doesn't know.

## Core Anti-Goals

The following are strictly prohibited in RepoMind 2.0:
1. **Developer Scoring**: Do NOT create Developer quality/risk/performance/ranking scores.
2. **Automated Merging**: A human always decides whether a PR merges. RepoMind is an advisory gate only.
3. **Cross-Organization Data Leakage**: RAG and LLM context must be strictly partitioned by organization and repository.

## Target Users / Intended Usage

RepoMind 2.0 is an internal engineering tool intended for use by a company's development teams. It is organized around an Organization → Repository hierarchy, so multiple teams can connect their own repositories, review their own PRs, and see only their own review history.

Primary users:
- **Developer** — opens PRs as normal; sees RepoMind findings alongside standard GitHub review. Can interact with the AI Chat Assistant.
- **Reviewer** — reviews findings, accepts/rejects/ignores them, still makes the actual merge decision on GitHub.
- **Team Lead / Org Admin** — connects repositories, manages GitHub credentials and org membership. Views global security findings.

## Main Capabilities

- Fetch PR metadata and diffs from GitHub.
- Fetch and index a connected repository's own documentation for Code-Aware RAG using `pgvector`.
- Run Risk and Conflict Engines to detect logical collisions across concurrent PRs.
- Call the Gemini API with the diff, retrieved repository rules, and linter output to produce structured findings.
- Real-time AI Chat Assistant grounded in repository context.
- Global Security Browser for organization-wide vulnerability tracking.
- Re-analyze a PR when new commits are pushed and classify findings as NEW / PERSISTENT / RESOLVED.

## High-Level Workflow

1. An Org Admin connects a GitHub repository via Settings.
2. RepoMind indexes the repository's documentation into PostgreSQL `pgvector`.
3. A user triggers a review for a specific PR.
4. RepoMind fetches the PR diff, retrieves the top relevant repository-rule chunks, runs engines, and calls Gemini.
5. The reviewer sees findings, risk assessments, and conflicts in the Review UI.
6. The developer can chat with the AI Assistant to ask questions about the findings or repository rules.

## Key Technologies

- **Frontend:** Vite + React + TanStack Query + TailwindCSS (v3.4.0) with premium dark-mode glassmorphism.
- **Backend:** FastAPI (Python) + Pydantic.
- **Database:** PostgreSQL with `pgvector` extension natively installed on Windows.
- **ORM / Migrations:** SQLAlchemy + Alembic.
- **LLM:** Google Gemini API (`google-genai`).
- **Infrastructure:** Python Virtual Environments (NO Docker).

## Current Project Status

**Status: Completed.** RepoMind 2.0 has been fully implemented with all frontend views (Dashboard, Repositories, PRs, Security, Settings, Review) and backend routes wired to a live PostgreSQL database and Gemini LLM.
