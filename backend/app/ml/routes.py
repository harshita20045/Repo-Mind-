from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db import get_db
from .schemas import MLPredictionResponse
from .service import MLService

router = APIRouter(prefix='/ml', tags=['ml'])

@router.get('/prediction/pr/{pr_id}', response_model=MLPredictionResponse)
def get_pr_prediction(pr_id: int, db: Session = Depends(get_db)):
    prediction = MLService.get_prediction_for_pr(db, pr_id)
    if not prediction:
        raise HTTPException(status_code=404, detail='Prediction not found')
    return prediction
