from sqlalchemy.orm import Session
from .models import MLPrediction
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MLService:
    @staticmethod
    def get_prediction_for_pr(db: Session, pr_id: int) -> MLPrediction:
        # Check training data availability
        total_prs = db.query(PullRequest).count()
        closed_prs = db.query(PullRequest).filter(PullRequest.state == 'closed').count()
        
        # We need at least 50 historical closed PRs to train a meaningful regression model
        if closed_prs < 50:
            logger.warning("INSUFFICIENT TRAINING DATA: %d closed PRs. Falling back to rule-based baseline.", closed_prs)
            return MLService._get_rule_based_baseline(db, pr_id)
            
        # In the future, this would load the pickled sklearn RandomForestRegressor/Classifier
        # and extract features from the PR. For now, data is insufficient.
        return MLService._get_rule_based_baseline(db, pr_id)

    @staticmethod
    def _get_rule_based_baseline(db: Session, pr_id: int) -> MLPrediction:
        pr = db.get(PullRequest, pr_id)
        if not pr:
            return None
            
        # Extract basic deterministic features
        # In a real model, additions/deletions would be available from the GitHub API sync
        # Here we use the PR status and number of review runs to estimate complexity
        runs_count = db.query(ReviewRun).filter_by(pull_request_id=pr_id).count()
        
        # Rule-based heuristics
        expected_days = 1.0 + (runs_count * 0.5)
        
        # Delay probability classification threshold: > 2 days is considered delayed
        delay_threshold_days = 2.0
        
        predicted_delay_category = "SLOW" if expected_days > delay_threshold_days else "ON_TIME"
        confidence_score = 0.5 # Low confidence due to rule-based baseline
        
        prediction = MLPrediction(
            pull_request_id=pr_id,
            predicted_delay_category=predicted_delay_category,
            confidence_score=confidence_score,
            prediction_model_version="baseline-v1",
            created_at=datetime.now(timezone.utc)
        )
        
        # Persist to DB so it has an ID
        existing = db.query(MLPrediction).filter_by(pull_request_id=pr_id).first()
        if existing:
            existing.predicted_delay_category = predicted_delay_category
            existing.confidence_score = confidence_score
            existing.prediction_model_version = "baseline-v1"
            existing.created_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
            
        db.add(prediction)
        db.commit()
        db.refresh(prediction)
        
        return prediction

