# RepoMind Phase 6–7 Complete Technical Walkthrough

## Executive Summary
This document serves as a deep technical dive into the implementation of RepoMind's Phase 6 (Repository Indexing and Embedding) and Phase 7 (Repository-Isolated Vector Retrieval). It explains the entire architecture, data flow, code specifics, database migrations, and testing strategies. The goal is to provide a comprehensive mental model to understand *how* and *why* RepoMind converts GitHub Markdown documents into mathematical vectors, and how those vectors are later retrieved to power the core RAG (Retrieval-Augmented Generation) capability, all while maintaining strict organizational security boundaries.

---

## Part 1 — Phase 6 Overview

### Phase 6 — Repository Indexing and Embedding Pipeline

The fundamental problem Phase 6 solves is preparing raw GitHub code/documentation for an LLM to understand contextually. An LLM cannot read a 10,000-line codebase in real-time efficiently. RepoMind needs to index this content and map it semantically so that we can retrieve *only* the relevant parts when a PR is opened.

The pipeline converts:
**Repository → Repository contents → Documents → Chunks → Embeddings → Vector storage**

*   **GitHub repository**: The external remote Git source.
*   **Repository record**: A row in our `repository` table connecting the GitHub origin to a RepoMind Project.
*   **Document**: A single markdown file represented in the `document` table.
*   **DocumentChunk**: A smaller, model-friendly slice of a document.
*   **Embedding vector**: A 384-dimensional mathematical representation of a chunk's semantic meaning.
*   **PostgreSQL**: Our primary relational database.
*   **pgvector**: The PostgreSQL extension allowing vector storage and similarity searches.
*   **LocalEmbedder**: The Python class that generates embeddings locally using CPU without relying on external APIs.

Phase 6 *does* orchestrate the downloading, hashing, chunking, embedding, and storage of documents. Phase 6 *does not* implement retrieval, LLM interaction, or background job polling.

---

## Part 2 — Phase 6 Complete End-to-End Flow

```text
GitHub Repository
      ↓ (GitHub API requests)
Repository Loader
      ↓ (Security paths/files filtering)
Document
      ↓ (HuggingFace AutoTokenizer)
Chunker
      ↓ (Overlap slicing)
DocumentChunk
      ↓ (sentence-transformers encode)
LocalEmbedder
      ↓ (Float list validation)
384-dimensional vector
      ↓ (SQLAlchemy insert)
PostgreSQL + pgvector
```

### Stage Explanations
1.  **Repository Loader**: 
    *   *Input*: `owner`, `repo`, `sha`.
    *   *Function*: `DocumentLoader.discover_documents()`.
    *   *Output*: List of file metadata.
    *   *Why*: Discovers which Markdown files exist via recursive Git tree API.
2.  **File Filtering**: 
    *   *Input*: File path.
    *   *Function*: `DocumentLoader._should_exclude_path()`.
    *   *Output*: Boolean.
    *   *Why*: Strips `.env`, `.git`, `node_modules` for security and relevance.
3.  **Document**:
    *   *Input*: File content.
    *   *Function*: `RAGRepository.save_document()`.
    *   *Output*: DB record ID.
    *   *Why*: Establishes a parent record for the file and its SHA-256 hash.
4.  **Chunker**:
    *   *Input*: Full document text.
    *   *Function*: `TextChunker.chunk_text()`.
    *   *Output*: List of overlapping strings.
    *   *Why*: LLMs and embedding models have strict token limits (256 for MiniLM).
5.  **LocalEmbedder**:
    *   *Input*: List of text chunks.
    *   *Function*: `LocalEmbedder.embed_chunks()`.
    *   *Output*: `List[List[float]]` (384 dims).
    *   *Why*: Converts text into semantic mathematical coordinates.
6.  **PostgreSQL + pgvector**:
    *   *Input*: Chunks and float arrays.
    *   *Function*: `RAGRepository.save_chunks()`.
    *   *Output*: DB insertion.
    *   *Why*: Persistent storage enabling later vector similarity search.

---

## Part 3 — Phase 6 File-by-File Walkthrough

### `backend/app/rag/service.py`
**Responsibility**: Orchestrates the entire pipeline.
**Important Function**: `index_repository(db, repository_id)`
**Flow**:
```text
service.index_repository(...)
    ↓
github_client.get_repository_tree(...) via loader.discover_documents()
    ↓
loader.load_document_content(...)
    ↓
loader.hash_content(...)
    ↓
rag_repo.save_document(...)
    ↓
chunker.chunk_text(...)
    ↓
embedder.embed_chunks(...)
    ↓
rag_repo.save_chunks(...)
```
**Decisions**: Ensures the PAT (Personal Access Token) is fetched dynamically, decrypted, and not stored longer than needed.

### `backend/app/rag/loader.py`
**Responsibility**: GitHub communication and rule-based file inclusion.
**Classes/Functions**: `DocumentLoader`, `discover_documents()`, `load_document_content()`, `_should_exclude_path()`.
**Decisions**: Enforces exact security boundary rules (`.env`, `vendor`, `node_modules`) explicitly in Python.

### `backend/app/rag/chunker.py`
**Responsibility**: Token-aware deterministic string splitting.
**Classes/Functions**: `TextChunker`, `chunk_text()`.
**Decisions**: Uses exact `sentence-transformers` tokenizer instead of naive character counts to prevent silent truncation.

### `backend/app/rag/embedder.py`
**Responsibility**: In-memory CPU inference for sentence-transformers.
**Classes/Functions**: `LocalEmbedder`, `embed_chunks()`.
**Decisions**: Validates exact 384-dimensional output and lack of NaN/infinite floats to protect the DB from poisoning.

### `backend/app/rag/repository.py`
**Responsibility**: Database persistence layer.
**Classes/Functions**: `RAGRepository`, `save_document()`, `save_chunks()`.
**Decisions**: Deletes existing chunks for a document before inserting new ones to maintain state safely.

---

## Part 4 — Line-by-Line Code Teaching

### Function: `_should_exclude_path()`
**File**: `backend/app/rag/loader.py`
**Purpose**: Security and relevance filter for GitHub tree blobs.
**Called by**: `DocumentLoader.discover_documents()`

```python
def _should_exclude_path(self, path: str) -> bool:
    parts = path.split("/")
    
    # Check excluded directories
    for part in parts[:-1]:
        if part in EXCLUDED_DIRS:  # EXCLUDED_DIRS = {"node_modules", "vendor", ...}
            return True
            
    filename = parts[-1]
    
    # Check exact filename exclusions
    if filename in EXCLUDED_FILES or filename.startswith(".env."):
        return True
        
    # Only include markdown files
    if not filename.endswith(".md"):
        return True
        
    return False
```
*   `path.split("/")`: Python string manipulation to isolate directories and the filename.
*   `for part in parts[:-1]`: Iterates over all directory segments. If the path is `node_modules/api/auth.md`, `part` will evaluate `node_modules`, flag true, and exit early.
*   `not filename.endswith(".md")`: We strictly only index Markdown files for the MVP. Removing this line would attempt to chunk and embed binary images or heavy minified JS files.

### Function: `chunk_text()`
**File**: `backend/app/rag/chunker.py`
**Purpose**: Splits documents into overlapping tokenized blocks.

```python
tokens = self.tokenizer.encode(text, add_special_tokens=False)
chunks = []
start = 0
while start < len(tokens):
    end = start + self.max_tokens
    chunk_tokens = tokens[start:end]
    chunk_text = self.tokenizer.decode(chunk_tokens, skip_special_tokens=True)
    if chunk_text.strip():
        chunks.append(chunk_text)
    start += (self.max_tokens - self.overlap_tokens)
```
*   `self.tokenizer.encode`: Uses the HuggingFace AutoTokenizer to convert a string into an integer array of tokens.
*   `start + self.max_tokens`: Takes a slice of exactly 256 tokens.
*   `start += (self.max_tokens - self.overlap_tokens)`: Advances the window by `256 - 50 = 206` tokens, creating an intentional 50-token overlap between chunks.

### Function: `embed_chunks()`
**File**: `backend/app/rag/embedder.py`
**Purpose**: Transforms token chunks into math vectors.

```python
embeddings_array = self.model.encode(chunks, convert_to_numpy=True)
result = []
for emb in embeddings_array:
    float_list = emb.tolist()
    if len(float_list) != self.EXPECTED_DIMENSIONS:
        raise EmbedderError(...)
    result.append(float_list)
```
*   `self.model.encode(...)`: Triggers the local PyTorch model to run inference. It returns a NumPy matrix.
*   `emb.tolist()`: NumPy arrays must be converted to standard Python float lists before SQLAlchemy and `psycopg2` can serialize them into PostgreSQL `vector(384)`.
*   `if len(float_list) != 384`: Prevents writing a corrupted embedding which would crash the `pgvector` column constraints.

---

## Part 5 — GitHub Repository Loading

RepoMind uses the GitHub REST API (specifically `GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1`) to get the entire architecture of the codebase in one call. 
*   **tree**: A JSON list containing every file and folder in the repo.
*   **blob**: A specific file's content in Git, identifiable by a unique `sha`.
*   **document**: RepoMind's internal representation of a file.

The loader actively skips `vendor/`, `node_modules/`, `.git/`, `.env`, and only downloads `.md` files to ensure we don't pollute the context window with raw dependencies.
If GitHub returns `"truncated": true` (repo is too massive), RepoMind explicitly raises an error rather than silently omitting files.

---

## Part 6 — Hashing

RepoMind implements SHA-256 content hashing (`hashlib.sha256(content.encode("utf-8")).hexdigest()`).
*   **What is hashed**: The exact UTF-8 string content of the downloaded file.
*   **Why**: It is stored in `Document.content_hash`. In `index_repository()`, before re-chunking a file, the system checks if the old hash matches the new hash. If so, it gracefully skips the file.
*   **Why SHA-256**: Cryptographically secure, eliminating the MD5 collision risk.

---

## Part 7 — Chunking

We use the `AutoTokenizer` associated with `sentence-transformers/all-MiniLM-L6-v2`.
*   **Max tokens**: 256
*   **Overlap**: 50 tokens
*   **Why overlap**: If a sentence is cut in half at exactly the 256th token, the semantic meaning is lost. Overlapping by 50 tokens ensures the "context glue" between the end of chunk A and the start of chunk B is preserved.

**Example**:
Document: `A B C D E F`
Tokens: `[1, 2, 3, 4, 5, 6]` (max 3, overlap 1)
Chunk 1: `A B C`
Chunk 2: `C D E`
Chunk 3: `E F`

---

## Part 8 — Embeddings

An embedding is a list of floating-point numbers that represents the semantic meaning of a piece of text. 
We use `sentence-transformers/all-MiniLM-L6-v2`. "MiniLM" is a distilled language model. "L6" means 6 transformer layers. "v2" outputs exactly 384 numbers. 
*   **Why not load for every query?**: Loading a PyTorch model into CPU memory is incredibly slow (taking seconds). The `LocalEmbedder` class loads it once lazily (`if self._model is None:`) and keeps it in memory for the life of the worker process, making subsequent encoding calls near-instantaneous.

---

## Part 9 — Temporary JSONB → Native pgvector Migration

Historically, Phase 6 initially built the tables using `postgresql.JSONB`. This was because native pgvector required system-level extensions. 

1.  **Temporary schema**: `document_chunk.embedding` was a `JSONB` list of floats (`bb220ed50f98_repository_indexing_temporary_jsonb_.py`).
2.  **Why unacceptable**: JSONB cannot perform fast mathematical cosine distance searches in SQL. Python would have had to load thousands of vectors into RAM and compute math manually, which is extremely slow.
3.  **Migration `f2a7b8f58af8`**:
    We created a new Alembic migration that runs:
    `CREATE EXTENSION IF NOT EXISTS vector`
    `ALTER TABLE document_chunk ALTER COLUMN embedding TYPE vector(384) USING (embedding::text::vector)`
4.  **Why a new migration instead of rewriting?**: In production environments, once a migration is applied (JSONB), you must create a new forward migration to transform the data, even if it's empty in development. 

---

## Part 10 — PostgreSQL + pgvector Internal Understanding

*   **vector type**: pgvector introduces a first-class `vector` datatype to PostgreSQL.
*   **vector(384)**: Strictly enforces that exactly 384 dimensions are inserted.
*   **cosine distance**: Represents the angle difference between two vectors. A smaller angle (lower distance) means higher semantic similarity.
*   **Integration**: SQLAlchemy talks to the database using strings/bytes. The `pgvector.sqlalchemy` plugin intercepts Python lists, casts them as PostgreSQL vector arrays `[0.1, 0.2...]`, and saves them to disk optimally.

---

## Part 11 — Database Model

**Relationships**:
`Repository` (1) → (Many) `Document` (1) → (Many) `DocumentChunk`

**Primary / Foreign Keys**:
*   `Document.repository_id` references `Repository.id` (ON DELETE CASCADE).
*   `DocumentChunk.document_id` references `Document.id` (ON DELETE CASCADE).
*   `DocumentChunk.repository_id` references `Repository.id`.

**Why is repository_id on the Chunk?**: This denormalization is intentional. It allows us to execute vector searches directly on the `document_chunk` table using an indexed `repository_id` WHERE clause, without having to execute an expensive SQL JOIN to the `document` table on every single vector similarity calculation.

---

## Part 12 — Phase 7 Overview

### Phase 7 — Repository-Isolated Vector Retrieval

Phase 6 handled "Create and store vectors." Phase 7 implements "Use vectors to find relevant chunks." Phase 7 introduces the `RAGRetriever`, which accepts a text query, converts it into an embedding, and finds the mathematically closest chunks inside the database securely.

---

## Part 13 — Phase 7 End-to-End Retrieval Flow

```text
User/application
      ↓
RAGRetriever.search(repository_id=1, query_text="how to login", top_k=5)
      ↓
LocalEmbedder.embed_chunks(["how to login"])
      ↓
query_embedding (384 float array)
      ↓
SQLAlchemy Statement compilation
      ↓
WHERE DocumentChunk.repository_id = 1
      ↓
pgvector cosine distance ( embedding <=> query_embedding )
      ↓
ORDER BY distance LIMIT 5
      ↓
Mapped to RetrievalResult
      ↓
caller
```

---

## Part 14 — Retriever Code Deep Dive

`backend/app/rag/retriever.py`
```python
distance = DocumentChunk.embedding.cosine_distance(query_embedding)

stmt = (
    select(DocumentChunk, Document, distance.label("distance"))
    .join(Document, DocumentChunk.document_id == Document.id)
    .where(DocumentChunk.repository_id == repository_id)
    .order_by(distance)
    .limit(top_k)
)
```
*   **Validation**: Ensures `top_k` is between 1 and 20.
*   **SQL Isolation**: `.where(DocumentChunk.repository_id == repository_id)`
    *   *Why Python filtering is wrong*: `results = all_chunks; filter(repo_id)` requires downloading millions of vectors into RAM, computing Python math, and dropping 99% of them. It is slow, wastes memory, and risks leaking data if the Python filter has a bug. SQL filtering executes efficiently at the disk level.

---

## Part 15 — Cosine Retrieval

`DocumentChunk.embedding.cosine_distance(query_embedding)`
*   **Left side**: The stored column inside PostgreSQL.
*   **Right side**: The `[0.01, 0.5, ...]` literal array we generated from the query text.
*   **SQL generated**: `document_chunk.embedding <=> '[0.01, ...]'`
*   **Nearest**: Lower distance means the angle between the vectors is smaller (more similar). Therefore `ORDER BY distance ASC` puts the best matches at index 0.

---

## Part 16 — top_k

*   **Why**: We only want the 5 most relevant chunks to feed to the LLM context window.
*   **Validation limits**: `MAX_TOP_K = 20`.
*   **Behavior**: 
    *   `top_k = 5`: Limit 5 chunks.
    *   `top_k = 0`: Raises ValueError.
    *   `top_k = -1`: Raises ValueError.
    *   `top_k = 5000`: Raises ValueError (protects against unbounded DB/memory spikes).

---

## Part 17 — Repository Isolation

This is the most critical security feature of RepoMind.
`.where(DocumentChunk.repository_id == repository_id)`

Because this is evaluated *before* the `ORDER BY` and `LIMIT` clauses, PostgreSQL completely ignores rows belonging to other repositories.
If `Repo A` contains text that is 99% similar to the query, but the user requested `Repo B`, the pgvector extension will never even calculate the cosine distance for the `Repo A` chunks. This mathematically guarantees cross-tenant data isolation.

---

## Part 18 — Phase 7 Result Object

```python
class RetrievalResult(BaseModel):
    chunk_id: int          # The DB PK of the chunk
    document_id: int       # The parent document PK
    repository_id: int     # Security proof of context
    text: str              # The actual markdown content to feed to the LLM
    distance: float        # How confident the system is in the match
    path: str              # The file path (e.g. docs/api.md) for LLM citations
```
Phase 8 (LLM integration) will take the `text` and `path` from these objects and inject them into the final prompt.

---

## Part 19 — Testing Architecture

*   **repomind_test**: The dedicated testing database.
*   **repomind**: The development database.
*   **conftest.py Identity Guard**: 
    ```python
    db_name = conn.execute(text("SELECT current_database()")).scalar()
    if db_name != "repomind_test": pytest.exit(...)
    ```
    This function prevents tests from accidentally wiping out the local development database by actively querying PostgreSQL for its name before yielding any sessions.
*   **Cleanup**: Tables are dynamically deleted and recreated between test sessions to ensure deterministic states.

---

## Part 20 — Phase 7 Test-by-Test Walkthrough

### Test B — test_repository_isolation
*   **Purpose**: Proves SQL boundary enforcement.
*   **Setup**: Seeds Repos A and B with incredibly similar text ("fastAPI", "python styling").
*   **Input**: Query "explicit instruction python styling fastAPI" requesting `repo_a_id`.
*   **Expected**: Returns ONLY chunks from Repo A, despite Repo B chunks being a near-perfect vector match.
*   **Bug caught**: If someone removed the `.where()` clause and filtered in Python, or missed the filter entirely, this test would fail immediately because Repo B chunks would bleed into the result set.

### Test E — test_embedding_dimension
*   **Purpose**: Proves the local embedder outputs strictly 384-length float lists, protecting against pgvector schema crashes.

---

## Part 21 — Complete Example

1. **GitHub**: Repo `frontend-ui` has file `auth.md`.
2. **Phase 6 Loader**: Downloads `auth.md` string.
3. **Phase 6 Chunker**: Splits `auth.md` into 3 overlapping strings.
4. **Phase 6 Embedder**: Passes 3 strings to MiniLM. Receives three 384-float arrays.
5. **Phase 6 DB**: Saves 3 rows to `document_chunk` in PostgreSQL.
6. **User** asks: "How does auth work?" (in context of `frontend-ui`).
7. **Phase 7 Embedder**: Encodes "How does auth work?" -> 1 query array.
8. **Phase 7 Retriever**: Generates `SELECT ... <=> query_array WHERE repo_id = X ORDER BY distance LIMIT 5`.
9. **PostgreSQL**: Returns the single `DocumentChunk` closest to the query.
10. **RepoMind**: Wraps it in `RetrievalResult`.

---

## Part 22 — Commands

*   `uvicorn backend.app.main:app --reload`: Starts the FastAPI development server.
*   `alembic upgrade head`: Applies migrations to the DB.
*   `pytest backend/tests/test_rag_retriever.py`: **SAFE TEST DATABASE COMMAND**. Runs focused RAG retrieval tests against `repomind_test`.
*   `pytest backend/tests`: **SAFE TEST DATABASE COMMAND**. Runs full backend suite against `repomind_test`.
*   `git diff` / `git status`: Verifies uncommitted changes and tracked/untracked states.

---

## Part 23 — Git Checkpoints

*   **`368a997` feat(rag): complete native pgvector Phase 6**: This milestone established the DB architecture, verified the `all-MiniLM` model, and finalized the JSONB -> native vector migration.
*   **`e4088a3` feat(rag): implement repository-isolated vector retrieval**: This milestone implemented the search mechanic (`RAGRetriever`), bounding it securely by `repository_id` and locking it down with dedicated pgvector tests.

---

## Part 24 — What is NOT Implemented Yet

Phase 6 and Phase 7 intentionally **DO NOT** implement:
*   **LLM Integration / Claude API**: Calling Anthropic Claude and injecting context is explicitly Phase 8.
*   **Query Derivation**: Extracting the search query from a GitHub PR diff is Phase 8/9.
*   **Findings / Review_Run**: Storing the results of a review.
*   **Static Analysis**: Linters are Phase 9.
*   **Background Jobs / Webhooks**: The orchestration of these pipelines triggered by GitHub Webhooks belongs to later phases.
*   **API Endpoints**: No FastAPI routes expose this retrieval yet.

---

## Part 25 — Common Misunderstandings

# Things I Must Not Misunderstand
1. **Embedding ≠ similarity search**: The embedder makes the vector. pgvector performs the search.
2. **Phase 6 ≠ Phase 7**: Phase 6 writes. Phase 7 reads.
3. **pgvector is not an external vector database**: It lives entirely inside our existing PostgreSQL instance.
4. **cosine distance is not cosine similarity**: Distance approaches 0 for identical vectors. Similarity approaches 1. Our SQL uses distance.
5. **repository isolation is a database query constraint**: It is NOT a python filter.
6. **top_k is not the embedding dimension**: Top K (e.g. 5) is rows returned. Dimension (384) is the length of the vector.
7. **chunk overlap is not duplicate documents**: It's a sliding window of context to preserve meaning.
8. **Phase 7 does not derive an LLM query from a PR diff**: It strictly accepts a ready-made text query.

---

## Part 26 — Developer Mental Model

**PHASE 6 (WRITE)**:
Repository → load files → filter files → create documents → chunk documents → embed chunks → store vectors

**PHASE 7 (READ)**:
query text → embed query → filter repository → compare vectors → cosine distance → sort nearest first → take top_k → return chunks

**Technical Translation**: Phase 6 transforms raw external textual data into normalized semantic database rows via deterministic NLP chunking. Phase 7 executes constrained mathematical distance calculations in SQL against those rows to surface relevant textual context.

---

## Part 27 — Glossary

*   **RAG**: Retrieval-Augmented Generation. Finding facts to give to an LLM.
*   **Embedding**: Text transformed into an array of floats.
*   **Vector**: The actual float array.
*   **Dimension**: The length of the array (384).
*   **Chunk**: A subset of a document's text.
*   **Tokenizer**: Converts strings into integer ID mapping for ML models.
*   **pgvector**: The C-extension for Postgres adding native vector similarity.
*   **Cosine Distance**: Metric measuring angle difference between vectors.
*   **top_k**: The upper limit of rows to return from the database.

---

## Verification Snapshot

*   **Current Alembic head**: `f2a7b8f58af8` (native pgvector migration)
*   **Current relevant commit**: `e4088a3`
*   **Backend test count**: 28 tests passing
*   **Phase 7 test count**: 6 tests (`test_rag_retriever.py`)
*   **Embedding model**: `sentence-transformers/all-MiniLM-L6-v2`
*   **Embedding dimension**: 384
*   **Chunk size**: 256 max tokens
*   **Chunk overlap**: 50 tokens
*   **Vector storage type**: `vector(384)`
*   **Test database**: `repomind_test`
*   **Development database**: `repomind`
*   **Confirmation**: Phase 8 (LLM implementation) was definitively NOT implemented.

---

## Learning Checklist

- [ ] I understand why repositories are indexed.
- [ ] I understand the Document → Chunk → Embedding relationship.
- [ ] I understand how GitHub files become database rows.
- [ ] I understand how MiniLM creates a 384-dimensional vector.
- [ ] I understand why pgvector is needed.
- [ ] I understand cosine distance.
- [ ] I understand repository-level SQL isolation.
- [ ] I understand top_k.
- [ ] I understand the Phase 6 pipeline.
- [ ] I understand the Phase 7 retrieval pipeline.
- [ ] I understand the six retrieval tests.
- [ ] I understand why `repomind_test` exists.
- [ ] I understand the JSONB → pgvector migration.
- [ ] I understand what Phase 8 will consume from Phase 7.
