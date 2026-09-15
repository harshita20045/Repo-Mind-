import datetime
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.app.review.models import ReviewRun, RiskAssessment, Finding
from backend.app.github.models import PullRequest
from backend.app.organizations.models import Repository, Project

def get_organization_analytics(db: Session, organization_id: int, days: int = 30):
    """
    Returns analytics for the given organization over the last N days.
    Metrics:
    - Average risk score
    - Total PRs reviewed
    - Findings distribution by severity
    - Findings distribution by category
    - Trend (prs over time)
    """
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    # 1. Base query for completed ReviewRuns in this org
    base_run_query = (
        db.query(ReviewRun)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
    )

    # Total PRs reviewed (unique PRs)
    total_reviews = base_run_query.count()

    # 2. Average Risk Score
    avg_risk_query = (
        db.query(func.avg(RiskAssessment.score))
        .join(ReviewRun, RiskAssessment.review_run_id == ReviewRun.id)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
    )
    avg_risk_score = db.execute(avg_risk_query).scalar() or 0.0

    # 3. Findings Distribution by Severity
    severity_query = (
        db.query(Finding.severity, func.count(Finding.id))
        .join(ReviewRun, Finding.review_run_id == ReviewRun.id)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
        .group_by(Finding.severity)
    )
    severity_distribution = {row[0]: row[1] for row in db.execute(severity_query)}

    # 4. Findings Distribution by Category
    category_query = (
        db.query(Finding.type, func.count(Finding.id))
        .join(ReviewRun, Finding.review_run_id == ReviewRun.id)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
        .group_by(Finding.type)
    )
    category_distribution = {row[0]: row[1] for row in db.execute(category_query)}
    
    # 5. Lifecycle Status
    lifecycle_query = (
        db.query(Finding.lifecycle_status, func.count(Finding.id))
        .join(ReviewRun, Finding.review_run_id == ReviewRun.id)
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
        .group_by(Finding.lifecycle_status)
    )
    lifecycle_distribution = {row[0]: row[1] for row in db.execute(lifecycle_query)}

    return {
        "period_days": days,
        "total_reviews": total_reviews,
        "average_risk_score": round(avg_risk_score, 1),
        "findings_by_severity": severity_distribution,
        "findings_by_category": category_distribution,
        "findings_by_lifecycle": lifecycle_distribution,
    }
