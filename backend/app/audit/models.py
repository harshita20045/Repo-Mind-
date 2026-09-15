from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.db import Base
from datetime import datetime, timezone

class AuditLog(Base):
    __tablename__ = "audit_log"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(255), nullable=False)
    target_type = Column(String(255), nullable=False)
    target_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
