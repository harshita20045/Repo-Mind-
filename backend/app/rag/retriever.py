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

class RAGRetriever:
    """
    Service for retrieving RAG document chunks via vector similarity search.
    Enforces strict repository isolation.
    """
    MAX_TOP_K = 20

    def __init__(self, db: Session, embedder: Optional[LocalEmbedder] = None):
        self.db = db
        # Reuse existing LocalEmbedder if provided, else instantiate
        self.embedder = embedder or LocalEmbedder()

    def search(self, repository_id: int, query_text: str, top_k: int = 5) -> List[RetrievalResult]:
        """
        Search for the top_k most similar document chunks in a repository.
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
            .order_by(distance)
            .limit(top_k)
        )

        results = self.db.execute(stmt).all()

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
                    path=doc.path
                )
            )

        return retrieval_results
