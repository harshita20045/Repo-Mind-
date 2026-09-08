# Diagram — Component Architecture (Backend Modules)

**Status: Confirmed**

```mermaid
flowchart TB
    Auth[auth] --> Org[organizations]
    Org --> GH[github]
    GH --> RAG[rag]
    GH --> Linter[linter]
    RAG --> Review[review]
    Linter --> Review
    GH --> Review
    Review --> Eval[evaluation]
    GH --> ML[ml]
    ML --> Eval
    Review --> Feedback[feedback]
    Auth -.audit.-> Audit[audit]
    Org -.audit.-> Audit
    GH -.audit.-> Audit
    Review -.audit.-> Audit
    Feedback -.audit.-> Audit
```

Dependency direction is strictly one-way. `github` has zero AI dependencies — a pure adapter. `evaluation` is a leaf: nothing depends on it. `audit` observes actions across modules without other modules depending on it.
