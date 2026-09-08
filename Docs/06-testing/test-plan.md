# RepoMind — Test Plan

**Status: Confirmed**

Organized by the same categories as `06-testing/testing-strategy.md`. Each item below states objective, prerequisites, test environment, test type, expected result, and priority.

## Component-Level

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| Chunker produces correctly-sized chunks | Sample repository docs (README + ARCHITECTURE.md) | Local, backend venv | Unit | Chunks are 500–800 tokens with 50–100 token overlap, tagged with `repository_id` | P0 |
| GitHub PR-URL/diff parser extracts owner/repo/PR number correctly | Sample PR URLs | Local | Unit | Correct owner/repo/number extracted; malformed URLs raise a clear error | P0 |
| LLM output parser handles valid/invalid/missing-field JSON | Sample LLM responses (valid, malformed, partial) | Local | Unit | Valid parsed into `Finding` objects; invalid triggers the retry-then-fail path | P0 |
| ML feature engineering produces correct feature rows | Sample historical PR metadata | Local | Unit | Feature values match expected calculations; no post-open-time fields present | P0 |

## Feature-Level

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| Repository connection flow | Valid read-only PAT, test repository | Staging/local with real GitHub | Integration | `POST /repositories/connect` validates the token and queues an indexing job | P0 |
| Repository indexing completes | Connected repository | Staging/local | Integration | `repository.index_status` becomes `ready`; `document`/`document_chunk` rows created | P0 |
| PR review end-to-end | Indexed repository, real test PR | Staging/local | Integration | Review job completes; findings visible with citations | P0 |
| Feedback persistence | A displayed finding | Staging/local | Integration | Accept/reject persists a `finding_feedback` row and updates UI without reload | P0 |
| Re-analysis reconciliation | A PR already reviewed once, then a new commit pushed | Staging/local | Integration | New review run's findings classified NEW/PERSISTENT/RESOLVED against the prior run | P1 |

## Integration-Level

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| GitHub client against a real repo | Valid PAT, public test repository | Local/staging | Integration | `fetch_pr(number)` returns diff + metadata matching GitHub's UI | P0 |
| RAG retrieval end-to-end | Indexed repository | Local/staging | Integration | Known query returns the expected chunk(s) | P0 |
| Database migrations | Empty database | Local/CI | Integration | `alembic upgrade head` runs cleanly | P0 |

## System-Level

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| Full user journey | Seeded demo org/project/repo | Staging | E2E | Login → project → repo → PR → review → feedback → re-analysis all succeed | P1 |
| Job failure surfaces correctly | Simulated GitHub 5xx / LLM timeout | Local/staging | System | Job marked FAILED with a clear, user-visible message; no silent failure | P0 |

## AI / RAG

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| AI evaluation regression | Labeled answer-key test set | CI | Regression | Precision/recall/F1/false-positive-rate/groundedness do not regress vs. baseline | **P0 — most important suite** |
| Repository isolation | Two connected repositories (A, B) with different docs | CI/Integration | Isolation | Repo A's chunks never retrieved for repo B's PR (automated assertion, not manual inspection) | P0 |
| Prompt injection resistance | A test PR whose diff/docs embed a fake instruction | CI/Integration | Security | LLM does not comply with the embedded instruction | P0 |
| Groundedness of standards_violation findings | Test PR with a known documented rule violation | CI/Integration | AI quality | Finding cites the exact rule/source; cited text verified to appear in retrieved context | P0 |

## ML

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| Chronological split enforced | Historical PR dataset | CI | Unit/Integration | Test set contains only PRs later in time than the training set | P0 |
| No data leakage | Feature list audit | CI | Unit | No feature uses information unavailable at PR-open time (e.g. no `merged_at`) | P0 |
| Baseline vs. model comparison | Trained models + rule-based baseline | CI/Local | Evaluation | Comparison table (MAE/RMSE for regression; Precision/Recall/F1/ROC-AUC for classification) produced | P0 |

## Security

| Objective | Prerequisites | Environment | Type | Expected Result | Priority |
|---|---|---|---|---|---|
| Authorization boundary enforcement | Users with different roles | CI/Integration | Security | A `developer` cannot call `org_admin`-only endpoints; org-scoped data cannot be accessed cross-org | P0 |
| Secret handling | `.env.example` and CI config | CI | Static check | No real secret values present in source control | P0 |

See `06-testing/test-cases.md` for concrete, numbered test cases (`TC-xxx`) derived from this plan.
