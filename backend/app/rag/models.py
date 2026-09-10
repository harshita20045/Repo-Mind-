import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.db import Base

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
    # Temporary JSONB storage for 384-dimensional embedding bridge
    embedding = Column(JSONB, nullable=False)
    chunk_index = Column(Integer, nullable=False)
