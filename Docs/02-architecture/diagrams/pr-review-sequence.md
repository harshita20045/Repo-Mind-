# Diagram — PR Review Sequence

**Status: Confirmed**

```mermaid
sequenceDiagram
    participant U as Reviewer
    participant API as Backend
    participant W as Worker
    participant GH as GitHub API
    participant LLM as LLM Provider
    participant DB as Database
    U->>API: POST /pull-requests/{id}/review
    API->>DB: create job type=review_pr, status=pending
    API-->>U: job queued (poll or websocket for status)
    W->>DB: pick up job
    W->>GH: fetch diff, changed files
    W->>DB: retrieve relevant chunks (repository_id filtered)
    W->>W: run linter
    W->>LLM: build context, call LLM
    LLM-->>W: structured JSON
    W->>W: validate schema
    W->>DB: store ReviewRun, Finding[]
    W->>DB: mark job completed
    U->>API: GET /review-runs/{id}
    API-->>U: findings displayed
```

## Job State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> FETCHING
    FETCHING --> RETRIEVING
    RETRIEVING --> LINTING
    LINTING --> REVIEWING
    REVIEWING --> PREDICTING
    PREDICTING --> COMPLETED
    FETCHING --> FAILED
    RETRIEVING --> FAILED
    REVIEWING --> FAILED
    COMPLETED --> [*]
    FAILED --> [*]
```

## Re-analysis Sequence

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant API as Backend
    participant W as Worker
    Dev->>GH: push new commit
    Note over API: Current phase — manual re-trigger;<br/>Future — webhook auto-fires
    API->>W: create job type=review_pr (new commit_sha)
    W->>W: re-run full pipeline
    W->>W: diff findings vs. previous run: NEW / PERSISTENT / RESOLVED
```
