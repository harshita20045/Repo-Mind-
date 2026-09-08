# Diagram — RAG Pipeline

**Status: Confirmed**

## Indexing

```mermaid
flowchart TB
    Repo[Repository] --> Discover[File discovery]
    Discover --> Filter["Filter: allow *.md docs, ignore node_modules/vendor/generated"]
    Filter --> Extract[Extract text]
    Extract --> Chunk["Chunk: 500-800 tokens, 50-100 overlap"]
    Chunk --> Embed[Embed via sentence-transformers]
    Embed --> Store[(document_chunk table, repository_id tagged, pgvector)]
```

## Retrieval

```mermaid
flowchart LR
    Diff[PR Diff] --> Query[Derive query from changed files + summary]
    Query --> QEmbed[Embed query]
    QEmbed --> Search["pgvector cosine similarity\nWHERE repository_id = :id"]
    Search --> TopK[Top-k (3-5) chunks]
    TopK --> Context[Passed to context builder\nwith source citations preserved]
```

Re-indexing is triggered only when a document's content hash changes, not on every PR, avoiding re-embedding unchanged docs. Repository isolation is enforced at the query level, not assumed from separate embedding runs — see `06-testing/test-cases.md`, TC-011.
