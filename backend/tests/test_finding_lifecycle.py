import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.auth.models import Organization
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest
from backend.app.review.models import ReviewRun, Finding
from backend.app.review.schemas import FindingSchema
from backend.app.review.evidence import ValidatedFinding
from backend.app.review.service import _persist_validated_findings


def _setup_test_pr(db: Session):
    org = Organization(name="Finding Lifecycle Org")
    db.add(org)
    db.flush()

    proj = Project(organization_id=org.id, name="Finding Lifecycle Proj")
    db.add(proj)
    db.flush()

    repo = Repository(
        project_id=proj.id,
        github_repository_id="gh_finding_repo",
        github_owner="org",
        github_name="repo"
    )
    db.add(repo)
    db.flush()

    pr = PullRequest(
        repository_id=repo.id,
        github_number=42,
        head_sha="sha1",
        github_pr_id="pr_42",
        title="Lifecycle PR",
        created_at=datetime.now(timezone.utc)
    )
    db.add(pr)
    db.flush()
    db.commit()
    return pr


def _make_validated_finding(file: str, line: int, category: str, title: str, problem: str):
    schema = FindingSchema(
        category=category,
        severity="high",
        file=file,
        line=line,
        title=title,
        problem=problem,
        evidence="Rule 1",
        recommendation="Fix it",
        confidence=0.9
    )
    return ValidatedFinding(
        finding=schema,
        adjusted_confidence=0.9,
        evidence_status="supported",
        supporting_evidence=[],
        contradicting_evidence=[]
    )


def test_def_03_no_infinite_zombie_duplication_across_runs(db_session: Session):
    """
    DEF-03: Multi-run reviews must NOT endlessly duplicate resolved findings.
    Run 1: Finding A, Finding B (both new)
    Run 2: Finding A resolved (fixed in PR), Finding B still present (persistent)
    Run 3: Finding B also resolved, 0 active findings.
           Crucially, Finding A must NOT be duplicated again in Run 3!
    Run 4: No new findings. Run 4 should have 0 findings (no zombie duplication).
    """
    pr = _setup_test_pr(db_session)

    # --- Run 1 ---
    run1 = ReviewRun(pull_request_id=pr.id, commit_sha="sha1", status="completed")
    db_session.add(run1)
    db_session.commit()

    vf_a = _make_validated_finding("auth.py", 10, "security", "SQL Injection", "Unescaped query")
    vf_b = _make_validated_finding("utils.py", 50, "standards_violation", "NPE risk", "Null check missing")
    findings_run1 = _persist_validated_findings(db_session, run1, [vf_a, vf_b])
    db_session.commit()

    assert len(findings_run1) == 2
    assert all(f.lifecycle_status == "new" for f in findings_run1)
    assert all(f.status == "open" for f in findings_run1)

    # --- Run 2: Developer fixed Finding A; Finding B persists ---
    run2 = ReviewRun(pull_request_id=pr.id, commit_sha="sha2", status="completed")
    db_session.add(run2)
    db_session.commit()

    findings_run2 = _persist_validated_findings(db_session, run2, [vf_b])
    db_session.commit()

    # Run 2 should have 2 findings: 1 persistent (B) and 1 newly resolved (A)
    assert len(findings_run2) == 2
    f_b_run2 = next(f for f in findings_run2 if f.file == "utils.py")
    f_a_run2 = next(f for f in findings_run2 if f.file == "auth.py")
    assert f_b_run2.lifecycle_status == "persistent"
    assert f_b_run2.status == "open"
    assert f_a_run2.lifecycle_status == "resolved"
    assert f_a_run2.status == "resolved"

    # --- Run 3: Developer fixed Finding B as well; 0 findings reported by LLM ---
    run3 = ReviewRun(pull_request_id=pr.id, commit_sha="sha3", status="completed")
    db_session.add(run3)
    db_session.commit()

    findings_run3 = _persist_validated_findings(db_session, run3, [])
    db_session.commit()

    # Run 3 should ONLY resolve Finding B! Finding A was ALREADY resolved in Run 2 and must NOT be duplicated!
    assert len(findings_run3) == 1
    assert findings_run3[0].file == "utils.py"
    assert findings_run3[0].lifecycle_status == "resolved"
    assert findings_run3[0].status == "resolved"

    # --- Run 4: Another commit pushed with no findings ---
    run4 = ReviewRun(pull_request_id=pr.id, commit_sha="sha4", status="completed")
    db_session.add(run4)
    db_session.commit()

    findings_run4 = _persist_validated_findings(db_session, run4, [])
    db_session.commit()

    # Run 4 should have 0 findings! Absolutely NO zombie cloned records!
    assert len(findings_run4) == 0


def test_def_03_reopened_finding_lifecycle_on_regression(db_session: Session):
    """
    DEF-03: When a previously resolved finding re-appears in a later run,
    it should be tagged as 'reopened' (regression) rather than 'new' or 'persistent'.
    """
    pr = _setup_test_pr(db_session)

    # Run 1: Finding A introduced
    run1 = ReviewRun(pull_request_id=pr.id, commit_sha="sha1", status="completed")
    db_session.add(run1)
    db_session.commit()

    vf_a = _make_validated_finding("auth.py", 10, "security", "SQL Injection", "Unescaped query")
    _persist_validated_findings(db_session, run1, [vf_a])
    db_session.commit()

    # Run 2: Finding A resolved (fixed)
    run2 = ReviewRun(pull_request_id=pr.id, commit_sha="sha2", status="completed")
    db_session.add(run2)
    db_session.commit()

    findings_run2 = _persist_validated_findings(db_session, run2, [])
    db_session.commit()
    assert len(findings_run2) == 1
    assert findings_run2[0].lifecycle_status == "resolved"

    # Run 3: Developer accidentally re-introduced Finding A (regression)
    run3 = ReviewRun(pull_request_id=pr.id, commit_sha="sha3", status="completed")
    db_session.add(run3)
    db_session.commit()

    findings_run3 = _persist_validated_findings(db_session, run3, [vf_a])
    db_session.commit()

    assert len(findings_run3) == 1
    assert findings_run3[0].file == "auth.py"
    assert findings_run3[0].lifecycle_status == "reopened"
    assert findings_run3[0].status == "open"

