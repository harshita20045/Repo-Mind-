# RepoMind — Security

**Status: Confirmed** (per the Implementation Blueprint, Part 18, and the Team Workflow Analysis, Section M)

## Application Security

- Every API query is scoped by `organization_id`/`repository_id` derived from the authenticated session — **never trusted from client-supplied request input**.
- Rate limiting: a standard per-user request rate limit is applied on the API.
- Audit logging: GitHub connection changes, organization membership changes, feedback actions, and evaluation runs are recorded in `audit_log` (see `03-design/database-design.md`).

## Repository / Organization / Project / Team Isolation

RepoMind is multi-tenant at the organization level, and multi-repository within an organization. Two isolation guarantees are confirmed requirements:

1. **Data isolation:** all resource queries are scoped by the requesting user's organization/repository access, derived server-side from the session.
2. **RAG/document isolation:** `document_chunk.repository_id` is filtered on **every** retrieval query — a PR review in one repository must never retrieve or cite documentation chunks from another repository. This is enforced at the query level, not merely assumed from separate embedding/indexing runs, and is covered by a dedicated automated test (see `06-testing/test-cases.md`, TC-011, and `07-deployment` isolation notes).

## GitHub API Security

- The GitHub connection uses a **read-only** Personal Access Token, scoped to the specific repositories being analyzed — never organization-wide admin access.
- RepoMind never requests or uses commit/write access — it should never modify code (a "never" constraint, not merely unbuilt).
- The token is stored **encrypted at rest** in `github_connection`, per organization, never in a shared plaintext `.env` committed to the repository, and never logged.
- Standard GitHub REST rate limits (5000/hr authenticated) are not a concern at internal-team PR volume; the `github` module retries once on a transient 5xx and surfaces 403/429 as a clear job failure, not a silent retry loop.

## API Security

- Session-based authentication on every non-public endpoint (see `05-security/authentication-authorization.md`).
- Standard input validation via Pydantic at the API boundary (see `04-development/coding-standards.md`).
- Webhook signature verification is a **future** control, applicable only once GitHub webhooks exist (Production phase, P3) — not part of the current scope's attack surface, but documented now so it is not forgotten later.

## AI Security — Prompt Injection Protection

Repository content is inherently **untrusted input**: READMEs, ARCHITECTURE/CONTRIBUTING docs, PR descriptions, commit messages, and code comments may contain text engineered to look like an instruction to the AI system.

**Confirmed control:** repository-sourced content is explicitly labeled in the LLM prompt as *untrusted evidence*, structurally separated from the fixed system instruction. The system instruction is outside and independent of any repository-sourced text, and the model is explicitly told not to follow instructions found inside retrieved content. This applies to:
- Repository documentation retrieved via RAG.
- PR titles/descriptions and commit messages.
- Any code comments included in the diff.

**Repository content must never override system/developer instructions.** This is tested directly: a dedicated test PR whose diff/docs contain an embedded fake instruction (e.g. "ignore previous instructions...") asserts the LLM does not comply (see `06-testing/testing-strategy.md`, "Prompt injection" row, P0 priority).

## RAG Security

In addition to prompt-injection framing, the RAG pipeline's own isolation guarantee (above) is itself a security control: without it, a malicious or misconfigured document in one repository could influence findings shown for an unrelated repository's PR.

## Hallucination / Groundedness as a Trust Control

Every `standards_violation` finding must cite a specific source and quoted rule (`evidence`, `repository_rule` fields). Findings claiming to be doc-based without verifiable evidence are visually flagged in the UI as "unverified citation" rather than presented with unwarranted confidence — this is both a quality control and a security-adjacent trust control, since ungrounded "security" or "standards_violation" findings could otherwise be used to mislead a reviewer.

## Logging / Security Events

- Structured logs per pipeline stage, with timing (see `08-operations/monitoring.md`).
- No source code retained in logs beyond what's needed for a specific, time-boxed debugging session — raw diffs and document text are **not** retained indefinitely; findings and feedback records (accept/reject) are fine to retain long-term, since they do not contain raw source code.
- Sensitive actions (GitHub connection changes, membership changes, feedback, evaluation runs) are captured in `audit_log`.

## Data Protection

- **Source-code privacy disclosure:** organization admins are explicitly told, at GitHub-connection time, that PR diffs are sent to the configured LLM provider. This is a disclosure requirement, not merely a technical control.
- Private/enterprise repositories should default to a local LLM option or an enterprise-approved API endpoint if sending code to a third-party LLM is not contractually acceptable — the LLM client is deliberately built as a **configurable provider**, with a local/self-hosted model documented as a future option (see `01-project/scope.md`, Future Scope), specifically to support this.
- Data retention: feedback and findings are retained; raw diffs/document text are not retained beyond what the review record itself needs.

## Dependency Security

Not detailed beyond the choice of well-maintained, standard libraries (FastAPI, SQLAlchemy, scikit-learn, sentence-transformers) named throughout the source materials. No specific dependency-scanning tool is named in the source materials — **Open Decision / TBD** if one is introduced.

## Explicit "Never" Constraints

- RepoMind **never** requests or uses write/commit access to a connected repository.
- No individual developer performance score exists anywhere in the data model or UI (see `01-project/requirements.md`, NFR-010) — this is treated as a fairness/trust security-adjacent constraint enforced at the schema level, not just a policy statement.
