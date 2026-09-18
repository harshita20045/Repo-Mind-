# 04 — Feature Flow: RAG Indexing

## Feature Summary
When a repository's `index_status` is `'unindexed'`, the background worker picks it up and runs the full RAG indexing pipeline: discover documents from GitHub's tree API, load and hash each file, chunk text into 256-token windows, embed with `sentence-transformers/all-MiniLM-L6-v2` (384 dims), and persist both document metadata and vector embeddings into PostgreSQL via `pgvector`.

---

## Trigger Chain

```
Repository.index_status = 'unindexed'
    |
    | (worker polls every 5s)
    v
worker._process_one_indexing_job()
    |
    v
rag.service.index_repository(db, repository_id)
    |
    v
RAG Pipeline: discover -> load -> hash -> chunk -> embed -> persist
```

---

## Detailed Step-by-Step

### Step 1: Worker Claims the Job
File: `worker/worker.py` → `_process_one_indexing_job()`

```
SELECT repository WHERE index_status='unindexed'
FOR UPDATE SKIP LOCKED
ORDER BY id ASC
LIMIT 1
```
- Sets `repo.index_status = 'indexing'`  
- Commits the claim immediately (prevents double-processing)
- Opens a fresh session for the actual indexing work

---

### Step 2: Setup — Decrypt PAT & Initialize Components
File: `backend/app/rag/service.py` → `index_repository(db, repository_id)`

```python
repo = db.get(Repository, repository_id)
project = repo.project
organization_id = project.organization_id

stmt = select(GithubConnection).where(GithubConnection.organization_id == organization_id)
conn = db.execute(stmt).scalars().first()

pat = decrypt_token(conn.encrypted_token)           # Fernet decrypt
github_client = GitHubClient(pat)                   # httpx client

loader = DocumentLoader(github_client, owner, name, default_branch)
chunker = TextChunker()
embedder = LocalEmbedder()
rag_repo = RAGRepository(db)
```

---

### Step 3: Discover Documents
File: `backend/app/rag/loader.py` → `DocumentLoader.discover_documents()`

```
GET /repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1
```
- Filters by file extensions: `.md`, `.txt`, `.rst`, `.py`, `.ts`, `.js`, `.jsx`, `.tsx`, `.json`, `.yaml`, `.yml`  
- Returns list of `{"path": "...", "sha": "..."}` dicts  
- SHA is the Git blob SHA (content-addressable)

---

### Step 4: Load Document Content
File: `backend/app/rag/loader.py` → `DocumentLoader.load_document_content(path, sha)`

```
GET /repos/{owner}/{repo}/git/blobs/{sha}
```
- Returns base64-encoded content; decoded to UTF-8 text  
- Empty files are skipped (`return None` → `continue` in service)

---

### Step 5: Hash for Idempotency
File: `backend/app/rag/loader.py` → `DocumentLoader.hash_content(text)`

```python
hashlib.sha256(text.encode("utf-8")).hexdigest()
```
- Compared against `Document.content_hash` in DB  
- If unchanged: **skip** (idempotent re-index)  
- If changed: delete old chunks + re-embed  

---

### Step 6: Save Document Metadata
File: `backend/app/rag/repository.py` → `RAGRepository.save_document()`

```python
doc = Document(
    repository_id=repository_id,
    path=path,
    content_hash=content_hash
)
db.add(doc)
db.flush()   # Get doc.id without commit
```

---

### Step 7: Chunking
File: `backend/app/rag/chunker.py` → `TextChunker.chunk_text(text)`

Algorithm:
1. Tokenize text using the model's tokenizer (`all-MiniLM-L6-v2`)
2. Slide a window of **256 tokens** with **50-token overlap**
3. Decode each window back to UTF-8 text
4. Return list of string chunks

This is deterministic: same input always produces same chunks.

---

### Step 8: Embedding
File: `backend/app/rag/embedder.py` → `LocalEmbedder.embed_chunks(chunks)`

```python
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embeddings = model.encode(chunks)   # shape: (N, 384)
return [e.tolist() for e in embeddings]
```
- Model loaded from local cache (or downloaded first time)
- Returns list of 384-dimensional float vectors
- Runs in-process (no external API call)

---

### Step 9: Determine Chunk Type
File: `backend/app/rag/loader.py` → `DocumentLoader.determine_chunk_type(path)`

| Extension | `chunk_type` |
|---|---|
| `.md`, `.rst`, `.txt` | `documentation` |
| `.py`, `.ts`, `.js`, `.jsx`, `.tsx` | `source_code` |
| `.json`, `.yaml`, `.yml` | `configuration` |
| (default) | `documentation` |

---

### Step 10: Persist Chunks (with stale-chunk deletion)
File: `backend/app/rag/repository.py` → `RAGRepository.save_chunks()`

```python
# Delete stale chunks first (re-index case)
DELETE FROM document_chunk WHERE repository_id=? AND document_id=?

# Insert new chunks
for idx, (text, embedding) in enumerate(chunks):
    chunk = DocumentChunk(
        document_id=doc.id,
        repository_id=repository_id,
        text=text,
        embedding=embedding,    # Stored as vector(384) in pgvector column
        chunk_index=idx,
        chunk_type=chunk_type,
        file_path=path
    )
    db.add(chunk)
db.flush()
```

---

### Step 11: Final Commit
File: `backend/app/rag/service.py`

```python
db.commit()   # Commit all documents + chunks atomically
```

Worker then marks:
```python
repo.index_status = 'indexed'
repo.last_indexed_at = datetime.now(timezone.utc)
db.commit()
```

---

## Crash Recovery

On worker startup (`worker.py:95-105`):
```python
db.query(Repository)
  .filter(Repository.index_status == "indexing")
  .update({"index_status": "unindexed"})
```
Any repository stuck in `'indexing'` (from a previous crash) is reset to `'unindexed'` and re-queued.

---

## Manual Re-Index

| Step | Where | What Happens |
|---|---|---|
| User clicks "Re-index" | `RepositoriesPage.jsx` | `orgApi.triggerIndex(repoId)` |
| API call | `lib/api.js:93` | `POST /repositories/{repoId}/index` |
| Route | `backend/app/organizations/router.py` | Sets `repo.index_status = 'unindexed'`, commits |
| Worker pickup | Worker next poll | `_process_one_indexing_job()` picks it up |

---

## Key Files

| File | Location | Role |
|---|---|---|
| `service.py` | `backend/app/rag/service.py` | `index_repository()` — orchestration |
| `loader.py` | `backend/app/rag/loader.py` | `DocumentLoader` — GitHub tree + blob fetching, hash |
| `chunker.py` | `backend/app/rag/chunker.py` | `TextChunker` — 256/50 token sliding window |
| `embedder.py` | `backend/app/rag/embedder.py` | `LocalEmbedder` — sentence-transformers inference |
| `repository.py` | `backend/app/rag/repository.py` | `RAGRepository` — DB read/write for Document + DocumentChunk |
| `retriever.py` | `backend/app/rag/retriever.py` | `RAGRetriever.search()` — cosine distance vector search |
| `models.py` | `backend/app/rag/models.py` | `Document`, `DocumentChunk` SQLAlchemy models |
| `worker.py` | `worker/worker.py` | `_process_one_indexing_job()` |

---

## Database Tables

| Table | Column | Detail |
|---|---|---|
| `document` | `repository_id`, `path`, `content_hash` | One row per indexed file |
| `document_chunk` | `document_id`, `repository_id`, `text`, `embedding` (vector(384)), `chunk_index`, `chunk_type`, `file_path` | One row per chunk |

The `embedding` column uses pgvector's `vector(384)` type. Cosine distance queries use `<=>` operator.

---

## Embedding Model Details

| Property | Value |
|---|---|
| Model | `sentence-transformers/all-MiniLM-L6-v2` |
| Dimensions | 384 |
| Inference | Local CPU/GPU (no API key required) |
| Normalization | L2-normalized by default |
| Cosine distance range | 0.0 (identical) to 2.0 (opposite) |
| Distance operator in pgvector | `<=>` (cosine distance) |

---

## RAG Retrieval (used during review)

File: `backend/app/rag/retriever.py` → `RAGRetriever.search()`

```python
query_embedding = embedder.embed_chunks([query_text])[0]

# pgvector cosine distance query
results = db.query(DocumentChunk)
    .filter(DocumentChunk.repository_id == repository_id)   # ISOLATION ENFORCED
    .order_by(DocumentChunk.embedding.op("<=>")(query_embedding))
    .limit(top_k)
    .all()
```

Repository isolation is enforced at every retrieval: `filter(DocumentChunk.repository_id == repository_id)`. Cross-repository leakage is architecturally impossible.
