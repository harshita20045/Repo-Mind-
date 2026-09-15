"""
Chat Assistant Service — RepoMind 2.0.

Manages conversational sessions scoped to PRs, repositories, or reviews.
Integrates code-aware RAG to ensure assistant answers are grounded in evidence.
"""
import logging
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.chat.models import ChatSession, ChatMessage
from backend.app.rag.retriever import RAGRetriever
from backend.app.review.provider import LLMProvider
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_CHAT_PROMPT = """You are RepoMind, an expert engineering intelligence assistant.
You are currently engaged in a conversation scoped to a {context_type}.

Always base your answers on the provided Evidence below, which is retrieved from the repository using Code-Aware RAG.
If the Evidence does not contain the answer, say "I don't have enough information in the repository context to answer that."
Never hallucinate file names, functions, or logic that isn't provided.

Evidence:
{evidence}
"""


def create_session(
    db: Session,
    user_id: int,
    organization_id: int,
    context_type: str,
    context_id: int
) -> ChatSession:
    """Create a new chat session."""
    session = ChatSession(
        user_id=user_id,
        organization_id=organization_id,
        context_type=context_type,
        context_id=context_id,
        created_at=datetime.now(timezone.utc)
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_sessions(db: Session, user_id: int, context_type: str, context_id: int) -> List[ChatSession]:
    """Get chat sessions for a user in a specific context."""
    stmt = select(ChatSession).where(
        ChatSession.user_id == user_id,
        ChatSession.context_type == context_type,
        ChatSession.context_id == context_id
    ).order_by(ChatSession.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def get_session_messages(db: Session, session_id: int, user_id: int) -> List[ChatMessage]:
    """Get all messages for a session (must belong to user)."""
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        return []
        
    stmt = select(ChatMessage).where(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc())
    return list(db.execute(stmt).scalars().all())


def send_message(
    db: Session,
    session_id: int,
    user_id: int,
    message: str,
    provider: LLMProvider,
    repository_id: int,
) -> ChatMessage:
    """
    Send a message in a chat session.
    Retrieves RAG context and queries the LLM.
    """
    session = db.get(ChatSession, session_id)
    if not session or session.user_id != user_id:
        raise ValueError("Session not found or access denied")
        
    # 1. Save user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=message
    )
    db.add(user_msg)
    
    # 2. Retrieve context via RAG
    retriever = RAGRetriever(db=db)
    # Search across all chunk types
    chunks = retriever.search(
        repository_id=repository_id,
        query_text=message,
        top_k=5,
        chunk_types=["documentation", "source_code", "test_code"]
    )
    
    # 3. Build evidence string
    evidence_parts = []
    sources = []
    for c in chunks:
        evidence_parts.append(f"--- File: {c.path} ({c.chunk_type}) ---\n{c.text}\n")
        sources.append({"type": c.chunk_type, "path": c.path})
        
    evidence_text = "\n".join(evidence_parts) if evidence_parts else "No relevant repository context found."
    
    system_prompt = SYSTEM_CHAT_PROMPT.format(
        context_type=session.context_type,
        evidence=evidence_text
    )
    
    # 4. Fetch previous history for context
    history = get_session_messages(db, session_id, user_id)
    # Simple history string formatting (in a real app, pass proper message objects to provider)
    history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in history[-5:]])
    user_content = f"Chat History:\n{history_text}\n\nUser Question:\n{message}"
    
    # 5. Call LLM
    try:
        response_content = provider.complete(system_prompt, user_content)
        is_grounded = bool(chunks)
    except Exception as e:
        logger.error(f"LLM Chat Error: {e}")
        response_content = "I'm sorry, I encountered an error while processing your request."
        is_grounded = False
        
    # 6. Save assistant message
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_content,
        sources=sources,
        is_grounded=is_grounded
    )
    db.add(assistant_msg)
    
    # Update session
    session.last_message_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_msg)
    
    return assistant_msg
