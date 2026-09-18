# 14 — Feature Flow: Background Worker

## Feature Summary
The background worker is a standalone Python process that polls PostgreSQL every 5 seconds for two types of jobs: pending `ReviewRun` records and unindexed `Repository` records. It uses `SELECT FOR UPDATE SKIP LOCKED` to safely support multiple parallel worker instances without a message broker. On startup, it performs crash recovery by resetting stale `running`/`indexing` jobs.

---

## Process Architecture

```
python -m worker.worker
        |
        v
poll_and_execute()  [infinite loop, sleep 5s between iterations]
        |
        +---> _process_one_job(provider)           [ReviewRun pipeline]
        |
        +---> _process_one_indexing_job()          [RAG indexing pipeline]
```

---

## Startup Crash Recovery

File: `worker/worker.py` → `poll_and_execute()`

```python
# Reset stale 'running' ReviewRuns
stale_count = (
    db.query(ReviewRun)
    .filter(ReviewRun.status == "running")
    .update({"status": "pending", "progress_message": "Reset by worker startup (crash recovery)"})
)

# Reset stale 'indexing' Repositories
stale_repo_count = (
    db.query(Repository)
    .filter(Repository.index_status == "indexing")
    .update({"index_status": "unindexed"})
)
```

This handles the case where the worker process died mid-execution. Without this, jobs would be stuck in `running`/`indexing` indefinitely.

---

## ReviewRun Job Processing

File: `worker/worker.py` → `_process_one_job(provider)`

### Phase 1: Atomic Job Claim (Short Transaction)

```python
with SessionLocal() as db:
    run = (
        db.query(ReviewRun)
        .filter(ReviewRun.status == "pending")
        .with_for_update(skip_locked=True)   # Skip if another worker holds the lock
        .order_by(ReviewRun.id.asc())        # FIFO order
        .first()
    )
    
    if run is None:
        return   # Nothing to do
    
    run.status = "running"
    run.started_at = datetime.now(timezone.utc)
    run.progress_message = "Fetching PR data..."
    db.commit()   # Release lock, claim job
    run_id = run.id
```

The lock is held only for the duration of the claim commit — not for the entire review execution.

### Phase 2: Execute in Fresh Session (Long Transaction)

```python
with SessionLocal() as db:
    run = db.get(ReviewRun, run_id)
    pr = db.get(PullRequest, run.pull_request_id)
    repo = db.get(Repository, pr.repository_id)
    project = db.get(Project, repo.project_id)
    organization_id = project.organization_id
    
    completed_run = run_review(
        db=db,
        pull_request_id=run.pull_request_id,
        organization_id=organization_id,
        provider=provider,
    )
```

A fresh SQLAlchemy session is used for execution. This prevents the long-running review from holding the row lock from the claim phase.

### Error Handling

```python
except ReviewError as exc:
    _fail_run(db, run, str(exc))         # Expected errors (PR not found, etc.)
except Exception as exc:
    _fail_run(db, run, f"{type(exc).__name__}: {exc}")  # Unexpected errors

def _fail_run(db, run, reason):
    run.status = "failed"
    run.completed_at = datetime.now(timezone.utc)
    run.error_message = reason[:1000]
    run.progress_message = None
    db.commit()
```

---

## Repository Indexing Job Processing

File: `worker/worker.py` → `_process_one_indexing_job()`

### Phase 1: Atomic Job Claim

```python
repo = (
    db.query(Repository)
    .filter(Repository.index_status == "unindexed")
    .with_for_update(skip_locked=True)
    .order_by(Repository.id.asc())
    .first()
)

repo.index_status = "indexing"
repo.last_indexed_at = datetime.now(timezone.utc)
db.commit()
repo_id = repo.id
```

### Phase 2: Execute in Fresh Session

```python
with SessionLocal() as db:
    repo = db.get(Repository, repo_id)
    index_repository(db, repo_id)
    
    repo.index_status = "indexed"
    repo.last_indexed_at = datetime.now(timezone.utc)
    db.commit()
```

On failure:
```python
except Exception as exc:
    repo.index_status = "failed"
    db.commit()
```

---

## Consecutive Error Tracking

```python
consecutive_errors = 0
MAX_CONSECUTIVE_ERRORS = 10

while True:
    try:
        _process_one_job(provider)
        _process_one_indexing_job()
        consecutive_errors = 0       # Reset on success
    except Exception as exc:
        consecutive_errors += 1
        if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
            logger.critical("Too many consecutive errors. Worker shutting down.")
            sys.exit(1)
    
    time.sleep(POLL_INTERVAL_SECONDS)   # 5 seconds
```

If 10 consecutive errors occur (e.g., DB is unreachable), the worker exits with code 1.

---

## LLM Provider Initialization

```python
provider = get_llm_provider(settings)  # Called ONCE at startup
logger.info("Worker started. LLM provider: %s. Poll interval: %ds.", type(provider).__name__, ...)
```

The provider is initialized once and reused for all review jobs. This avoids repeated SDK initialization overhead.

---

## Parallelism Support

Using `SELECT FOR UPDATE SKIP LOCKED`, multiple worker processes can run simultaneously against the same PostgreSQL database. Each worker picks a different job. No message broker (Redis/Celery) is required.

To run 3 parallel workers:
```bash
python -m worker.worker &
python -m worker.worker &
python -m worker.worker &
```

---

## Job Lifecycle States

### ReviewRun

```
pending  --> running  --> completed
                     \--> failed
                     \--> cancelled (reserved, not yet used)
```

### Repository

```
unindexed  --> indexing  --> indexed
                        \--> failed
```

---

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `POLL_INTERVAL_SECONDS` | 5 | Sleep between poll loops |
| `MAX_CONSECUTIVE_ERRORS` | 10 | Crash threshold |
| `POSTGRES_URL` | required | DB connection |
| `FERNET_KEY` | required | PAT decryption |
| `LLM_PROVIDER` | required | `groq` / `gemini` / local |
| `GROQ_API_KEY` | conditional | Required when `LLM_PROVIDER=groq` |
| `GEMINI_API_KEY` | conditional | Required for fallback |

---

## Key Files

| File | Location | Role |
|---|---|---|
| `worker.py` | `worker/worker.py` | Complete worker process: startup, crash recovery, job loop |
| `service.py` (review) | `backend/app/review/service.py` | `run_review()` — called by worker |
| `service.py` (rag) | `backend/app/rag/service.py` | `index_repository()` — called by worker |
| `db.py` | `backend/app/db.py` | `SessionLocal` — used by worker for DB sessions |
| `config.py` | `backend/app/core/config.py` | `settings` — loaded by worker |
