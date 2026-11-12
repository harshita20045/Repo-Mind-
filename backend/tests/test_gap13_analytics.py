import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun, RiskAssessment, Finding
from backend.app.analytics.service import get_organization_analytics


def _setup_org_project_repo(db: Session, num: int = 1):
    org = Organization(name=f"Analytics Org {num}")
    db.add(org)
    db.flush()

    project = Project(name=f"Analytics Proj {num}", organization_id=org.id)
    db.add(project)
    db.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id=f"gh_ana_{num}",
        github_owner="testowner",
        github_name=f"testrepo_{num}",
    )
    db.add(repo)
    db.flush()
    db.commit()
    return org, project, repo


def test_gap_13_analytics_counts_distinct_prs_not_all_runs(db_session: Session):
    """
    GAP-13: When a single PR has 4 review runs (e.g. 2 completed on consecutive commits,
    1 superseded, 1 failed), total_reviews must count exactly 1 unique PR reviewed,
    and findings/risk metrics must reflect the latest completed review run.
    """
    org, project, repo = _setup_org_project_repo(db_session, num=10)

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_10_gh",
        github_number=10,
        title="Multi-commit PR",
        head_sha="sha_latest",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    now = datetime.now(timezone.utc)

    # Run 1: completed, risk score = 40, has 3 findings
    run1 = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_1",
        status="completed",
        completed_at=now - timedelta(days=2),
    )
    db_session.add(run1)
    db_session.flush()
    db_session.add(RiskAssessment(review_run_id=run1.id, score=40, level="medium", factors={}))
    for i in range(3):
        db_session.add(Finding(
            review_run_id=run1.id,
            type="security",
            severity="medium",
            title=f"Old Sec {i}",
            explanation="Old exp",
            confidence=0.8,
            lifecycle_status="new",
        ))

    # Run 2: superseded, risk score = 70
    run2 = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_2",
        status="superseded",
        completed_at=now - timedelta(days=1),
    )
    db_session.add(run2)

    # Run 3: completed (LATEST COMPLETED RUN), risk score = 20, 1 finding
    run3 = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_latest",
        status="completed",
        completed_at=now - timedelta(hours=2),
    )
    db_session.add(run3)
    db_session.flush()
    db_session.add(RiskAssessment(review_run_id=run3.id, score=20, level="low", factors={}))
    db_session.add(Finding(
        review_run_id=run3.id,
        type="security",
        severity="low",
        title="Latest Sec",
        explanation="Latest exp",
        confidence=0.9,
        lifecycle_status="persistent",
    ))

    db_session.commit()

    # Query analytics
    analytics = get_organization_analytics(db_session, org.id, days=30)

    # Total PRs reviewed must be 1, NOT 2 or 3!
    assert analytics["total_reviews"] == 1

    # Average risk score must be 20.0 (from latest completed run3), NOT (40+20)/2 = 30.0!
    assert analytics["average_risk_score"] == 20.0

    # Findings distribution must only include run3 (1 finding of severity="low"), NOT run1's 3 medium findings!
    assert analytics["findings_by_severity"].get("low") == 1
    assert analytics["findings_by_severity"].get("medium") is None


def test_gap_13_pr_without_completed_runs_excluded_from_reviews(db_session: Session):
    """
    GAP-13: A PR that only has pending, failed, or superseded runs must not count
    toward total_reviews.
    """
    org, project, repo = _setup_org_project_repo(db_session, num=11)

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_11_gh",
        github_number=11,
        title="Failed/Superseded PR",
        head_sha="sha_broken",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_broken",
        status="superseded",
        completed_at=datetime.now(timezone.utc),
    )
    db_session.add(run)
    db_session.commit()

    analytics = get_organization_analytics(db_session, org.id, days=30)
    assert analytics["total_reviews"] == 0
    assert analytics["average_risk_score"] == 0.0


def test_gap_13_time_window_boundary_filtering(db_session: Session):
    """
    GAP-13: A completed review run older than the time window (days) must be excluded.
    """
    org, project, repo = _setup_org_project_repo(db_session, num=12)

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_12_gh",
        github_number=12,
        title="Old PR",
        head_sha="sha_ancient",
        created_at=datetime.now(timezone.utc) - timedelta(days=60),
    )
    db_session.add(pr)
    db_session.commit()

    # Completed 45 days ago
    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_ancient",
        status="completed",
        completed_at=datetime.now(timezone.utc) - timedelta(days=45),
    )
    db_session.add(run)
    db_session.flush()
    db_session.add(RiskAssessment(review_run_id=run.id, score=85, level="critical", factors={}))
    db_session.commit()

    # For 30 days window: should be 0
    analytics_30d = get_organization_analytics(db_session, org.id, days=30)
    assert analytics_30d["total_reviews"] == 0

    # For 60 days window: should be 1
    analytics_60d = get_organization_analytics(db_session, org.id, days=60)
    assert analytics_60d["total_reviews"] == 1
    assert analytics_60d["average_risk_score"] == 85.0


def test_gap_13_higher_id_completed_earlier_lower_id_completed_later(db_session: Session):
    """
    GAP-13 Requirement 1:
    A regression test where a higher-ID run completed earlier than a lower-ID run.
    Verify that the lower-ID run is selected because it completed later (completed_at DESC, id DESC).
    """
    org, project, repo = _setup_org_project_repo(db_session, num=13)

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id="pr_13_gh",
        github_number=13,
        title="Out of Order Completed PR",
        head_sha="sha_unordered",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(pr)
    db_session.commit()

    now = datetime.now(timezone.utc)

    # Run A (lower ID): created earlier, but finished LATER (1 hour ago) with risk=15, 1 low finding
    run_a = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_unordered",
        status="completed",
        completed_at=now - timedelta(hours=1),
    )
    db_session.add(run_a)
    db_session.flush()
    db_session.add(RiskAssessment(review_run_id=run_a.id, score=15, level="low", factors={}))
    db_session.add(Finding(
        review_run_id=run_a.id,
        type="security",
        severity="low",
        title="Low Finding Run A",
        explanation="Completed later",
        confidence=0.9,
        lifecycle_status="new",
    ))

    # Run B (higher ID): created later, but finished EARLIER (5 hours ago) with risk=95, 1 critical finding
    run_b = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_unordered",
        status="completed",
        completed_at=now - timedelta(hours=5),
    )
    db_session.add(run_b)
    db_session.flush()
    db_session.add(RiskAssessment(review_run_id=run_b.id, score=95, level="critical", factors={}))
    db_session.add(Finding(
        review_run_id=run_b.id,
        type="security",
        severity="critical",
        title="Critical Finding Run B",
        explanation="Completed earlier",
        confidence=0.9,
        lifecycle_status="new",
    ))
    db_session.commit()

    assert run_b.id > run_a.id
    assert run_a.completed_at > run_b.completed_at

    # Analytics query must select run_a (lower ID, completed later), NOT run_b (higher ID)!
    analytics = get_organization_analytics(db_session, org.id, days=30)

    assert analytics["total_reviews"] == 1
    assert analytics["average_risk_score"] == 15.0
    assert analytics["findings_by_severity"].get("low") == 1
    assert analytics["findings_by_severity"].get("critical") is None
