"""
Chat / AI Assistant SQLAlchemy models — RepoMind 2.0.

The AI assistant is NOT a generic chatbot.
Each session is scoped to a specific context (PR, repository, or review run)
and all answers must be grounded in repository evidence.

Tables:
  chat_session  — a conversation session tied to a specific context
  chat_message  — individual messages within a session
"""
import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.app.db import Base


class ChatSession(Base):
    """
    A conversation session between a user and the RepoMind AI assistant.

    context_type determines what data the assistant has access to:
      - pr:         PR detail, review run, findings, evidence, conflicts
      - repository: Repository docs, architecture, source code (via RAG)
      - review:     Specific review run, findings, evidence comparison
    """
    __tablename__ = "chat_session"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # pr | repository | review
    context_type = Column(String(50), nullable=False)
    # FK to the specific context resource (PR id, repository id, or review_run id)
    context_id = Column(Integer, nullable=False)
    # Organization for permission scoping
    organization_id = Column(
        Integer,
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )
    last_message_at = Column(DateTime(timezone=True), nullable=True)

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at",
    )


class ChatMessage(Base):
    """
    A single message in a chat session.

    Messages from the assistant include source citations grounding the answer
    in actual repository/review evidence.
    """
    __tablename__ = "chat_message"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(
        Integer,
        ForeignKey("chat_session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # user | assistant
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    # For assistant messages: list of sources used to ground the answer
    # Example: [{"type": "document", "path": "ARCHITECTURE.md", "excerpt": "..."}]
    sources = Column(JSONB, nullable=True)
    # Whether the assistant had sufficient evidence to answer confidently
    is_grounded = Column(Boolean, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
    )

    session = relationship("ChatSession", back_populates="messages")
