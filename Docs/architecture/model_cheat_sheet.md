# 15 — Database Schema & Model Cheat Sheet

## All SQLAlchemy Models

### Tables & Source Files

| Table | SQLAlchemy Model | Source File |
|---|---|---|
| `user` | `User` | `backend/app/auth/models.py` |
| `organization` | `Organization` | `backend/app/organizations/models.py` |
| `org_membership` | `OrgMembership` | `backend/app/auth/models.py` |
| `project` | `Project` | `backend/app/organizations/models.py` |
| `repository` | `Repository` | `backend/app/organizations/models.py` |
| `github_connection` | `GithubConnection` | `backend/app/github/models.py` (or organizations) |
| `pull_request` | `PullRequest` | `backend/app/github/models.py` |
| `commit` | `Commit` | `backend/app/github/models.py` |
| `document` | `Document` | `backend/app/rag/models.py` |
| `document_chunk` | `DocumentChunk` | `backend/app/rag/models.py` |
| `review_run` | `ReviewRun` | `backend/app/review/models.py` |
| `finding` | `Finding` | `backend/app/review/models.py` |
| `finding_evidence` | `FindingEvidence` | `backend/app/review/models.py` |
| `linter_result` | `LinterResult` | `backend/app/review/models.py` |
| `risk_assessment` | `RiskAssessment` | `backend/app/review/models.py` |
| `conflict` | `Conflict` | `backend/app/review/models.py` |
| `human_decision` | `HumanDecision` | `backend/app/review/models.py` |
| `chat_session` | `ChatSession` | `backend/app/chat/models.py` |
| `chat_message` | `ChatMessage` | `backend/app/chat/models.py` |
| `ml_prediction` | `MLPrediction` | `backend/app/ml/models.py` |
| `audit_log` | `AuditLog` | `backend/app/audit/models.py` |
| `webhook_event` | `WebhookEvent` | `backend/app/webhooks/models.py` |

---

## Model Detail: Auth

### `user`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `email` | String unique | Login identifier |
| `hashed_password` | String | bcrypt hash, 12 rounds |
| `role` | String | `developer` / `reviewer` / `tech_lead` / `org_admin` (global) |
| `is_active` | Boolean | Soft disable |
| `created_at` | DateTime(tz) | |

### `org_membership`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → `user.id` CASCADE | |
| `organization_id` | FK → `organization.id` CASCADE | |
| `role` | String | Role within this org (matches RoleEnum) |
| `joined_at` | DateTime(tz) | |

---

## Model Detail: Organizations

### `organization`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `name` | String | Display name |
| `created_at` | DateTime(tz) | |

### `project`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `organization_id` | FK → `organization.id` CASCADE | |
| `name` | String | Project display name |
| `created_at` | DateTime(tz) | |

### `repository`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `project_id` | FK → `project.id` CASCADE | |
| `github_owner` | String | e.g., `"octocat"` |
| `github_name` | String | e.g., `"my-repo"` |
| `default_branch` | String | e.g., `"main"` |
| `index_status` | String | `unindexed` / `indexing` / `indexed` / `failed` |
| `last_indexed_at` | DateTime(tz) nullable | |

---

## Model Detail: GitHub

### `github_connection`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `organization_id` | FK → `organization.id` | |
| `encrypted_token` | String | Fernet-encrypted PAT |
| `created_at` | DateTime(tz) | |

### `pull_request`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `repository_id` | FK → `repository.id` CASCADE | |
| `github_number` | Integer | PR number on GitHub |
| `title` | String | PR title |
| `state` | String | `open` / `closed` / `merged` |
| `head_sha` | String(40) | Current HEAD commit SHA |
| `additions` | Integer nullable | Line additions (from GitHub) |
| `deletions` | Integer nullable | Line deletions (from GitHub) |
| `files_changed` | Integer nullable | Number of files changed |
| `created_at` | DateTime(tz) | PR creation time |
| `merged_at` | DateTime(tz) nullable | Used by ML trainer |

### `commit`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `repository_id` | FK → `repository.id` CASCADE | |
| `sha` | String(40) unique | Git commit SHA |
| `message` | Text | Commit message |
| `author_name` | String | |
| `committed_at` | DateTime(tz) | |

---

## Model Detail: RAG

### `document`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `repository_id` | FK → `repository.id` | |
| `path` | String | File path in repo |
| `content_hash` | String | SHA-256 of file content |

### `document_chunk`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `document_id` | FK → `document.id` | |
| `repository_id` | Integer | Denormalized for fast filtering |
| `text` | Text | Chunk content |
| `embedding` | Vector(384) | pgvector column — cosine distance |
| `chunk_index` | Integer | Position within document |
| `chunk_type` | String | `documentation` / `source_code` / `configuration` |
| `file_path` | String | Redundant path for quick lookup |

---

## Model Detail: Review

### `review_run`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `pull_request_id` | FK → `pull_request.id` CASCADE | |
| `commit_sha` | String(255) | SHA at time of review |
| `status` | String(50) | `pending` / `running` / `completed` / `failed` |
| `repomind_version` | String(50) | `"0.8.0"` |
| `prompt_version` | String(50) | `"p8-v1"` |
| `llm_model` | String(255) | Provider class name |
| `rag_enabled` | Boolean | Always `True` |
| `intelligence_mode` | String(20) | `"v1"` |
| `started_at` | DateTime(tz) nullable | |
| `completed_at` | DateTime(tz) nullable | |
| `progress_message` | String(255) nullable | UI polling field |
| `error_message` | Text nullable | Never exposed to UI |

### `finding`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` CASCADE | |
| `type` | String(100) | LLM-assigned category (maps to `category` in schema) |
| `severity` | String(50) | `critical`/`high`/`medium`/`low`/`info` |
| `file` | String(1024) nullable | File path |
| `line` | Integer nullable | Line number |
| `title` | String(512) | |
| `explanation` | Text | `problem` from LLM schema |
| `rule_source` | Text nullable | `evidence` from LLM schema |
| `recommendation` | Text nullable | |
| `confidence` | Float | Adjusted by evidence layer |
| `status` | String(50) | `open`/`accepted`/`rejected`/`resolved`/`dismissed` |
| `evidence_status` | String(50) | `supported`/`unverified`/`contradicted` |
| `lifecycle_status` | String(50) | `new`/`persistent`/`resolved` |

### `finding_evidence`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `finding_id` | FK → `finding.id` CASCADE | |
| `evidence_status` | String(50) | `supported` / `contradicted` |
| `source_type` | String(50) | `documentation`/`source_code`/`linter`/`diff`/`test` |
| `source_path` | String(1024) nullable | File path of evidence |
| `source_text` | Text nullable | Truncated to 2000 chars |
| `citation_metadata` | JSONB nullable | Line numbers, chunk IDs, distances |

### `linter_result`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` CASCADE | |
| `tool` | String(255) | `"ruff"` / `"bandit"` |
| `raw_output` | JSONB | Full linter JSON output |

### `risk_assessment`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` CASCADE, UNIQUE | One per review run |
| `score` | Integer | 0–100 |
| `level` | String(20) | `low`/`medium`/`high`/`critical` |
| `factors` | JSONB | Per-factor breakdown |
| `blast_radius` | JSONB | `{directly_affected, potentially_affected, ...}` |
| `test_impact` | JSONB | `{affected_source_files, likely_affected_tests, ...}` |
| `summary` | Text | Human-readable explanation |
| `calculated_at` | DateTime(tz) | |

### `conflict`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` CASCADE | |
| `conflict_type` | String(50) | `mechanical` / `semantic` |
| `category` | String(100) | `git_merge`/`architecture`/`api_contract`/`security_policy`/`test_contract`/`configuration` |
| `severity` | String(50) | `critical`/`high`/`medium`/`low` |
| `title` | String(512) | |
| `description` | Text | |
| `evidence` | JSONB | `{expected, actual, sources, pattern_matched}` |
| `status` | String(50) | `open`/`dismissed`/`resolved` |

### `human_decision`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `review_run_id` | FK → `review_run.id` CASCADE | |
| `user_id` | FK → `user.id` SET NULL | Nullable if user deleted |
| `action` | String(50) | `approve`/`request_changes`/`dismiss`/`resolve_finding` |
| `target_type` | String(50) nullable | `finding`/`conflict`/`review` |
| `target_id` | Integer nullable | ID of specific target |
| `note` | Text nullable | Human justification |
| `created_at` | DateTime(tz) | |

---

## Model Detail: Chat

### `chat_session`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → `user.id` CASCADE | |
| `context_type` | String(50) | `pr`/`repository`/`review` |
| `context_id` | Integer | ID of scoped resource |
| `organization_id` | FK → `organization.id` CASCADE | |
| `created_at` | DateTime(tz) | |
| `last_message_at` | DateTime(tz) nullable | |

### `chat_message`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `session_id` | FK → `chat_session.id` CASCADE | |
| `role` | String(20) | `user`/`assistant` |
| `content` | Text | |
| `sources` | JSONB nullable | `[{type, path}]` for assistant messages |
| `is_grounded` | Boolean nullable | Whether RAG context was found |
| `created_at` | DateTime(tz) | |

---

## Model Detail: ML

### `ml_prediction`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `pull_request_id` | FK → `pull_request.id` | |
| `predicted_delay_category` | String | `ON_TIME` / `SLOW` |
| `confidence_score` | Float | 0.0–1.0 (always 0.5 for baseline) |
| `prediction_model_version` | String | `"baseline-v1"` |
| `created_at` | DateTime(tz) | |

---

## Model Detail: Audit

### `audit_log`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → `user.id` SET NULL nullable | |
| `organization_id` | FK → `organization.id` nullable | |
| `action` | String | Action taken |
| `resource_type` | String nullable | e.g., `repository`, `review_run` |
| `resource_id` | Integer nullable | |
| `details` | JSONB nullable | Additional context |
| `created_at` | DateTime(tz) | |

---

## Model Detail: Webhooks

### `webhook_event`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `github_delivery_id` | String unique | `X-GitHub-Delivery` header value |
| `event_type` | String | `pull_request`/`ping`/etc. |
| `action` | String nullable | `opened`/`synchronize`/etc. |
| `repository_id` | FK → `repository.id` nullable | |
| `payload` | JSONB | Full GitHub event payload |
| `status` | String | `received`/`processed`/`skipped` |
| `processed_at` | DateTime nullable | |
| `error_message` | Text nullable | |
| `received_at` | DateTime(tz) | |

---

## Database Configuration

File: `backend/app/db.py`

```python
SQLALCHEMY_DATABASE_URL = settings.POSTGRES_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

pgvector extension must be enabled before running Alembic migrations:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
