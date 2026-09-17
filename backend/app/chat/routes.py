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
from backend.app.auth.permissions import Permission, require_org_permission
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
    """Start a new chat session."""
    # Ensure user has CHAT_USE permission in this organization
    require_org_permission(request.organization_id, Permission.CHAT_USE)(user, db)
    
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
    require_org_permission(organization_id, Permission.CHAT_USE)(user, db)
    
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
    require_org_permission(organization_id, Permission.CHAT_USE)(user, db)
    
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
    """Send a message and get the AI assistant response."""
    require_org_permission(organization_id, Permission.CHAT_USE)(user, db)
    
    provider = get_llm_provider(settings)
    try:
        assistant_msg = send_message(
            db=db,
            session_id=session_id,
            user_id=user.id,
            message=request.message,
            provider=provider,
            repository_id=request.repository_id
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
