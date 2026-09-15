import pytest
from unittest.mock import MagicMock
from sqlalchemy import text
from backend.app.rag.loader import DocumentLoader
from backend.app.rag.chunker import TextChunker
from backend.app.rag.embedder import LocalEmbedder, EmbedderError
from backend.app.rag.repository import RAGRepository
from backend.app.rag.models import Document, DocumentChunk
from backend.app.rag.service import index_repository
from backend.app.organizations.models import Project, Repository, GithubConnection
from backend.app.auth.models import Organization
from backend.app.github.encryption import encrypt_token

def test_loader_exclusions():
    client = MagicMock()
    loader = DocumentLoader(client, "owner", "repo", "sha")
    
    assert loader._should_exclude_path("node_modules/test.md") is True
    assert loader._should_exclude_path("vendor/docs/test.md") is True
    assert loader._should_exclude_path("generated/api.md") is True
    assert loader._should_exclude_path(".git/config") is True
    assert loader._should_exclude_path(".env") is True
    assert loader._should_exclude_path(".env.local") is True
    assert loader._should_exclude_path("secret.pem") is True
    assert loader._should_exclude_path("key.key") is True
    
    # Must only include markdown
    assert loader._should_exclude_path("src/main.py") is True
    assert loader._should_exclude_path("README.md") is False
    assert loader._should_exclude_path("docs/setup.md") is False

def test_loader_hashing():
    client = MagicMock()
    loader = DocumentLoader(client, "owner", "repo", "sha")
    
    h1 = loader.hash_content("hello world")
    h2 = loader.hash_content("hello world")
    h3 = loader.hash_content("hello world 2")
    
    assert h1 == h2
    assert h1 != h3
    assert len(h1) == 64  # SHA-256 hex digest length

def test_chunker_determinism_and_overlap():
    chunker = TextChunker()
    text = "word " * 600
    chunks = chunker.chunk_text(text)
    
    assert len(chunks) > 1
    # Check max tokens
    for chunk in chunks:
        tokens = chunker.tokenizer.encode(chunk, add_special_tokens=False)
        assert len(tokens) <= 256

def test_embedder_validation():
    embedder = LocalEmbedder()
    res = embedder.embed_chunks(["hello world"])
    assert len(res) == 1
    assert len(res[0]) == 384
    assert isinstance(res[0][0], float)

def test_persistence_and_idempotency(db_session):
    # Setup mock data
    org = Organization(name="Test Org")
    db_session.add(org)
    db_session.commit()
    project = Project(organization_id=org.id, name="Test Proj")
    db_session.add(project)
    db_session.commit()
    
    repo1 = Repository(project_id=project.id, github_owner="owner", github_name="repo1", default_branch="main")
    repo2 = Repository(project_id=project.id, github_owner="owner", github_name="repo2", default_branch="main")
    db_session.add_all([repo1, repo2])
    db_session.commit()
    
    rag_repo = RAGRepository(db_session)
    repo_id_1 = repo1.id
    repo_id_2 = repo2.id
    
    # 1. Save document
    doc1 = rag_repo.save_document(repo_id_1, "test.md", "hash1")
    assert doc1.id is not None
    
    # 2. Save chunks
    chunks = [("chunk1 text", [0.1] * 384), ("chunk2 text", [0.2] * 384)]
    rag_repo.save_chunks(repo_id_1, doc1.id, chunks)
    
    saved_chunks = rag_repo.get_document_chunks(repo_id_1, doc1.id)
    assert len(saved_chunks) == 2
    assert saved_chunks[0].chunk_index == 0
    assert len(saved_chunks[0].embedding) == 384
    
    # 3. Idempotency / Replacement
    # Replace chunks for doc1
    chunks_new = [("new chunk", [0.3] * 384)]
    rag_repo.save_chunks(repo_id_1, doc1.id, chunks_new)
    
    saved_chunks_new = rag_repo.get_document_chunks(repo_id_1, doc1.id)
    assert len(saved_chunks_new) == 1
    assert saved_chunks_new[0].text == "new chunk"
    
    # 4. Isolation
    doc2 = rag_repo.save_document(repo_id_2, "test.md", "hash2")
    chunks_repo2 = [("repo2 chunk", [0.4] * 384)]
    rag_repo.save_chunks(repo_id_2, doc2.id, chunks_repo2)
    
    # Verify repo_id_1 cannot access repo_id_2 chunks
    assert len(rag_repo.get_document_chunks(repo_id_1, doc2.id)) == 0

def test_service_integration(db_session, monkeypatch):
    """Integration test mocking GitHub but hitting real DB and LocalEmbedder."""
    # Ensure test DB
    assert db_session.execute(text("SELECT current_database()")).scalar() == "repomind_test"

    # Setup parent records
    org = Organization(name="Test Org RAG")
    db_session.add(org)
    db_session.commit()
    
    conn = GithubConnection(organization_id=org.id, encrypted_token=encrypt_token("fake_pat"))
    project = Project(organization_id=org.id, name="Test Proj RAG")
    db_session.add(conn)
    db_session.add(project)
    db_session.commit()
    
    repo = Repository(
        project_id=project.id, 
        github_owner="test_owner", 
        github_name="test_repo",
        default_branch="main"
    )
    db_session.add(repo)
    db_session.commit()
    
    # Mock GitHubClient inside service
    from backend.app.rag import service
    
    class FakeClient:
        def __init__(self, pat):
            pass
        def get_repository_tree(self, owner, repo, sha, recursive=True):
            return {
                "tree": [
                    {"path": "docs/test1.md", "type": "blob", "sha": "sha1"},
                    {"path": "docs/test2.md", "type": "blob", "sha": "sha2"}
                ]
            }
        def get_blob_content(self, owner, repo, sha):
            if sha == "sha1":
                return b"This is test document 1. " * 50
            return b"This is test document 2."
            
    monkeypatch.setattr(service, "GitHubClient", FakeClient)
    
    # Run indexing
    index_repository(db_session, repo.id)
    
    # Verify results
    rag_repo = RAGRepository(db_session)
    doc1 = rag_repo.get_document_by_path(repo.id, "docs/test1.md")
    doc2 = rag_repo.get_document_by_path(repo.id, "docs/test2.md")
    
    assert doc1 is not None
    assert doc2 is not None
    
    chunks1 = rag_repo.get_document_chunks(repo.id, doc1.id)
    assert len(chunks1) > 0
    assert len(chunks1[0].embedding) == 384
    
    # Run again to test idempotency (no chunks duplicated)
    index_repository(db_session, repo.id)
    chunks1_after = rag_repo.get_document_chunks(repo.id, doc1.id)
    assert len(chunks1) == len(chunks1_after)
