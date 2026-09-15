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

## Evaluation Comparison (kept separate from production inference)

```mermaid
flowchart LR
    subgraph Production
        PR[PR] --> RAGp[RAG] --> Lintp[Linter] --> LLMp[LLM] --> Findp[Findings]
    end
    subgraph Evaluation
        DS[Answer-key dataset] --> Exp[Experiment runner]
        Exp --> CfgA[Config A: generic LLM]
        Exp --> CfgB[Config B: LLM+linter]
        Exp --> CfgC[Config C: LLM+linter+RAG]
        CfgA --> Metrics[Precision/Recall/F1/Groundedness]
        CfgB --> Metrics
        CfgC --> Metrics
        Metrics --> Store[(evaluation_run)]
    end
```
