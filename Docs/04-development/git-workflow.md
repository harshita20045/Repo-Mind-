# RepoMind — Git Workflow

**Status: Proposed** (the source materials describe CI/CD checks and migration/prompt discipline in detail but do not specify a branch-naming or commit-message convention; a conventional, low-complexity workflow is proposed below, consistent with the project's "do not invent unnecessary complexity" instruction)

## Branch Strategy

- `main` is always deployable.
- Feature work happens on short-lived branches off `main`, one branch per phase/task (matching the `REPOMIND-0XX` task IDs in `01-project/implementation-plan.md`, e.g. `repomind-008-embedding-retrieval-isolation`).
- No long-lived `develop` branch or complex GitFlow — the project's own architecture explicitly avoids unnecessary process complexity, and a single mainline branch matches the "one team, one deploy" reality described in `02-architecture/architecture-decisions.md`.

## Commit Conventions

- Commits reference the task ID where applicable (e.g. `REPOMIND-008: add repository isolation test for retriever`).
- Not otherwise specified in the source materials; standard, descriptive commit messages are sufficient — no enforced conventional-commits tooling is described as a requirement.

## Pull Requests and Code Review

- Every change to RepoMind itself goes through a GitHub PR (RepoMind is, fittingly, expected to eventually review its own PRs once the pipeline is stable — this is a natural dogfooding opportunity, not a formal requirement in the source materials).

## Merge Strategy

- Not specified beyond "CI must pass." Squash-merge to keep `main` history aligned with one task/PR per commit is a reasonable, low-complexity default — **Proposed**, not confirmed by the source materials.

## Release / Versioning Approach


## Handling Database Migrations

- Every schema change ships with an Alembic migration in the same PR as the code that depends on it (see `07-deployment/database-migrations.md`).
- Migrations are numbered sequentially (see the migration plan in `03-design/database-design.md`) and are reviewed as part of the normal PR process — no separate migration-approval process is described in the source materials.

## Handling AI Prompt / Model Changes

- ML model retraining produces a new versioned `.pkl` artifact (see `04-development/coding-standards.md`); the training script itself goes through normal PR review, and the resulting model version is compared against the previous version's baseline metrics before being adopted (see `02-architecture/diagrams/ml-pipeline.md`).
