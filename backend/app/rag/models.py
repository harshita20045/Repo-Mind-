import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.db import Base
from pgvector.sqlalchemy import Vector

class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String, nullable=False, index=True)
    content_hash = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunk"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("document.id", ondelete="CASCADE"), nullable=False, index=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    # Changed to 384 to match local sentence-transformers model (all-MiniLM-L6-v2)
    embedding = Column(Vector(384), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    
    # RepoMind 2.0 extensions
    chunk_type = Column(String(50), nullable=False, server_default="documentation", index=True)
    file_path = Column(String(1024), nullable=True, index=True)
