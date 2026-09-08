# RepoMind — Testing Strategy

**Status: Confirmed** (per the Implementation Blueprint, Part 20)

## Testing Pyramid

| Level | Covers | Priority |
|---|---|---|
| Unit | Chunker, GitHub parser, output parser, feature engineering | P0 |
| Integration | GitHub client against a real test repo, RAG retrieval end-to-end, DB migrations | P0 |
| API | Every endpoint in `03-design/api-design.md`, auth/authz enforcement | P0 |
| **AI evaluation regression** | Run the labeled answer-key test set through the pipeline on every change to prompt/RAG config; assert metrics don't regress | **P0 — the most important suite** |
| RAG isolation | Explicit test that repository A's docs are never retrieved for repository B's PR | P0 |
| Prompt injection | A test PR whose diff/docs contain an embedded fake instruction ("ignore previous instructions...") — assert the LLM does not comply | P0 |
| Frontend | Component rendering, PR page states (loading/empty/error) | P1 |
| E2E | Login → project → repo → PR → review → feedback → re-analysis | P1 |

This is intentionally weighted toward the AI-specific suites (evaluation regression, isolation, prompt injection) rather than a conventional unit-heavy pyramid alone — these are the suites that actually validate RepoMind's core value proposition and its most important safety guarantee.

## Frontend Unit Tests

Component rendering and state-handling tests for the PR review page's loading/empty/error states (see `03-design/ui-design.md`).

## Backend Unit Tests

Chunker (correct chunk sizes and overlap), GitHub PR-URL/diff parser, LLM output parser (valid/invalid/missing-field cases), ML feature-engineering functions.

## Integration Tests

- GitHub client against a real (or realistic mocked) test repository.
- RAG retrieval end-to-end (chunk → embed → store → retrieve).
- Database migrations run cleanly against an empty database.

## API Tests

Every endpoint listed in `03-design/api-design.md`, including authorization enforcement per the role table in `05-security/authentication-authorization.md` (e.g. a `developer` cannot call `POST /repositories/connect`).

## AI Tests

The AI-evaluation regression suite (below) plus unit tests for prompt construction, JSON-schema validation, and retry-once-then-fail behavior on invalid LLM output.

## RAG Tests

`test_retriever.py` (a known query returns the correct chunk) and `test_repository_isolation.py` — this isolation test must exist and must fail loudly if isolation ever breaks; it is explicitly called out as a required test, not an optional nice-to-have (see `01-project/requirements.md`, FR-011a).

## ML Tests

Feature-engineering correctness, chronological-split enforcement (no leakage), and baseline-vs-model comparison correctness.

## GitHub Integration Tests

Mocked-API unit tests plus one live integration test against a public repository, per the Implementation Blueprint's task template (`REPOMIND-006`).

## End-to-End Tests

Login → project → repository → PR → review → feedback → re-analysis, exercising the full stack.

## Security Tests

Prompt-injection test (above) and authorization-boundary tests confirming that org/repository scoping cannot be bypassed via client-supplied parameters (see `05-security/security.md`).

## AI Evaluation Regression Suite (Detail)

This is the **single most important test suite** in the project, because it operationalizes the project's central research question as a CI gate:

- Runs the labeled answer-key test set (see `06-testing/test-plan.md`) through the pipeline on every prompt or RAG-config change.
- Asserts precision/recall/F1/false-positive-rate/groundedness do not regress versus the previously recorded baseline.
- Runs as part of CI before merge (see `04-development/git-workflow.md`).

## Error Handling Matrix

| Failure | Detection | User Experience | Retry? | Logging |
|---|---|---|---|---|
| GitHub unavailable / rate limit | HTTP status | Job fails with a clear message, retry button | Once, backoff | Yes |
| Repository not accessible (bad PAT scope) | 403/404 on fetch | "Check repository permissions" message | No | Yes |
| PR too large | Pre-check diff size | Per-file review, report notes "reviewed in parts" | N/A | Yes |
| Embedding failure | Exception in embed step | Review proceeds without RAG, findings tagged "no repo context available" | Once | Yes |
| LLM timeout | Timeout exception | Job fails, retry button shown | Once | Yes |
| LLM invalid JSON | Schema validation fails | Retry once, then job fails with raw output logged | Once | Yes |
| Linter failure | Non-zero exit unexpected | Review proceeds without static-analysis evidence, noted in report | No | Yes |
| Database failure | Connection error | 500, generic error page | No (fail fast) | Yes |
| Webhook invalid signature | Signature check | 401, request dropped | No | Yes (future, once webhooks exist) |
| Worker crash mid-job | Job stuck in RUNNING past timeout | Job auto-marked FAILED by a sweep, retry available | Manual | Yes |
