import sys
sys.path.insert(0, ".")
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from backend.app.core.config import settings
from sqlalchemy.engine.url import make_url

url = make_url(settings.POSTGRES_URL).set(database="repomind_test").render_as_string(hide_password=False)
eng = create_engine(url)
Session = sessionmaker(bind=eng)

# Import models
from backend.app.auth.models import Organization
from backend.app.organizations.models import Repository, Project
from backend.app.rag.models import Document, DocumentChunk

with Session() as s:
    doc = Document(repository_id=1, path="test.md", content_hash="h1")
    s.add(doc)
    s.flush()
    chunk = DocumentChunk(
        document_id=doc.id,
        repository_id=1,
        text="Sample text",
        embedding=[0.1] * 384,
        chunk_index=0,
    )
    s.add(chunk)
    s.commit()
    loaded = s.query(DocumentChunk).filter_by(id=chunk.id).first()
    print("Loaded chunk id:", loaded.id, "embedding len:", len(loaded.embedding))
