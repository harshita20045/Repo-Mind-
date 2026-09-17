from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MLPredictionResponse(BaseModel):
    id: int
    pull_request_id: int
    predicted_delay_category: str
    confidence_score: Optional[float]
    prediction_model_version: str
    created_at: datetime

    class Config:
        from_attributes = True
