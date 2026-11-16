from typing import List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.rag.models import Document, DocumentChunk
from backend.app.rag.embedder import LocalEmbedder

class RetrievalResult(BaseModel):
    chunk_id: int
    document_id: int
    repository_id: int
    text: str
    distance: float
    path: str
    chunk_type: str = "documentation"

class RAGRetriever:
    """
    Service for retrieving RAG document chunks via vector similarity search.
    Enforces strict repository isolation and supports code-aware filtering.
    """
    MAX_TOP_K = 20

    def __init__(self, db: Session, embedder: Optional[LocalEmbedder] = None):
        self.db = db
        # Reuse existing LocalEmbedder if provided, else instantiate
        self.embedder = embedder or LocalEmbedder()

    def search(
        self, 
        repository_id: int, 
        query_text: str, 
        top_k: int = 5,
        chunk_types: Optional[List[str]] = None,
        file_path_pattern: Optional[str] = None,
    ) -> List[RetrievalResult]:
        """
        Search for the top_k most similar document chunks in a repository.
        Optionally filter by chunk_types (e.g., ["documentation", "source_code", "class", "function"])
        or file_path_pattern.
        """
        # Validate top_k
        if top_k <= 0 or top_k > self.MAX_TOP_K:
            raise ValueError(f"top_k must be between 1 and {self.MAX_TOP_K}, got {top_k}")

        # Empty query
        if not query_text or not query_text.strip():
            return []

        # Generate embedding for the query
        embeddings = self.embedder.embed_chunks([query_text])
        if not embeddings:
            return []
            
        query_embedding = embeddings[0]

        # Construct cosine distance expression
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)

        # Build SQL query with strict repository isolation
        stmt = (
            select(DocumentChunk, Document, distance.label("distance"))
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.repository_id == repository_id)
        )
        
        # Apply chunk_type filter if specified
        if chunk_types:
            stmt = stmt.where(DocumentChunk.chunk_type.in_(chunk_types))
        if file_path_pattern:
            stmt = stmt.where(Document.path.ilike(f"%{file_path_pattern}%"))
            
        stmt = stmt.order_by(distance).limit(top_k)

        try:
            with self.db.begin_nested():
                results = self.db.execute(stmt).all()
        except Exception as e:
            if "operator does not exist" in str(e) or "<=>" in str(e) or "type modifier is not allowed" in str(e):
                stmt_fallback = (
                    select(DocumentChunk, Document)
                    .join(Document, DocumentChunk.document_id == Document.id)
                    .where(DocumentChunk.repository_id == repository_id)
                )
                if chunk_types:
                    stmt_fallback = stmt_fallback.where(DocumentChunk.chunk_type.in_(chunk_types))
                if file_path_pattern:
                    stmt_fallback = stmt_fallback.where(Document.path.ilike(f"%{file_path_pattern}%"))
                rows = self.db.execute(stmt_fallback).all()
                import numpy as np
                q_vec = np.array(query_embedding, dtype=float)
                q_norm = np.linalg.norm(q_vec)
                scored = []
                for chunk, doc in rows:
                    c_emb = chunk.embedding
                    if isinstance(c_emb, str):
                        import json
                        c_emb = json.loads(c_emb)
                    c_vec = np.array(c_emb, dtype=float)
                    c_norm = np.linalg.norm(c_vec)
                    if q_norm > 0 and c_norm > 0:
                        dist = 1.0 - (float(np.dot(q_vec, c_vec)) / float(q_norm * c_norm))
                    else:
                        dist = 1.0
                    scored.append((chunk, doc, dist))
                scored.sort(key=lambda x: x[2])
                results = scored[:top_k]
            else:
                raise

        # Map to typed schema
        retrieval_results = []
        for chunk, doc, dist in results:
            retrieval_results.append(
                RetrievalResult(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    repository_id=chunk.repository_id,
                    text=chunk.text,
                    distance=float(dist),
                    path=doc.path,
                    chunk_type=chunk.chunk_type
                )
            )

        return retrieval_results
