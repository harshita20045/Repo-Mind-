# 18 — Feature Flow: ML Prediction (PR Cycle Time)

## Feature Summary
The ML module provides PR cycle time prediction. It is currently a **rule-based baseline** (`baseline-v1`) because the application requires at least 50 closed PRs with `merged_at` timestamps to train a meaningful ML model. The trainer code exists and is functional (`trainer.py`), but the `MLService` always falls back to the heuristic baseline due to insufficient training data.

---

## Current State (as observed in source)

The ML system has two layers:
1. **`ml/service.py`** — Called by the API, always uses rule-based baseline
2. **`ml/trainer.py`** — Full sklearn pipeline (LinearRegression + RandomForestClassifier), not yet called in production

---

## End-to-End Flow (Current Production Behavior)

### 1. API Request

| Step | Where | What Happens |
|---|---|---|
| User or system requests prediction | `mlApi.getPrPrediction(prId)` | `frontend/src/lib/api.js:139` |
| API call | `GET /ml/prediction/pr/{pr_id}` | |
| Route | `backend/app/ml/router.py` | Calls `MLService.get_prediction_for_pr(db, pr_id)` |

---

### 2. Training Data Check

File: `backend/app/ml/service.py` → `MLService.get_prediction_for_pr()`

```python
closed_prs = db.query(PullRequest).filter(PullRequest.state == 'closed').count()

if closed_prs < 50:
    logger.warning("INSUFFICIENT TRAINING DATA: %d closed PRs. Falling back to rule-based baseline.", closed_prs)
    return MLService._get_rule_based_baseline(db, pr_id)
    
# Would load trained model here — not yet reached in practice
return MLService._get_rule_based_baseline(db, pr_id)
```

Both branches call `_get_rule_based_baseline()`. Even if 50+ closed PRs exist, the current code still returns the baseline.

---

### 3. Rule-Based Baseline

```python
@staticmethod
def _get_rule_based_baseline(db, pr_id) -> MLPrediction:
    pr = db.get(PullRequest, pr_id)
    
    # Count how many reviews this PR has had
    runs_count = db.query(ReviewRun).filter_by(pull_request_id=pr_id).count()
    
    # Heuristic: more reviews = more complex PR = longer cycle time
    expected_days = 1.0 + (runs_count * 0.5)
    
    # Classify: >2 days = SLOW
    predicted_delay_category = "SLOW" if expected_days > 2.0 else "ON_TIME"
    confidence_score = 0.5  # Always 0.5 for rule-based (low confidence)
    
    # Upsert prediction
    existing = db.query(MLPrediction).filter_by(pull_request_id=pr_id).first()
    if existing:
        # Update
    else:
        db.add(MLPrediction(...))
    db.commit()
    return prediction
```

---

### 4. Response

```python
{
    "id": 1,
    "pull_request_id": 42,
    "predicted_delay_category": "ON_TIME",
    "confidence_score": 0.5,
    "prediction_model_version": "baseline-v1",
    "created_at": "2026-09-18T..."
}
```

---

## Trainer Architecture (Not Yet Active)

File: `backend/app/ml/trainer.py`

### Feature Extraction

```python
def extract_features(pr: PullRequest) -> List[float]:
    return [
        float(pr.additions or 0),
        float(pr.deletions or 0),
        float(pr.files_changed or 0),
    ]
```

Only 3 features: `additions`, `deletions`, `files_changed`. Requires these fields to be populated in the `pull_request` table from GitHub sync.

### Dataset Building

```python
def build_dataset(db: Session):
    prs = db.query(PullRequest).filter(PullRequest.state == "closed").all()
    
    if len(prs) < MIN_REQUIRED_PRS:  # 50
        raise InsufficientDataError(...)
    
    for pr in prs:
        if not pr.created_at or not pr.merged_at:
            continue  # Skip PRs without timestamps
        
        cycle_time_days = (pr.merged_at - pr.created_at).total_seconds() / 86400.0
        is_slow = 1 if cycle_time_days > 2.0 else 0
        
        X.append(extract_features(pr))
        y_reg.append(cycle_time_days)
        y_cls.append(is_slow)
    
    return np.array(X), np.array(y_reg), np.array(y_cls)
```

### ML Pipeline

```python
class RepoMindMLPipeline:
    def __init__(self):
        self.regressor = LinearRegression()         # Predicts cycle time in days
        self.classifier = RandomForestClassifier(n_estimators=50, random_state=42)  # Predicts SLOW/ON_TIME
    
    def train(self, X, y_reg, y_cls):
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        
        self.regressor.fit(X_train, y_reg_train)
        self.classifier.fit(X_train, y_cls_train)
        
        return {
            "regression_mae": mae,
            "classification_accuracy": acc,
            "classification_precision": precision,
            "classification_recall": recall,
        }
    
    def predict(self, pr: PullRequest):
        features = np.array(extract_features(pr)).reshape(1, -1)
        predicted_days = self.regressor.predict(features)[0]
        delay_prob = self.classifier.predict_proba(features)[0][1]
        return {"predicted_days": float(predicted_days), "delay_probability": float(delay_prob)}
```

### Production Training Entry Point

```python
def train_production_models(db: Session):
    X, y_reg, y_cls = build_dataset(db)
    pipeline = RepoMindMLPipeline()
    metrics = pipeline.train(X, y_reg, y_cls)
    # TODO: pickle.dump(pipeline, open("model.pkl", "wb"))  # Not yet implemented
    return metrics
```

Model persistence is commented out — no model file is ever written to disk.

---

## Data Model

File: `backend/app/ml/models.py` → `MLPrediction`

| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `pull_request_id` | FK → `pull_request.id` | |
| `predicted_delay_category` | String | `ON_TIME` / `SLOW` |
| `confidence_score` | Float | Always 0.5 for baseline |
| `prediction_model_version` | String | `"baseline-v1"` |
| `created_at` | DateTime(tz) | |

---

## Key Files

| File | Location | Role |
|---|---|---|
| `service.py` | `backend/app/ml/service.py` | `MLService.get_prediction_for_pr()` — always calls baseline |
| `trainer.py` | `backend/app/ml/trainer.py` | Full sklearn pipeline — not yet active in production |
| `models.py` | `backend/app/ml/models.py` | `MLPrediction` SQLAlchemy model |
| `router.py` | `backend/app/ml/router.py` | `GET /ml/prediction/pr/{pr_id}` |
| `api.js` | `frontend/src/lib/api.js:138-143` | `mlApi.getPrPrediction()` |

---

## External Libraries

| Library | Purpose | Import Location |
|---|---|---|
| `sklearn.linear_model.LinearRegression` | Cycle time regression | `trainer.py` |
| `sklearn.ensemble.RandomForestClassifier` | Delay classification | `trainer.py` |
| `sklearn.metrics` | MAE, accuracy, precision, recall | `trainer.py` |
| `numpy` | Feature matrix operations | `trainer.py` |
| `pickle` | Model serialization (commented out) | `trainer.py` |

---

## Production Gap

The ML system as currently deployed is purely heuristic. The comment in `service.py` states:
```python
# In the future, this would load the pickled sklearn RandomForestRegressor/Classifier
# and extract features from the PR. For now, data is insufficient.
```

To enable real ML:
1. Accumulate 50+ merged PRs with `additions`, `deletions`, `files_changed`, `merged_at` populated
2. Call `train_production_models(db)` via a management script
3. Persist the model with `pickle.dump()`
4. Update `MLService.get_prediction_for_pr()` to load and use the pickled model
