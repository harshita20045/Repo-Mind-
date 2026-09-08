# Diagram — ML Pipeline

**Status: Confirmed**

```mermaid
flowchart TB
    Hist[Historical PRs] --> FE[Feature Engineering]
    FE --> Split["Time-based train/test split\n(chronological, not random)"]
    Split --> Baseline[Rule-based baseline]
    Split --> Train[Train scikit-learn models]
    Baseline --> Compare[Compare]
    Train --> Compare
    Compare --> Store[(ml_prediction table, versioned .pkl model files)]
```

- **Regression (cycle time):** Linear Regression → Random Forest → Gradient Boosting, evaluated by MAE/RMSE.
- **Classification (delay):** Logistic Regression → Random Forest, evaluated by Precision/Recall/F1/ROC-AUC.
- **Leakage prevention:** only features knowable at PR-open time are used (no final review count, no `merged_at`); the train/test split is chronological, not random.
- **Inference:** synchronous, fast (<100ms), loaded from versioned `.pkl` files, called from `review_service` alongside the AI review — not a separate serving system.
