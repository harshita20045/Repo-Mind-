# RepoMind — Database Migrations

**Status: Confirmed**

## SQLAlchemy Model Workflow

Each backend module (`auth`, `organizations`, `github`, `rag`, `review`, `linter`, `ml`, `evaluation`, `feedback`, `audit`) defines its own SQLAlchemy models under its `models.py` (see `04-development/development-guide.md` folder structure). Model changes are the source of truth Alembic migrations are generated/authored against.

## Alembic Workflow

1. Modify the relevant SQLAlchemy model(s).
2. Generate (or hand-author, for anything Alembic's autogenerate handles imprecisely — e.g. the `pgvector` column type) a new migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add finding_feedback table"
   ```
3. Review the generated migration file by hand — autogenerate is a starting point, not a guarantee of correctness, especially for enum types and the `vector` column type used by `document_chunk.embedding`.
4. Test the migration locally:
   ```bash
   alembic upgrade head
   alembic downgrade -1   # confirm it reverses cleanly where practical
   alembic upgrade head
   ```
5. Include the migration file in the same PR as the code that depends on it (see `04-development/git-workflow.md`).

## Migration Creation

New migrations are numbered sequentially, matching the phase-by-phase plan in `03-design/database-design.md` (001 through 010 for the currently-planned schema). A migration should be scoped to one phase's schema needs, not bundled across unrelated features.

## Migration Review

Reviewed as a normal part of PR review — no separate migration-approval process is specified in the source materials. Reviewers should specifically check: correct foreign keys and indexes (see `03-design/database-design.md`), correct enum values, and — for migration 004 specifically — that the `pgvector` extension is enabled (`CREATE EXTENSION IF NOT EXISTS vector;`) before the `document_chunk.embedding` column is created.

## Migration Testing

Covered by the "Integration" test level in `06-testing/testing-strategy.md`: migrations must run cleanly against an empty database as part of CI.

## Applying Migrations

- **Local development:** `alembic upgrade head` (see `04-development/development-guide.md`).
- **Staging/Production:** run as an explicit deployment step, before the new application version starts serving traffic (see `07-deployment/deployment-guide.md`, "Deployment Validation").

## Rollback Strategy

`alembic downgrade` is available for migrations that can be safely reversed. Any migration that is not safely reversible (e.g. one that drops a column with data) must call this out explicitly in the migration's own docstring/comment, so a rollback decision is made deliberately, not automatically assumed safe.

## Production Migration Precautions

- Run migrations during a low-traffic window where practical, given RepoMind's internal-tool usage pattern.
- Because the architecture has a single database and no horizontal scaling of the backend beyond simple process replication, there is no multi-version-compatibility concern to manage during a migration (unlike a system with independently-deployed, differently-versioned service instances) — this simplifies migration safety relative to a microservices architecture, one of the practical benefits of the confirmed modular-monolith decision (see `02-architecture/architecture-decisions.md`, ADR-001).
- The `document_chunk.embedding` (`pgvector`) column and any future vector-index changes should be tested against a realistic chunk volume before applying to production, since index rebuilds on a vector column can be costly at scale — not detailed further in the source materials; flagged here as a **Proposed** operational precaution.
