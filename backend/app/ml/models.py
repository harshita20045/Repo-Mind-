from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from backend.app.db import Base

class MLPrediction(Base):
    __tablename__ = 'ml_prediction'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    pull_request_id = Column(Integer, ForeignKey('pull_request.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    predicted_delay_category = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=True)
    prediction_model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    pull_request = relationship('PullRequest')
