# RepoMind — Monitoring & Observability

**Status: Confirmed** for the requirements; **TBD/Proposed** for specific tooling, per the Implementation Blueprint, Part 19 ("No APM/tracing infrastructure at this scale — structured logs + the `job` table's own status history cover debugging needs")

## Application Logs

Structured logs are emitted per pipeline stage — fetch, retrieve, lint, LLM call, predict — each with timing. No specific logging library/format is mandated by the source materials beyond "structured"; standard structured logging (e.g. JSON log lines) is a reasonable implementation choice.

## What Is Tracked

| Signal | Why |
|---|---|
| LLM token usage and $ cost per call | Cost growth is a named risk (see `02-architecture/architecture-decisions.md` risk table, sourced from the Implementation Blueprint, Part 30) |
| GitHub API failures | Surfaces rate-limit/availability issues before they silently degrade review quality |
| RAG retrieval latency | Detects retrieval-path degradation |
| Job failure rate | Directly reflects pipeline health; ties to the `job` table's own status history |
| Review duration end-to-end | Practical adoption/UX signal |

## API Errors

Tracked via standard structured logs at the API layer; the error-handling matrix in `06-testing/testing-strategy.md` defines exactly which failures are logged, retried, and surfaced to the user.

## GitHub Integration Failures

Logged with enough detail to distinguish rate-limit (403/429) from transient (5xx) from permission (403/404 on repository access) failures — these map to different user-facing messages per the error-handling matrix.

## AI Failures

LLM timeouts and invalid-JSON-after-retry failures are logged with the raw output retained (time-boxed, not indefinite — see `05-security/security.md`) specifically to support debugging prompt/schema issues.

## RAG Failures

Embedding-step failures are logged; the review proceeds without RAG context in that case, and the finding is tagged so the degraded quality is visible in the output, not just in logs.

## ML Failures

Not detailed beyond standard exception logging in the source materials — model-loading failures at inference time should be logged and should surface a missing-prediction state in the UI rather than failing the whole review.

## Database Health

Not detailed with specific tooling in the source materials. Standard connection-health checks (e.g. as part of `GET /health` or a dedicated readiness check) are a reasonable minimum — **Proposed**, since no specific requirement or tool is named.

## Performance Metrics

Latency per PR review and approximate dollar cost per review call are explicitly named as practical adoption metrics worth tracking (distinct from the AI-quality research metrics in `06-testing/testing-strategy.md`).

## Review Processing Status

The `job` table's own status history (`pending`/`running`/`completed`/`failed`/`cancelled`, with `created_at`/`updated_at`) is the primary mechanism for observing review-processing status — both for the UI (polling `GET /review-runs/{id}`) and for operational visibility, without a separate monitoring dashboard being required at this scale.

## What Is Deliberately Not Built

No large monitoring stack (no APM, no distributed tracing) is introduced — this is an explicit architectural decision in the source materials, not an oversight. If a specific monitoring technology becomes necessary, it should be selected against a concrete operational need at that time; until then, this is marked:

**Status: TBD/Proposed** — structured logs plus the `job` table's status history are the confirmed baseline; any dashboard/alerting tool on top of them is undecided.
