# RepoMind 2.0 — System Architecture

**Status: Completed**

## Overall Architecture

RepoMind 2.0 is a **modular monolith**. It is designed to be run natively on bare-metal or VMs using Python Virtual Environments (NO Docker). 

```mermaid
flowchart TB
    User[Developer / Reviewer / Team Lead / Org Admin] --> FE[React Frontend]
    FE -->|HTTPS/REST| API[FastAPI Backend — Modular Monolith]
    API --> DB[(PostgreSQL + pgvector)]
    API --> GH[GitHub REST API]
    API --> LLM[Google Gemini API]
    API --> Engines[Risk & Conflict Engines]
```

## Frontend

React + Vite + TailwindCSS (v3.4.0) single-page application. Features a premium dark-mode glassmorphism aesthetic. Server state is managed with TanStack Query. 
Core views: Dashboard, Repositories, PRs, Security Browser, Settings, and Review UI.

## Backend

FastAPI + Pydantic, organized as internal modules:

| Module | Responsibility | Depends on |
|---|---|---|
| `auth` | Login, sessions, org membership | — |
| `organizations` | Org/Project/Repository hierarchy | `auth` |
| `github` | GitHub API client, PR/doc/diff fetch | `organizations` |
| `rag` | Chunk, embed, retrieve via pgvector | `github` |
| `review` | Build Gemini context, run engines, validate output | `rag`, `github` |
| `chat` | Manage AI conversational sessions | `rag`, `github` |
| `risk` | Compute logical complexity score | `github` |
| `conflicts` | Detect cross-PR merge conflicts | `github` |

## AI Layer

The AI layer is exclusively powered by Google Gemini (`google-genai` SDK) and Code-Aware RAG.
There are no local ML models or complex ML training pipelines. The LLM handles structure findings and real-time chat, strictly grounded in repository rules.

## Authentication Flow

```mermaid
sequenceDiagram
    participant U as User
    participant FE as React Frontend
    participant API as Backend
    participant DB as Database
    U->>FE: enter email + password
    FE->>API: POST /auth/login
    API->>DB: verify password_hash + load organization memberships
    DB-->>API: user + roles + org scope
    API-->>FE: session token / cookie
    FE->>API: request scoped data with session attached
    API->>DB: derive organization_id / repository_id from session
    DB-->>API: authorized response payload
```

## Repository Onboarding / Indexing Flow

```mermaid
sequenceDiagram
    participant Admin as Org Admin
    participant FE as React Frontend
    participant API as Backend
    participant GH as GitHub API
    participant DB as Database
    Admin->>FE: connect repository
    FE->>API: POST /repositories/connect
    API->>DB: store github_connection + repository row
    API->>GH: fetch repository docs + metadata
    API->>API: filter, chunk, embed repository docs
    API->>DB: store document + document_chunk rows via pgvector
    API-->>FE: index complete
```

## Database

PostgreSQL is the single data store for relational data **and** for embedding storage/search via the natively installed `pgvector` extension. 

## RAG Pipeline

```mermaid
flowchart TB
    Repo[Repository] --> Discover[File discovery]
    Discover --> Filter["Filter: allow *.md docs"]
    Filter --> Extract[Extract text]
    Extract --> Chunk["Chunk text"]
    Chunk --> Embed[Embed via sentence-transformers]
    Embed --> Store[(document_chunk table, repository_id tagged, pgvector)]
```

Retrieval: diff/chat query → embed → `pgvector` cosine similarity, **filtered by `repository_id` on every query** → top-k → passed to Gemini.

## API Communication

Frontend ↔ backend communication is HTTPS/REST with session-based authentication.

## PR Review Flow

```mermaid
sequenceDiagram
    participant U as Reviewer
    participant API as Backend
    participant GH as GitHub API
    participant Gemini as Google Gemini
    participant DB as Database
    U->>API: POST /pull-requests/{id}/review
    API->>GH: fetch diff, changed files
    API->>DB: retrieve relevant chunks (repository_id filtered)
    API->>API: run risk and conflict engines
    API->>Gemini: build context, call LLM
    Gemini-->>API: structured JSON
    API->>DB: store ReviewRun, Finding[]
    API-->>U: findings displayed
```
