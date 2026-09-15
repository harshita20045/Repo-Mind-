# Diagram — Deployment Architecture (Native, No Docker)

**Status: Proposed** (the source materials specify Docker Compose for deployment; this diagram reflects the project-owner's explicit native-deployment override — see `01-project/scope.md` and `07-deployment/deployment-guide.md`)

```mermaid
flowchart TB
    subgraph Host[Single Host / VM]
        FE[React build served via a static file server / reverse proxy]
        BE[FastAPI backend — uvicorn/gunicorn process]
        WK[Background worker — Python process]
        PG[(PostgreSQL + pgvector, native install)]
    end
    Browser --> FE
    FE --> BE
    BE --> PG
    WK --> PG
    BE -->|job table| WK
    BE --> GH[GitHub REST API]
    WK --> GH
    WK --> LLM[LLM Provider]
```

No Kubernetes and no container orchestration — no component here has an independent-scaling profile that justifies it. All processes run natively on one host (a developer machine for local development, or a single small VM for staging/production), managed by a process manager (see `07-deployment/deployment-guide.md`).
