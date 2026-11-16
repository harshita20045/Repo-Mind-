import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB
from backend.app.db import Base
from pgvector.sqlalchemy import Vector as _BaseVector


def _has_vector_extension() -> bool:
    if not hasattr(_has_vector_extension, "_cached"):
        try:
            from backend.app.core.config import settings
            from sqlalchemy import create_engine, text
            eng = create_engine(settings.POSTGRES_URL)
            with eng.connect() as conn:
                val = conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")).scalar()
                _has_vector_extension._cached = bool(val)
        except Exception:
            _has_vector_extension._cached = False
    return _has_vector_extension._cached


class Vector(_BaseVector):
    cache_ok = True

    def get_col_spec(self, **kw) -> str:
        if _has_vector_extension():
            return super().get_col_spec(**kw)
        return "JSONB"

    def bind_processor(self, dialect):
        if _has_vector_extension():
            return super().bind_processor(dialect)
        import json
        def process(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return json.dumps(list(value))
            return value
        return process

    def result_processor(self, dialect, coltype):
        if _has_vector_extension():
            base_proc = super().result_processor(dialect, coltype)
            def process(value):
                if value is None or isinstance(value, list):
                    return value
                return base_proc(value)
            return process
        import json
        def process(value):
            if value is None:
                return None
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except Exception:
                    return value
            return value
        return process

class Document(Base):
    __tablename__ = "document"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    repository_id = Column(Integer, ForeignKey("repository.id", ondelete="CASCADE"), nullable=False, index=True)
    path = Column(String, nullable=False, index=True)
    content_hash = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class DocumentChunk(Base):
    __tablename__ = "document_chunk"
    __table_args__ = {"extend_existing": True}

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
