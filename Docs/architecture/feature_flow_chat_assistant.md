# 11 — Feature Flow: AI Chat Assistant

## Feature Summary
The AI chat assistant provides a conversational interface for engineers to query their repository's codebase. Each chat session is **scoped to a context** (PR, repository, or review run) and all answers are grounded in actual repository evidence via RAG retrieval. The assistant cannot answer questions outside its indexed repository context.

---

## End-to-End Flow

### 1. Create a Chat Session

| Step | Where | What Happens |
|---|---|---|
| User opens Chat tab | `ChatPage.jsx` | Calls `chatApi.createSession({organization_id, context_type, context_id})` |
| API call | `lib/api.js:118` | `POST /chat/sessions` with `{organization_id, context_type, context_id}` |
| Route | `backend/app/chat/router.py` | `POST /chat/sessions` → `create_session()` |
| `create_session()` | `backend/app/chat/service.py:32` | Creates `ChatSession(user_id, organization_id, context_type, context_id)` |
| DB write | `chat_session` table | Committed, returns session with ID |

Context types:
- `pr` — scoped to a pull request (accesses PR review data)
- `repository` — scoped to a repository's indexed docs
- `review` — scoped to a specific review run

---

### 2. Send a Message

| Step | Where | What Happens |
|---|---|---|
| User types message + hits send | `ChatPage.jsx` | `chatApi.sendMessage(sessionId, orgId, {message, repository_id})` |
| API call | `lib/api.js:131` | `POST /chat/sessions/{sessionId}/messages?organization_id={orgId}` |
| Route | `backend/app/chat/router.py` | Resolves session, verifies ownership, calls `send_message()` |
| `send_message()` | `backend/app/chat/service.py:75` | Main chat logic |

---

### 3. RAG Context Retrieval

File: `backend/app/chat/service.py` → `send_message()`

```python
retriever = RAGRetriever(db=db)
chunks = []
if repository_id is not None:
    chunks = retriever.search(
        repository_id=repository_id,
        query_text=message,
        top_k=5,
        chunk_types=["documentation", "source_code", "test_code"]
    )
```

`retriever.search()` in `backend/app/rag/retriever.py`:
1. Embeds `message` using `LocalEmbedder` (all-MiniLM-L6-v2, 384-dim)
2. Queries `document_chunk` table: `ORDER BY embedding <=> query_vector LIMIT 5`
3. Filter: `repository_id == repository_id` (isolation enforced)
4. Filter: `chunk_type IN ["documentation", "source_code", "test_code"]`
5. Returns `List[RetrievalResult]`

---

### 4. Build Evidence + System Prompt

```python
evidence_parts = []
sources = []
for c in chunks:
    evidence_parts.append(f"--- File: {c.path} ({c.chunk_type}) ---\n{c.text}\n")
    sources.append({"type": c.chunk_type, "path": c.path})

evidence_text = "\n".join(evidence_parts) if evidence_parts else "No relevant repository context found."

system_prompt = SYSTEM_CHAT_PROMPT.format(
    context_type=session.context_type,
    evidence=evidence_text
)
```

`SYSTEM_CHAT_PROMPT` template:
```
You are RepoMind, an expert engineering intelligence assistant.
You are currently engaged in a conversation scoped to a {context_type}.

Always base your answers on the provided Evidence below...
If the Evidence does not contain the answer, say "I don't have enough information..."
Never hallucinate file names, functions, or logic that isn't provided.

Evidence:
{evidence}
```

Note: The evidence is embedded inside the system prompt here (unlike the review pipeline where system/user content are strictly separated). This is a different prompt architecture for chat vs. review.

---

### 5. Build User Content with History

```python
history = get_session_messages(db, session_id, user_id)   # Last 5 messages
history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-5:]])
user_content = f"Chat History:\n{history_text}\n\nUser Question:\n{message}"
```

---

### 6. Call LLM

```python
response_content = provider.complete(system_prompt, user_content)
is_grounded = bool(chunks)   # True if RAG returned any chunks
```

Uses the same `LLMProvider` protocol as the review pipeline. The provider is injected via FastAPI dependency.

---

### 7. Persist Messages

```python
# Save user message
user_msg = ChatMessage(session_id=session_id, role="user", content=message)
db.add(user_msg)

# Save assistant message
assistant_msg = ChatMessage(
    session_id=session_id,
    role="assistant",
    content=response_content,
    sources=sources,         # JSONB: [{type, path}, ...]
    is_grounded=is_grounded
)
db.add(assistant_msg)

session.last_message_at = datetime.now(timezone.utc)
db.commit()
```

---

### 8. Return Response

Route returns `ChatMessage` (assistant message), including `sources` and `is_grounded`. Frontend displays:
- The assistant's response text
- Source citations (file paths + types)
- A "grounded" / "not grounded" indicator

---

## Data Models

File: `backend/app/chat/models.py`

### `ChatSession`

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → `user.id` CASCADE | Session owner |
| `context_type` | String(50) | `pr` / `repository` / `review` |
| `context_id` | Integer | ID of the scoped resource |
| `organization_id` | FK → `organization.id` CASCADE | For permission scoping |
| `created_at` | DateTime(tz) | |
| `last_message_at` | DateTime(tz) nullable | Updated on each message |

### `ChatMessage`

| Column | Type | Description |
|---|---|---|
| `id` | Integer PK | |
| `session_id` | FK → `chat_session.id` CASCADE | |
| `role` | String(20) | `user` / `assistant` |
| `content` | Text | Message text |
| `sources` | JSONB nullable | For assistant: `[{type, path}]` |
| `is_grounded` | Boolean nullable | Whether RAG found any context |
| `created_at` | DateTime(tz) | |

---

## API Endpoints

| Method | URL | Purpose |
|---|---|---|
| `POST` | `/chat/sessions` | Create a new session |
| `GET` | `/chat/sessions?organization_id=&context_type=&context_id=` | List sessions for a context |
| `GET` | `/chat/sessions/{id}/messages?organization_id=` | Get all messages in session |
| `POST` | `/chat/sessions/{id}/messages?organization_id=` | Send a message (triggers RAG + LLM) |

---

## Key Files

| File | Location | Role |
|---|---|---|
| `router.py` | `backend/app/chat/router.py` | All chat API endpoints |
| `service.py` | `backend/app/chat/service.py` | `create_session()`, `send_message()`, `get_sessions()`, `get_session_messages()` |
| `models.py` | `backend/app/chat/models.py` | `ChatSession`, `ChatMessage` SQLAlchemy models |
| `retriever.py` | `backend/app/rag/retriever.py` | `RAGRetriever.search()` — vector similarity search |
| `api.js` (chatApi) | `frontend/src/lib/api.js:117-135` | `chatApi.createSession/getSessions/getHistory/sendMessage` |
| `ChatPage.jsx` | `frontend/src/pages/ChatPage.jsx` | Chat UI |

---

## Grounding Rule

If no repository is indexed (no `document_chunk` rows for `repository_id`):
- `chunks = []`
- `is_grounded = False`
- `evidence_text = "No relevant repository context found."`
- LLM is instructed to say it doesn't have enough information

This prevents hallucinations about repositories that haven't been indexed yet.

---

## Permission Required

Route requires: `Permission.CHAT_USE`

Roles with `CHAT_USE`: `developer`, `reviewer`, `tech_lead`, `org_admin` (all non-read-only roles).

`read_only` users cannot use the chat assistant.
