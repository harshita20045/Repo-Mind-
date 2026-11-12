"""
Chat Assistant Routes — RepoMind 2.0.

Provides endpoints to start sessions, retrieve history, and send messages.
Authorization is scoped per organization using the new RBAC system.
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.auth.permissions import Permission, assert_org_permission
from backend.app.organizations.models import Repository
from backend.app.github.models import PullRequest
from backend.app.chat.models import ChatSession
from backend.app.review.provider import get_llm_provider
from backend.app.core.config import settings

from backend.app.chat.service import (
    create_session,
    get_sessions,
    get_session_messages,
    send_message
)

router = APIRouter(tags=["chat"])

class ChatSessionCreate(BaseModel):
    organization_id: int
    context_type: str  # "pr", "repository", "review"
    context_id: int
    
class ChatSessionResponse(BaseModel):
    id: int
    context_type: str
    context_id: int
    
class ChatMessageRequest(BaseModel):
    message: str
    repository_id: Optional[int] = None  # Needed for RAG isolation

class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    sources: Optional[list] = None
    is_grounded: Optional[bool] = None

@router.post("/chat/sessions", response_model=ChatSessionResponse)
def start_chat_session(
    request: ChatSessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new chat session with strict context and organization validation."""
    # Ensure user has CHAT_USE permission in this organization
    assert_org_permission(db, user.id, request.organization_id, Permission.CHAT_USE)
    
    # Validate context and prevent cross-tenant repository / PR association
    ctx = request.context_type.lower()
    if ctx in ("repository", "repo"):
        repo = db.get(Repository, request.context_id)
        if not repo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        if repo.project.organization_id != request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Repository does not belong to specified organization"
            )
        assert_org_permission(db, user.id, repo.project.organization_id, Permission.REPOS_READ)
    elif ctx in ("pr", "pull_request"):
        pr = db.get(PullRequest, request.context_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
        pr_org_id = pr.repository.project.organization_id
        if pr_org_id != request.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Pull request does not belong to specified organization"
            )
        assert_org_permission(db, user.id, pr_org_id, Permission.PRS_READ)
    
    session = create_session(
        db=db,
        user_id=user.id,
        organization_id=request.organization_id,
        context_type=request.context_type,
        context_id=request.context_id
    )
    return ChatSessionResponse(
        id=session.id,
        context_type=session.context_type,
        context_id=session.context_id
    )

@router.get("/chat/sessions", response_model=List[ChatSessionResponse])
def list_chat_sessions(
    organization_id: int,
    context_type: str,
    context_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List chat sessions for a specific context."""
    assert_org_permission(db, user.id, organization_id, Permission.CHAT_USE)
    
    ctx = context_type.lower()
    if ctx in ("repository", "repo"):
        repo = db.get(Repository, context_id)
        if not repo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        if repo.project.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Repository does not belong to organization")
        assert_org_permission(db, user.id, repo.project.organization_id, Permission.REPOS_READ)
    elif ctx in ("pr", "pull_request"):
        pr = db.get(PullRequest, context_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
        if pr.repository.project.organization_id != organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Pull request does not belong to organization")
        assert_org_permission(db, user.id, pr.repository.project.organization_id, Permission.PRS_READ)

    sessions = get_sessions(db, user.id, context_type, context_id)
    return [
        ChatSessionResponse(
            id=s.id,
            context_type=s.context_type,
            context_id=s.context_id
        ) for s in sessions
    ]

@router.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
def get_chat_history(
    session_id: int,
    organization_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get message history for a session."""
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    if session.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to specified organization")
        
    assert_org_permission(db, user.id, organization_id, Permission.CHAT_USE)
    
    messages = get_session_messages(db, session_id, user.id)
    return [
        ChatMessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            sources=m.sources,
            is_grounded=m.is_grounded
        ) for m in messages
    ]

@router.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse)
def post_chat_message(
    session_id: int,
    organization_id: int,
    request: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message and get the AI assistant response with strict repository authorization."""
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found")
    if session.organization_id != organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Session does not belong to specified organization")

    assert_org_permission(db, user.id, organization_id, Permission.CHAT_USE)
    
    # Resolve and strictly authorize repository scoping
    target_repo_id: Optional[int] = None
    ctx = session.context_type.lower()
    
    if ctx in ("repository", "repo"):
        expected_repo_id = session.context_id
        if request.repository_id is not None and request.repository_id != expected_repo_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="repository_id cannot differ from session repository context"
            )
        target_repo_id = expected_repo_id
    elif ctx in ("pr", "pull_request"):
        pr = db.get(PullRequest, session.context_id)
        if not pr:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pull request not found")
        if request.repository_id is not None and request.repository_id != pr.repository_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="repository_id cannot differ from pull request repository"
            )
        target_repo_id = pr.repository_id
    else:
        target_repo_id = request.repository_id

    # If target_repo_id resolved, verify it belongs to this org and user has REPOS_READ
    if target_repo_id is not None:
        repo = db.get(Repository, target_repo_id)
        if not repo:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repository not found")
        if repo.project.organization_id != organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Repository does not belong to session organization"
            )
        assert_org_permission(db, user.id, repo.project.organization_id, Permission.REPOS_READ)

    provider = get_llm_provider(settings)
    try:
        assistant_msg = send_message(
            db=db,
            session_id=session_id,
            user_id=user.id,
            message=request.message,
            provider=provider,
            repository_id=target_repo_id
        )
        return ChatMessageResponse(
            id=assistant_msg.id,
            role=assistant_msg.role,
            content=assistant_msg.content,
            sources=assistant_msg.sources,
            is_grounded=assistant_msg.is_grounded
        )
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
