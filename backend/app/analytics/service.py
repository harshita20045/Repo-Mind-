import datetime
from sqlalchemy import func, case
from sqlalchemy.orm import Session

from backend.app.review.models import ReviewRun, RiskAssessment, Finding
from backend.app.github.models import PullRequest
from backend.app.organizations.models import Repository, Project

def get_organization_analytics(db: Session, organization_id: int, days: int = 30):
    """
    Returns analytics for the given organization over the last N days.

    GAP-13: Uses the latest completed review run per PR within the requested reporting
    window as the canonical metric unit. This avoids counting multiple historical runs
    for the same PR as multiple current reviews or double-counting findings.

    Metrics:
    - Average risk score (from latest completed run per PR)
    - Total PRs reviewed (distinct PRs with completed review runs)
    - Findings distribution by severity (from latest completed runs)
    - Findings distribution by category (from latest completed runs)
    - Findings distribution by lifecycle (from latest completed runs)
    """
    cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)

    # Subquery: get the ranked completed ReviewRuns for each PullRequest (completed_at DESC, id DESC)
    ranked_runs_subq = (
        db.query(
            ReviewRun.id.label("run_id"),
            ReviewRun.pull_request_id.label("pr_id"),
            func.row_number().over(
                partition_by=ReviewRun.pull_request_id,
                order_by=(ReviewRun.completed_at.desc(), ReviewRun.id.desc())
            ).label("row_num")
        )
        .join(PullRequest, ReviewRun.pull_request_id == PullRequest.id)
        .join(Repository, PullRequest.repository_id == Repository.id)
        .join(Project, Repository.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .filter(ReviewRun.status == "completed")
        .filter(ReviewRun.completed_at >= cutoff_date)
        .subquery()
    )

    # Subquery filtering down to exactly row_num == 1 (the single latest completed run per PR)
    latest_run_subq = (
        db.query(
            ranked_runs_subq.c.pr_id,
            ranked_runs_subq.c.run_id.label("max_run_id")
        )
        .filter(ranked_runs_subq.c.row_num == 1)
        .subquery()
    )

    # 1. Total unique PRs reviewed in this period
    total_reviews_query = db.query(func.count(latest_run_subq.c.pr_id))
    total_reviews = total_reviews_query.scalar() or 0

    # 2. Average Risk Score (across latest completed runs)
    avg_risk_query = (
        db.query(func.avg(RiskAssessment.score))
        .join(latest_run_subq, RiskAssessment.review_run_id == latest_run_subq.c.max_run_id)
    )
    avg_risk_score = avg_risk_query.scalar() or 0.0

    # 3. Findings Distribution by Severity (across latest completed runs)
    severity_query = (
        db.query(Finding.severity, func.count(Finding.id))
        .join(latest_run_subq, Finding.review_run_id == latest_run_subq.c.max_run_id)
        .group_by(Finding.severity)
    )
    severity_distribution = {row[0]: row[1] for row in severity_query.all()}

    # 4. Findings Distribution by Category (across latest completed runs)
    category_query = (
        db.query(Finding.type, func.count(Finding.id))
        .join(latest_run_subq, Finding.review_run_id == latest_run_subq.c.max_run_id)
        .group_by(Finding.type)
    )
    category_distribution = {row[0]: row[1] for row in category_query.all()}

    # 5. Lifecycle Status (across latest completed runs)
    lifecycle_query = (
        db.query(Finding.lifecycle_status, func.count(Finding.id))
        .join(latest_run_subq, Finding.review_run_id == latest_run_subq.c.max_run_id)
        .group_by(Finding.lifecycle_status)
    )
    lifecycle_distribution = {row[0]: row[1] for row in lifecycle_query.all()}

    # 6. Total Repositories
    total_repositories = db.query(Repository).join(Project).filter(Project.organization_id == organization_id).count()

    return {
        "period_days": days,
        "total_repositories": total_repositories,
        "total_reviews": total_reviews,
        "average_risk_score": round(avg_risk_score, 1),
        "findings_by_severity": severity_distribution,
        "findings_by_category": category_distribution,
        "findings_by_lifecycle": lifecycle_distribution,
    }
