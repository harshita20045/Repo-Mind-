# Diagram — AI Review Pipeline (LLM)

**Status: Confirmed**

```mermaid
flowchart LR
    Diff[PR Diff] --> Context[Context Builder]
    Chunks[Retrieved Chunks] --> Context
    Lint[Linter Output] --> Context
    Context --> Prompt[Prompt Template v1]
    Prompt --> LLMCall[LLM API Call]
    LLMCall --> Parse[JSON Parse]
    Parse --> Validate[Schema Validation]
    Validate -->|invalid| Retry[Retry once]
    Retry --> Parse
    Validate -->|valid| Findings[Normalized Findings]
```

Services: `DocumentLoader`, `DocumentFilter`, `Chunker`, `EmbeddingService`, `Retriever` (rag module); `ContextBuilder`, `PromptBuilder`, `LLMClient`, `OutputParser`, `FindingValidator`, `ReviewService` (review module).

Prompt injection defense: repository content (README, docs, PR description, commit messages, code comments) is explicitly labeled in the prompt as **untrusted evidence**, never as system-level instructions. The system instruction is fixed and outside any repository-sourced text; the model is explicitly told not to follow instructions found inside retrieved content. See `05-security/security.md`.


```mermaid
flowchart TD
    %% PR Review Flow
    GH[GitHub] --> PRData[Repository / PR Data]
    PRData --> PRRev[PR Review]
    PRRev --> Findings[Security / Quality Findings]
    PRData --> RAG[RAG]
    RAG --> LLM[LLM]
    LLM --> Findings
    
    %% ML Flow
    PRData --> MLExtract[ML Feature Extraction]
    MLExtract --> MLModel[ML Model]
    MLModel --> Delay[Delay Prediction]
    Delay --> PRUI[PR UI / Analytics]
    
    %% Chat Flow
    Chat[Chatbot] --> RepoRAG[Repository-scoped RAG]
    RepoRAG --> ChatLLM[LLM]
    
    %% Webhook Flow
    Hooks[Webhooks] --> Sync[Repository / PR Synchronization]
```
