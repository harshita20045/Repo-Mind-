from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from backend.app.rag.models import Document, DocumentChunk

class RAGRepository:
    """
    Persistence layer for RAG documents and chunks.
    Isolates the underlying storage representation (JSONB) from the rest of the application.
    """
    def __init__(self, db: Session):
        self.db = db

    def get_document_by_path(self, repository_id: int, path: str) -> Optional[Document]:
        """Fetch an existing document by its repository and path."""
        stmt = select(Document).where(
            Document.repository_id == repository_id,
            Document.path == path
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_document_chunks(self, repository_id: int, document_id: int) -> List[DocumentChunk]:
        """Fetch all chunks for a document, scoped by repository."""
        stmt = select(DocumentChunk).where(
            DocumentChunk.repository_id == repository_id,
            DocumentChunk.document_id == document_id
        ).order_by(DocumentChunk.chunk_index)
        return list(self.db.execute(stmt).scalars().all())

    def delete_document_chunks(self, repository_id: int, document_id: int) -> None:
        """Delete all chunks for a specific document."""
        stmt = delete(DocumentChunk).where(
            DocumentChunk.repository_id == repository_id,
            DocumentChunk.document_id == document_id
        )
        self.db.execute(stmt)

    def delete_document(self, repository_id: int, document_id: int) -> None:
        """Delete a document and its chunks (via cascade)."""
        stmt = delete(Document).where(
            Document.repository_id == repository_id,
            Document.id == document_id
        )
        self.db.execute(stmt)

    def save_document(self, repository_id: int, path: str, content_hash: str) -> Document:
        """Create or update a document record."""
        doc = self.get_document_by_path(repository_id, path)
        if doc:
            doc.content_hash = content_hash
        else:
            doc = Document(
                repository_id=repository_id,
                path=path,
                content_hash=content_hash
            )
            self.db.add(doc)
        
        self.db.flush()  # Ensure document gets an ID
        return doc

    def save_chunks(
        self, 
        repository_id: int, 
        document_id: int, 
        chunks: List[Tuple[str, List[float]]]
    ) -> None:
        """
        Save a list of chunk texts and their corresponding embedding vectors.
        Isolates the JSONB temporary storage mechanism.
        
        Args:
            chunks: A list of tuples (chunk_text, embedding_vector)
        """
        # Ensure stale chunks are removed before saving new ones
        self.delete_document_chunks(repository_id, document_id)
        
        for idx, (text, embedding) in enumerate(chunks):
            chunk = DocumentChunk(
                document_id=document_id,
                repository_id=repository_id,
                text=text,
                embedding=embedding,  # Stored as JSONB
                chunk_index=idx
            )
            self.db.add(chunk)
        self.db.flush()
