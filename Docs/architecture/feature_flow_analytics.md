# 13 — Feature Flow: Analytics

## Feature Summary
The analytics feature aggregates review data at the organization level to provide engineering managers with visibility into PR review quality, risk trends, and finding patterns. All queries are scoped to the requesting user's organization and filtered to completed review runs within a configurable time window.

---

## End-to-End Flow

### 1. Frontend Request

| Step | Where | What Happens |
|---|---|---|
| User opens Analytics page | `AnalyticsPage.jsx` | `analyticsApi.getOrgAnalytics(orgId, days=30)` |
| API call | `lib/api.js:111` | `GET /analytics/organization/{orgId}?days=30` |
| Route | `backend/app/analytics/router.py` | Auth + org membership check, calls `get_organization_analytics(db, org_id, days)` |

---

### 2. Analytics Queries

File: `backend/app/analytics/service.py` → `get_organization_analytics(db, organization_id, days)`

#### Base Query Setup
```python
cutoff_date = datetime.now(UTC) - timedelta(days=days)

# Walk: ReviewRun → PullRequest → Repository → Project → filter by organization_id
base_run_query = (
    db.query(ReviewRun)
    .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
    .join(Repository, PullRequest.repository_id == Repository.id)
    .join(Project, Repository.project_id == Project.id)
    .filter(Project.organization_id == organization_id)
    .filter(ReviewRun.status == "completed")
    .filter(ReviewRun.completed_at >= cutoff_date)
)
```

All 4 metrics use the same join chain and filters.

#### Metric 1: Total PRs Reviewed
```python
total_reviews = base_run_query.count()
```

#### Metric 2: Average Risk Score
```python
avg_risk = (
    db.query(func.avg(RiskAssessment.score))
    .join(ReviewRun, ...)  # Same join chain
    .filter(...)
)
avg_risk_score = db.execute(avg_risk).scalar() or 0.0
```

#### Metric 3: Findings by Severity
```python
severity_query = (
    db.query(Finding.severity, func.count(Finding.id))
    .join(ReviewRun, ...)
    .filter(...)
    .group_by(Finding.severity)
)
severity_distribution = {row[0]: row[1] for row in db.execute(severity_query)}
# Result: {"critical": 3, "high": 12, "medium": 45, "low": 20, "info": 5}
```

#### Metric 4: Findings by Category
```python
category_query = (
    db.query(Finding.type, func.count(Finding.id))
    .join(ReviewRun, ...)
    .filter(...)
    .group_by(Finding.type)
)
category_distribution = {row[0]: row[1] for row in db.execute(category_query)}
# Result: {"security": 8, "performance": 5, "standards_violation": 30, ...}
```

#### Metric 5: Findings by Lifecycle Status
```python
lifecycle_query = (
    db.query(Finding.lifecycle_status, func.count(Finding.id))
    .join(ReviewRun, ...)
    .filter(...)
    .group_by(Finding.lifecycle_status)
)
lifecycle_distribution = {row[0]: row[1] for row in db.execute(lifecycle_query)}
# Result: {"new": 15, "persistent": 8, "resolved": 22}
```

---

### 3. Response

```python
return {
    "period_days": days,
    "total_reviews": total_reviews,
    "average_risk_score": round(avg_risk_score, 1),
    "findings_by_severity": severity_distribution,
    "findings_by_category": category_distribution,
    "findings_by_lifecycle": lifecycle_distribution,
}
```

---

## UI Display

`AnalyticsPage.jsx` renders:
- Total PRs reviewed
- Average risk score (gauge or number)
- Findings by severity (bar/pie chart)
- Findings by category (bar chart)
- Findings by lifecycle (showing fix rate: resolved vs. persistent)

---

## Permission Required

Route requires: `Permission.ANALYTICS_READ`

Roles with `ANALYTICS_READ`: `developer`, `reviewer`, `tech_lead`, `org_admin` (all roles).

---

## Key Files

| File | Location | Role |
|---|---|---|
| `service.py` | `backend/app/analytics/service.py` | `get_organization_analytics()` — 5 DB queries |
| `router.py` | `backend/app/analytics/router.py` | `GET /analytics/organization/{org_id}` |
| `api.js` | `frontend/src/lib/api.js:110-115` | `analyticsApi.getOrgAnalytics()` |
| `AnalyticsPage.jsx` | `frontend/src/pages/AnalyticsPage.jsx` | Analytics UI |

---

## Tables Read

| Table | Via Join | For |
|---|---|---|
| `review_run` | Direct | Base query (completed runs in period) |
| `pull_request` | FK join | To get repository |
| `repository` | FK join | To get project |
| `project` | FK join | To filter by organization |
| `risk_assessment` | FK join | Average risk score |
| `finding` | FK join | Severity/category/lifecycle distributions |
