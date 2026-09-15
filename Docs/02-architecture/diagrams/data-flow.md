# Diagram — End-to-End Data Flow

**Status: Confirmed**

```mermaid
flowchart TB
    GH[GitHub Repository] -->|REST API| PR[PR Metadata + Diff]
    GH -->|REST API| Docs[Repository Documentation]
    Docs --> Chunk[Chunk + Embed]
    Chunk --> Store[(document_chunk, pgvector)]
    PR --> Feat[Feature Engineering]
    Feat --> MLModels[ML Models]
    MLModels --> MLPred[(ml_prediction)]
    PR --> Linter[Static Analysis]
    PR --> Query[Diff-derived query]
    Query --> Retrieve[pgvector retrieval, repository_id filtered]
    Store --> Retrieve
    Retrieve --> Context[Context Builder]
    Linter --> Context
    PR --> Context
    Context --> LLM[LLM Review]
    LLM --> Findings[(finding, review_run)]
    Findings --> UI[RepoMind UI]
    MLPred --> UI
    Findings --> Feedback[Accept/Reject]
    Feedback --> FeedbackStore[(finding_feedback)]
    Findings --> Eval[Evaluation Runner]
    FeedbackStore --> Eval
    Eval --> EvalStore[(evaluation_run)]
```

This diagram traces every data item from its GitHub source through to where it is stored and where it is surfaced in the UI, matching the module boundaries in `02-architecture/system-architecture.md`.
