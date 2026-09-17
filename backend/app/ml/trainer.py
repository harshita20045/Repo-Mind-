from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import mean_absolute_error, accuracy_score, precision_score, recall_score
from backend.app.github.models import PullRequest
import pickle

logger = logging.getLogger(__name__)

# Configurable threshold from spec
SLOW_THRESHOLD_DAYS = 2.0
MIN_REQUIRED_PRS = 50

class InsufficientDataError(Exception):
    pass

def extract_features(pr: PullRequest) -> List[float]:
    """Extract features from a PullRequest for ML models."""
    additions = float(pr.additions or 0)
    deletions = float(pr.deletions or 0)
    files_changed = float(pr.files_changed or 0)
    # Could add author historical metrics here if available in the schema, 
    # but currently schema has basic PR metadata.
    
    return [additions, deletions, files_changed]

def build_dataset(db: Session) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Build dataset from closed PullRequests.
    Returns:
        X: Feature matrix
        y_reg: Regression targets (cycle time in days)
        y_cls: Classification targets (1 if SLOW, 0 otherwise)
    """
    prs = db.query(PullRequest).filter(PullRequest.state == "closed").all()
    
    if len(prs) < MIN_REQUIRED_PRS:
        raise InsufficientDataError(
            f"INSUFFICIENT_TRAINING_DATA: Found {len(prs)} closed PRs, require {MIN_REQUIRED_PRS}"
        )
        
    X = []
    y_reg = []
    y_cls = []
    
    for pr in prs:
        # Require both timestamps to compute cycle time
        if not pr.created_at or not pr.merged_at:
            continue
            
        cycle_time_td = pr.merged_at - pr.created_at
        cycle_time_days = cycle_time_td.total_seconds() / 86400.0
        
        # Target for classification
        is_slow = 1 if cycle_time_days > SLOW_THRESHOLD_DAYS else 0
        
        X.append(extract_features(pr))
        y_reg.append(cycle_time_days)
        y_cls.append(is_slow)
        
    if len(X) < MIN_REQUIRED_PRS:
        raise InsufficientDataError(
            f"INSUFFICIENT_TRAINING_DATA: Found {len(X)} eligible closed PRs after filtering, require {MIN_REQUIRED_PRS}"
        )
        
    return np.array(X), np.array(y_reg), np.array(y_cls)

class RepoMindMLPipeline:
    def __init__(self):
        self.regressor = LinearRegression()
        self.classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        self.is_fitted = False
        
    def train(self, X: np.ndarray, y_reg: np.ndarray, y_cls: np.ndarray) -> Dict[str, Any]:
        """Train models and return metrics."""
        # Simple train/test split (80/20)
        split_idx = int(len(X) * 0.8)
        
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_reg_train, y_reg_test = y_reg[:split_idx], y_reg[split_idx:]
        y_cls_train, y_cls_test = y_cls[:split_idx], y_cls[split_idx:]
        
        # Fit Regression
        self.regressor.fit(X_train, y_reg_train)
        reg_preds = self.regressor.predict(X_test)
        mae = mean_absolute_error(y_reg_test, reg_preds)
        
        # Fit Classification
        self.classifier.fit(X_train, y_cls_train)
        cls_preds = self.classifier.predict(X_test)
        
        # Prevent division by zero warnings if the test set lacks one class
        acc = accuracy_score(y_cls_test, cls_preds)
        precision = precision_score(y_cls_test, cls_preds, zero_division=0)
        recall = recall_score(y_cls_test, cls_preds, zero_division=0)
        
        self.is_fitted = True
        
        return {
            "regression_mae": mae,
            "classification_accuracy": acc,
            "classification_precision": precision,
            "classification_recall": recall
        }
        
    def predict(self, pr: PullRequest) -> Dict[str, Any]:
        """Predict cycle time and delay risk for a given PR."""
        if not self.is_fitted:
            raise RuntimeError("Pipeline is not fitted yet.")
            
        features = np.array(extract_features(pr)).reshape(1, -1)
        
        predicted_days = self.regressor.predict(features)[0]
        delay_prob = self.classifier.predict_proba(features)[0][1]
        
        return {
            "predicted_days": float(predicted_days),
            "delay_probability": float(delay_prob),
            "is_slow_risk": delay_prob > 0.5
        }

def train_production_models(db: Session) -> Optional[Dict[str, Any]]:
    """Attempt to train models using production DB."""
    try:
        X, y_reg, y_cls = build_dataset(db)
        pipeline = RepoMindMLPipeline()
        metrics = pipeline.train(X, y_reg, y_cls)
        # Persistence would happen here, e.g., with pickle
        # with open("model.pkl", "wb") as f:
        #     pickle.dump(pipeline, f)
        return metrics
    except InsufficientDataError as e:
        logger.warning(str(e))
        return None
