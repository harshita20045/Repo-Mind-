import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun
from worker.worker import recover_stale_running_jobs, WORKER_LEASE_TIMEOUT_SECONDS, MAX_REVIEW_RUN_RETRIES


def _setup_repo_and_pr(db: Session, pr_number: int = 200):
    org = Organization(name=f"Worker Recovery Org {pr_number}")
    db.add(org)
    db.flush()

    project = Project(name=f"Worker Recovery Proj {pr_number}", organization_id=org.id)
    db.add(project)
    db.flush()

    repo = Repository(
        project_id=project.id,
        github_repository_id=f"gh_rec_{pr_number}",
        github_owner="testowner",
        github_name=f"testrepo_{pr_number}",
    )
    db.add(repo)
    db.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_pr_id=f"gh_pr_{pr_number}",
        github_number=pr_number,
        title="Recovery Test PR",
        head_sha="sha_latest",
        created_at=datetime.now(timezone.utc),
    )
    db.add(pr)
    db.commit()
    return org, project, repo, pr


def test_gap_09_stale_running_job_recovered_to_pending(db_session: Session):
    """
    GAP-09: A job stuck in status='running' whose heartbeat expired must be safely
    re-queued to 'pending' with incremented retry_count.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=201)

    expired_time = datetime.now(timezone.utc) - timedelta(seconds=WORKER_LEASE_TIMEOUT_SECONDS + 10)
    stale_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        started_at=expired_time,
        heartbeat_at=expired_time,
        retry_count=0,
    )
    db_session.add(stale_run)
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session)
    assert recovered == 1

    db_session.refresh(stale_run)
    assert stale_run.status == "pending"
    assert stale_run.retry_count == 1
    assert "lease timeout" in stale_run.progress_message.lower()


def test_gap_09_active_heartbeat_job_is_not_recovered(db_session: Session):
    """
    GAP-09: An actively running job with a fresh heartbeat must NOT be touched or interrupted.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=202)

    fresh_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    active_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        started_at=fresh_time,
        heartbeat_at=fresh_time,
        retry_count=0,
    )
    db_session.add(active_run)
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session)
    assert recovered == 0

    db_session.refresh(active_run)
    assert active_run.status == "running"
    assert active_run.retry_count == 0


def test_gap_09_abandoned_job_exceeding_max_retries_fails(db_session: Session):
    """
    GAP-09: An abandoned job that has already reached MAX_REVIEW_RUN_RETRIES must
    transition to 'failed' rather than looping indefinitely.
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=203)

    expired_time = datetime.now(timezone.utc) - timedelta(seconds=WORKER_LEASE_TIMEOUT_SECONDS + 20)
    failing_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        started_at=expired_time,
        heartbeat_at=expired_time,
        retry_count=MAX_REVIEW_RUN_RETRIES,
    )
    db_session.add(failing_run)
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session)
    assert recovered == 1

    db_session.refresh(failing_run)
    assert failing_run.status == "failed"
    assert "exceeded maximum retries" in failing_run.error_message


def test_gap_09_abandoned_job_with_superseded_sha_transitions_to_superseded(db_session: Session):
    """
    GAP-09: An abandoned job whose PR head_sha has already moved to a newer commit
    must NOT be re-queued to pending; it must transition to 'superseded' (GAP-08).
    """
    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=204)
    pr.head_sha = "sha_brand_new"
    db_session.commit()

    expired_time = datetime.now(timezone.utc) - timedelta(seconds=WORKER_LEASE_TIMEOUT_SECONDS + 30)
    obsolete_abandoned_run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha="sha_old_dead",
        status="running",
        started_at=expired_time,
        heartbeat_at=expired_time,
        retry_count=0,
    )
    db_session.add(obsolete_abandoned_run)
    db_session.commit()

    recovered = recover_stale_running_jobs(db_session)
    assert recovered == 1

    db_session.refresh(obsolete_abandoned_run)
    assert obsolete_abandoned_run.status == "superseded"
    assert "superseded by newer commit" in obsolete_abandoned_run.progress_message.lower()


def test_gap_09_heartbeat_renewal_and_token_validation(db_session: Session):
    """
    GAP-09: Periodic heartbeats must update heartbeat_at and progress message
    only when worker ownership (claim_token) is valid.
    """
    from backend.app.review.service import _update_progress

    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=205)

    old_heartbeat = datetime.now(timezone.utc) - timedelta(seconds=60)
    run = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        claim_token="valid_token_xyz",
        heartbeat_at=old_heartbeat,
    )
    db_session.add(run)
    db_session.commit()

    # Successful heartbeat renewal
    success = _update_progress(db_session, run, "Step 2: Analysis", claim_token="valid_token_xyz")
    assert success is True
    db_session.refresh(run)
    assert run.progress_message == "Step 2: Analysis"
    assert run.heartbeat_at > old_heartbeat

    # Rejected heartbeat when token does not match
    rejected = _update_progress(db_session, run, "Step 3: Stale", claim_token="different_token")
    assert rejected is False
    db_session.refresh(run)
    assert run.progress_message == "Step 2: Analysis"  # Unchanged


def test_gap_09_concurrent_worker_recovery_postgres_skip_locked(db_session: Session):
    """
    GAP-09: Concurrency integration test using separate PostgreSQL sessions and concurrent threads.
    Verifies that recover_stale_running_jobs() uses SELECT FOR UPDATE SKIP LOCKED
    so multiple concurrent workers never double-recover or conflict on the same expired job.
    """
    from concurrent.futures import ThreadPoolExecutor
    from sqlalchemy.orm import sessionmaker

    org, project, repo, pr = _setup_repo_and_pr(db_session, pr_number=206)
    expired_time = datetime.now(timezone.utc) - timedelta(seconds=WORKER_LEASE_TIMEOUT_SECONDS + 50)

    run1 = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        started_at=expired_time,
        heartbeat_at=expired_time,
        retry_count=0,
        claim_token="token_run1",
    )
    run2 = ReviewRun(
        pull_request_id=pr.id,
        commit_sha=pr.head_sha,
        status="running",
        started_at=expired_time,
        heartbeat_at=expired_time,
        retry_count=0,
        claim_token="token_run2",
    )
    db_session.add_all([run1, run2])
    db_session.commit()
    run1_id = run1.id
    run2_id = run2.id

    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=db_session.bind)

    def worker_recovery_task():
        with session_factory() as session:
            count = recover_stale_running_jobs(session)
            return count

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_recovery_task)
        f2 = executor.submit(worker_recovery_task)
        count1 = f1.result()
        count2 = f2.result()

    # The total number of recovered jobs across both workers must equal exactly 2
    assert count1 + count2 == 2

    # Verify both runs are now pending with retry_count=1 and claim_token=None in DB
    with session_factory() as session:
        r1 = session.get(ReviewRun, run1_id)
        r2 = session.get(ReviewRun, run2_id)
        assert r1.status == "pending"
        assert r1.retry_count == 1
        assert r1.claim_token is None

        assert r2.status == "pending"
        assert r2.retry_count == 1
        assert r2.claim_token is None
