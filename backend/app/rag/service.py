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
    
    # Fetch connection via the modern per-user OAuth logic (uses an org admin's token)
    from backend.app.github.service import get_decrypted_github_token_for_org
    from fastapi import HTTPException
    
    try:
        pat = get_decrypted_github_token_for_org(db, organization_id)
    except HTTPException as e:
        raise ValueError(e.detail)
        
    github_client = GitHubClient(pat)
    
    # Initialize RAG components
    loader = DocumentLoader(github_client, repo.github_owner, repo.github_name, repo.default_branch)
    chunker = TextChunker()
    embedder = LocalEmbedder()
    rag_repo = RAGRepository(db)
    
    from backend.app.github.client import GitHubAPIError

    # 2. Discover documents
    try:
        documents_meta = loader.discover_documents()
    except GitHubAPIError as e:
        if e.status_code == 401:
            logger.info("Encountered 401 during indexing, forcing token refresh...")
            pat = get_decrypted_github_token_for_org(db, organization_id, force_refresh=True)
            github_client = GitHubClient(pat)
            loader = DocumentLoader(github_client, repo.github_owner, repo.github_name, repo.default_branch)
            documents_meta = loader.discover_documents()
        else:
            raise
    
    # 3. Load valid document contents
    file_dict = {}
    for doc_meta in documents_meta:
        path = doc_meta["path"]
        sha = doc_meta["sha"]
        text_content = loader.load_document_content(path, sha)
        if text_content:
            file_dict[path] = text_content

    # 4. Orchestrate complete Repository Intelligence Indexing
    from backend.app.intelligence.indexer import RepositoryIndexer
    indexer = RepositoryIndexer(db, repository_id)
    indexer.index_from_file_dict(file_dict, commit_sha=repo.default_branch)
