"""
Webhook event SQLAlchemy model — RepoMind 2.0.

Incoming GitHub webhook events are persisted before processing.
This provides an audit trail and enables replay if processing fails.

Security:
  - Webhook signature is verified before the event is stored.
  - The GITHUB_WEBHOOK_SECRET must be set in .env.
  - Raw payload is stored as JSONB for processing flexibility.
"""
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB

from backend.app.db import Base


class WebhookEvent(Base):
    """
    A GitHub webhook event received by RepoMind.

    Lifecycle:
      received → processed (review job created)
               → skipped (event type not handled)
               → failed (processing error)
    """
    __tablename__ = "webhook_event"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # GitHub-assigned delivery ID (for deduplication and debugging)
    github_delivery_id = Column(String(255), nullable=True, unique=True, index=True)
    # pull_request | push | ping | etc.
    event_type = Column(String(100), nullable=False)
    # The action within the event (opened, synchronize, closed, etc.)
    action = Column(String(100), nullable=True)
    # Repository this webhook belongs to (resolved during processing)
    repository_id = Column(
        Integer,
        ForeignKey("repository.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    # Full webhook payload (JSONB for flexible querying)
    payload = Column(JSONB, nullable=False)
    # received | processed | skipped | failed
    status = Column(String(50), nullable=False, default="received")
    error_message = Column(Text, nullable=True)
    received_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.datetime.now(datetime.timezone.utc),
        nullable=False,
        index=True,
    )
    processed_at = Column(DateTime(timezone=True), nullable=True)
