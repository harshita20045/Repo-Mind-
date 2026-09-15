"""
RAG context assembly and deterministic query derivation — Phase 8.

Query derivation is intentionally non-LLM (no additional LLM call).
The strategy is:
  1. Extract changed file paths from unified diff `+++ b/<path>` headers.
  2. Combine with PR title.
  3. Truncate to a safe length for the embedder (not silently — see note).

Diff size:
  The authoritative docs do not establish a hard character limit on the diff
  passed to the LLM. The full diff is preserved and passed to build_user_content.
  The QUERY used for RAG search is derived and truncated only to fit the
  embedder's token budget — this is separate from and does not affect the diff
  passed to the LLM prompt.
"""
import re
from typing import List

from backend.app.rag.retriever import RAGRetriever, RetrievalResult

# Maximum characters for the RAG search query (not the LLM diff input).
# The MiniLM tokenizer accepts up to 256 tokens ≈ ~1000 characters.
# 500 is a conservative, documented bound that fits well within the model limit.
_MAX_QUERY_CHARS = 500


def derive_query_from_diff(pr_title: str, diff: str) -> str:
    """
    Deterministically derive a RAG search query from the PR title and diff.

    Strategy (non-LLM):
      - Extract `+++ b/<path>` lines from the unified diff headers.
      - Strip the `b/` prefix to get clean relative paths.
      - Combine PR title with changed paths as a space-separated string.
      - Truncate to _MAX_QUERY_CHARS characters.

    This ensures the query is:
      - Deterministic (same input → same query, always)
      - Repository-agnostic (paths, not content)
      - Safe (no repository source code enters the query string directly)
      - Not dependent on any additional LLM call

    Args:
        pr_title: The PR title from the pull_request DB record.
        diff:     The unified diff string from GitHub.

    Returns:
        A query string for RAGRetriever.search().
        Returns pr_title alone if the diff contains no parseable path headers.
    """
    # Extract changed file paths from diff headers (+++  b/<path>)
    paths = re.findall(r'^\+\+\+ b/(.+)$', diff, flags=re.MULTILINE)

    # Build query: title first, then unique paths
    seen = set()
    unique_paths = []
    for p in paths:
        if p not in seen and p != "/dev/null":
            seen.add(p)
            unique_paths.append(p)

    parts = [pr_title.strip()] + unique_paths
    query = " ".join(parts)

    # Truncate only for the embedder's token budget; this is NOT applied to the
    # diff sent to the LLM.
    if len(query) > _MAX_QUERY_CHARS:
        query = query[:_MAX_QUERY_CHARS]

    return query.strip() or pr_title


def retrieve_context(
    retriever: RAGRetriever,
    repository_id: int,
    query: str,
    top_k: int = 5,
) -> List[RetrievalResult]:
    """
    Retrieve the top-k relevant document chunks for a repository.

    repository_id is derived from the PullRequest → Repository relationship
    within review_service.run_review. It is never accepted from a client
    request parameter.

    Phase 7's RAGRetriever enforces SQL-level repository isolation:
      WHERE document_chunk.repository_id = repository_id
    This guarantee is preserved here.

    Args:
        retriever:     A RAGRetriever instance bound to the current DB session.
        repository_id: The repository ID derived from the PR's repository.
        query:         The deterministically derived query string.
        top_k:         Number of chunks to retrieve (default 5, max 20).

    Returns:
        List of RetrievalResult objects (may be empty if no chunks indexed).
    """
    return retriever.search(repository_id=repository_id, query_text=query, top_k=top_k)
