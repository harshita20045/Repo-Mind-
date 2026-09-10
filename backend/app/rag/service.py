import logging
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.organizations.models import Repository, GithubConnection
from backend.app.github.client import GitHubClient
from backend.app.github.encryption import decrypt_token
from backend.app.rag.loader import DocumentLoader
from backend.app.rag.chunker import TextChunker
from backend.app.rag.embedder import LocalEmbedder
from backend.app.rag.repository import RAGRepository

logger = logging.getLogger(__name__)

def index_repository(db: Session, repository_id: int) -> None:
    """
    Synchronous orchestration for Phase 6 repository indexing.
    Loads documents, checks for changes, chunks, embeds, and stores results.
    """
    # 1. Fetch the repository and connection
    repo = db.get(Repository, repository_id)
    if not repo:
        raise ValueError(f"Repository {repository_id} not found")
        
    project = repo.project
    if not project:
        raise ValueError(f"Project for repository {repository_id} not found")
        
    organization_id = project.organization_id
    
    # Fetch connection
    stmt = select(GithubConnection).where(GithubConnection.organization_id == organization_id)
    conn = db.execute(stmt).scalars().first()
    if not conn:
        raise ValueError(f"No GitHub connection found for organization {organization_id}")
        
    # Initialize GitHub client without persisting PAT in memory longer than needed
    pat = decrypt_token(conn.encrypted_token)
    github_client = GitHubClient(pat)
    
    # Initialize RAG components
    loader = DocumentLoader(github_client, repo.github_owner, repo.github_name, repo.default_branch)
    chunker = TextChunker()
    embedder = LocalEmbedder()
    rag_repo = RAGRepository(db)
    
    # 2. Discover documents
    documents_meta = loader.discover_documents()
    
    # 3. Process each document
    for doc_meta in documents_meta:
        path = doc_meta["path"]
        sha = doc_meta["sha"]
        
        # Load and hash
        text_content = loader.load_document_content(path, sha)
        if not text_content:
            continue
            
        content_hash = loader.hash_content(text_content)
        
        # Check idempotency
        existing_doc = rag_repo.get_document_by_path(repository_id, path)
        if existing_doc and existing_doc.content_hash == content_hash:
            # Unchanged, skip
            continue
            
        # 4. Save document metadata
        doc = rag_repo.save_document(repository_id, path, content_hash)
        
        # 5. Chunking
        text_chunks = chunker.chunk_text(text_content)
        if not text_chunks:
            continue
            
        # 6. Embedding
        embeddings = embedder.embed_chunks(text_chunks)
        
        # 7. Persistence
        # Combine text and embeddings
        chunk_data = list(zip(text_chunks, embeddings))
        rag_repo.save_chunks(repository_id, doc.id, chunk_data)
        
    # We do not mark index_status here because Phase 13 owns job states.
    # We just commit the data.
    db.commit()
