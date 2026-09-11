import pytest
from sqlalchemy import text
from backend.app.rag.retriever import RAGRetriever, RetrievalResult
from backend.app.rag.repository import RAGRepository
from backend.app.rag.embedder import LocalEmbedder
from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository

@pytest.fixture
def embedder():
    # Use real embedder for tests to verify integration with sentence-transformers
    return LocalEmbedder()

@pytest.fixture
def setup_test_repos(db_session, embedder):
    """Seed test repositories A and B with chunks for isolation and top_k testing."""
    # Ensure test DB
    assert db_session.execute(text("SELECT current_database()")).scalar() == "repomind_test"
    
    org = Organization(name="RAG Retriever Org")
    db_session.add(org)
    db_session.commit()
    
    project = Project(organization_id=org.id, name="RAG Retriever Proj")
    db_session.add(project)
    db_session.commit()
    
    repo_a = Repository(project_id=project.id, github_owner="owner", github_name="repo_a", default_branch="main")
    repo_b = Repository(project_id=project.id, github_owner="owner", github_name="repo_b", default_branch="main")
    db_session.add_all([repo_a, repo_b])
    db_session.commit()
    
    rag_repo = RAGRepository(db_session)
    
    # ----------------------------------------------------
    # Repo A data
    doc_a = rag_repo.save_document(repo_a.id, "docs/repo_a_guide.md", "hash_a")
    
    # Seed specific relevant chunks
    chunks_a_texts = [
        "This is an explicit instruction for Repo A python styling.",
        "Repo A requires fastAPI and pydantic for routing.",
        "General unrelated text for Repo A.",
        "Random noise chunk 1 in A.",
        "Random noise chunk 2 in A.",
        "Random noise chunk 3 in A.",
        "Random noise chunk 4 in A.",
    ]
    chunks_a_embeddings = embedder.embed_chunks(chunks_a_texts)
    chunks_a = list(zip(chunks_a_texts, chunks_a_embeddings))
    rag_repo.save_chunks(repo_a.id, doc_a.id, chunks_a)
    
    # ----------------------------------------------------
    # Repo B data
    doc_b = rag_repo.save_document(repo_b.id, "docs/repo_b_guide.md", "hash_b")
    
    # Seed chunks that are highly similar to Repo A's chunks to test isolation
    chunks_b_texts = [
        "This is an explicit instruction for Repo B python styling.",
        "Repo B requires fastAPI and pydantic for routing.",
    ]
    chunks_b_embeddings = embedder.embed_chunks(chunks_b_texts)
    chunks_b = list(zip(chunks_b_texts, chunks_b_embeddings))
    rag_repo.save_chunks(repo_b.id, doc_b.id, chunks_b)
    
    return repo_a.id, repo_b.id

def test_relevant_retrieval(db_session, setup_test_repos, embedder):
    """A. Relevant retrieval: verify nearest relevant chunks are returned in order."""
    repo_a_id, _ = setup_test_repos
    retriever = RAGRetriever(db_session, embedder)
    
    query = "python styling fastAPI"
    results = retriever.search(repo_a_id, query, top_k=3)
    
    assert len(results) == 3
    # Expect the most relevant chunks to be at the top
    assert "fastAPI" in results[0].text or "python styling" in results[0].text
    
    # Verify ordering by cosine distance (lower distance means more similar)
    assert results[0].distance <= results[1].distance
    assert results[1].distance <= results[2].distance

def test_repository_isolation(db_session, setup_test_repos, embedder):
    """B. Repository isolation: CRITICAL. Repo A search must not return Repo B chunks."""
    repo_a_id, repo_b_id = setup_test_repos
    retriever = RAGRetriever(db_session, embedder)
    
    # Search in Repo A
    query = "explicit instruction python styling fastAPI"
    results_a = retriever.search(repo_a_id, query, top_k=5)
    
    assert len(results_a) > 0
    for r in results_a:
        assert r.repository_id == repo_a_id
        assert "Repo B" not in r.text
        
    # Search in Repo B
    results_b = retriever.search(repo_b_id, query, top_k=5)
    assert len(results_b) > 0
    for r in results_b:
        assert r.repository_id == repo_b_id
        assert "Repo A" not in r.text

def test_top_k(db_session, setup_test_repos, embedder):
    """C. top_k: Verify exactly top_k results are returned."""
    repo_a_id, _ = setup_test_repos
    retriever = RAGRetriever(db_session, embedder)
    
    query = "Random noise chunk"
    # We seeded 4 random noise chunks in A
    results = retriever.search(repo_a_id, query, top_k=2)
    
    assert len(results) == 2
    assert results[0].distance <= results[1].distance

def test_empty_repository(db_session, setup_test_repos, embedder):
    """D. Empty repository: Search a valid repo with no chunks."""
    # Create empty repo
    org = Organization(name="Empty Repo Org")
    db_session.add(org)
    db_session.commit()
    project = Project(organization_id=org.id, name="Empty Repo Proj")
    db_session.add(project)
    db_session.commit()
    repo_empty = Repository(project_id=project.id, github_owner="owner", github_name="empty", default_branch="main")
    db_session.add(repo_empty)
    db_session.commit()
    
    retriever = RAGRetriever(db_session, embedder)
    results = retriever.search(repo_empty.id, "test query", top_k=5)
    
    assert results == []

def test_embedding_dimension(embedder):
    """E. Embedding dimension: Verify LocalEmbedder output is exactly 384 dimensions."""
    embeddings = embedder.embed_chunks(["test vector"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == 384
    assert isinstance(embeddings[0][0], float)

def test_invalid_top_k(db_session, setup_test_repos, embedder):
    """F. Invalid top_k: Ensure invalid values are rejected with ValueError."""
    repo_a_id, _ = setup_test_repos
    retriever = RAGRetriever(db_session, embedder)
    
    with pytest.raises(ValueError):
        retriever.search(repo_a_id, "query", top_k=0)
        
    with pytest.raises(ValueError):
        retriever.search(repo_a_id, "query", top_k=-5)
        
    with pytest.raises(ValueError):
        retriever.search(repo_a_id, "query", top_k=5000)
