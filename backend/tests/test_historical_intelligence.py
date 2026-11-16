"""
Tests for RepoMind Historical Code Intelligence — Stage 11.

Verifies:
1. ADR Markdown parsing & indexing (extracting ADR number, title, status, decision, reason).
2. Commit mining & bugfix detection heuristics.
3. Recurring issue hotspot calculation & severity scoring.
4. Historical PR search (keyword, file path, state, author).
5. Previous changes & original decision search with supporting evidence.
6. Similar resolved bug retrieval.
7. Change comparison with historical evolution & hotspot warning.
8. Zero-fabrication check (never invents decisions; explicit empty state).
9. Multi-tenant organization isolation (403 Forbidden for unauthorized org).
10. REST API endpoints.
"""
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum
from backend.app.organizations.models import Project, Repository
from backend.app.github.models import PullRequest, PullRequestFile, PullRequestCommit
from backend.app.review.models import ReviewRun, Finding, HumanDecision
from backend.app.history.models import (
    ArchitectureDecisionRecord,
    HistoricalCommitRecord,
    RecurringIssueHotspot,
)
from backend.app.history.indexer import (
    parse_and_index_adrs,
    mine_and_index_commits,
    compute_and_index_hotspots,
)
from backend.app.history.service import (
    search_historical_prs,
    search_previous_changes,
    get_recurring_issues,
    get_relevant_adrs,
    get_similar_resolved_bugs,
    compare_changes_with_history,
)


@pytest.fixture
def history_setup(db_session):
    """Sets up an organization, project, repository, PRs, findings, and commits."""
    # 1. Organization & Project
    org = Organization(name="HistoryOrg")
    db_session.add(org)
    db_session.commit()

    user = User(
        email="dev@historyorg.com",
        password_hash="pw",
    )
    db_session.add(user)
    db_session.commit()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        role=RoleEnum.ORG_ADMIN,
    )
    db_session.add(membership)

    project = Project(
        name="Core Engine",
        organization_id=org.id,
    )
    db_session.add(project)
    db_session.commit()

    repo = Repository(
        project_id=project.id,
        github_repository_id="repo_hist_intel_1",
        github_owner="historyorg",
        github_name="engine-service",
        default_branch="main",
        index_status="indexed",
    )
    db_session.add(repo)
    db_session.commit()

    # 2. Historical Pull Requests
    pr1 = PullRequest(
        repository_id=repo.id,
        github_pr_id="gh_pr_101",
        github_number=101,
        title="Fix race condition in session authenticator",
        description="Resolved concurrency deadlock when renewing expired tokens under high load.",
        state="merged",
        github_author_login="alice",
        head_sha="sha101aaa",
        base_sha="sha100base",
        source_branch="fix-deadlock",
        target_branch="main",
        created_at=datetime(2025, 1, 10, tzinfo=timezone.utc),
        updated_at=datetime(2025, 1, 11, tzinfo=timezone.utc),
        merged_at=datetime(2025, 1, 11, tzinfo=timezone.utc),
    )
    pr2 = PullRequest(
        repository_id=repo.id,
        github_pr_id="gh_pr_102",
        github_number=102,
        title="Refactor billing calculations and discount rules",
        description="Migrate invoice calculation to decimal precision to avoid floating point drift.",
        state="closed",
        github_author_login="bob",
        head_sha="sha102bbb",
        base_sha="sha101base",
        source_branch="feature-billing",
        target_branch="main",
        created_at=datetime(2025, 2, 1, tzinfo=timezone.utc),
        updated_at=datetime(2025, 2, 2, tzinfo=timezone.utc),
    )
    db_session.add_all([pr1, pr2])
    db_session.commit()

    # 3. Pull Request Files
    prf1 = PullRequestFile(
        pull_request_id=pr1.id,
        file_path="backend/app/auth/service.py",
        status="modified",
        additions=15,
        deletions=4,
        patch_data="@@ -20,4 +20,15 @@\n+with session_lock:\n+    token.refresh()",
    )
    prf2 = PullRequestFile(
        pull_request_id=pr2.id,
        file_path="backend/app/billing/calculator.py",
        status="modified",
        additions=30,
        deletions=10,
        patch_data="@@ -10,10 +10,30 @@\n-amount * 0.1\n+Decimal(amount) * Decimal('0.10')",
    )
    db_session.add_all([prf1, prf2])
    db_session.commit()

    # 4. Pull Request Commits
    c1 = PullRequestCommit(
        pull_request_id=pr1.id,
        sha="c101a01",
        message="fix(auth): prevent deadlock in token renewal by introducing thread-safe lock",
        author="alice",
        committer="alice",
        created_at=datetime(2025, 1, 10, 14, 0, tzinfo=timezone.utc),
    )
    c2 = PullRequestCommit(
        pull_request_id=pr1.id,
        sha="c101a02",
        message="test(auth): add concurrent session renewal test cases",
        author="alice",
        committer="alice",
        created_at=datetime(2025, 1, 10, 16, 0, tzinfo=timezone.utc),
    )
    c3 = PullRequestCommit(
        pull_request_id=pr2.id,
        sha="c102b01",
        message="feat(billing): use Decimal for invoice tax rounding",
        author="bob",
        committer="bob",
        created_at=datetime(2025, 2, 1, 10, 0, tzinfo=timezone.utc),
    )
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    # 5. Review Run & Findings
    run = ReviewRun(
        pull_request_id=pr1.id,
        commit_sha="sha101aaa",
        status="completed",
        completed_at=datetime(2025, 1, 10, 15, 0, tzinfo=timezone.utc),
    )
    db_session.add(run)
    db_session.commit()

    finding1 = Finding(
        review_run_id=run.id,
        rule_source="SEC-001",
        type="security",
        severity="high",
        confidence=0.95,
        title="Unsynchronized session token state update",
        file="backend/app/auth/service.py",
        line=24,
        explanation="Direct mutation without lock causes race condition across async tasks.",
        recommendation="Guard with asyncio.Lock or database row-level locking.",
        status="resolved",
    )
    finding2 = Finding(
        review_run_id=run.id,
        rule_source="PERF-002",
        type="performance",
        severity="medium",
        confidence=0.88,
        title="Unindexed token lookup by session ID",
        file="backend/app/auth/service.py",
        line=45,
        explanation="Full table scan on high-traffic authentication route.",
        recommendation="Add btree index on sessions(token).",
        status="resolved",
    )
    db_session.add_all([finding1, finding2])

    decision = HumanDecision(
        review_run_id=run.id,
        user_id=user.id,
        action="approve",
        note="Deadlock addressed with mutex lock. Verified against stress test suite.",
    )
    db_session.add(decision)
    db_session.commit()

    # 6. Manual ADR
    adr1 = ArchitectureDecisionRecord(
        repository_id=repo.id,
        adr_number="ADR-099",
        title="Session Token Synchronization Strategy",
        status="Confirmed",
        decision="All session state mutations must use centralized atomic redis or database row locks.",
        context="Distributed worker processes concurrently re-authenticated user tokens.",
        reason="Prevents race conditions, token invalidation glitches, and replay attacks.",
        consequences="Slight increase in renewal latency (~2ms) with guaranteed linear consistency.",
        file_source="docs/02-architecture/architecture-decisions.md",
        affected_modules=["backend/app/auth", "backend/app/auth/service.py"],
    )
    db_session.add(adr1)
    db_session.commit()

    return {
        "org": org,
        "user": user,
        "project": project,
        "repo": repo,
        "pr1": pr1,
        "pr2": pr2,
        "adr1": adr1,
    }


# =====================================================================
# 1. ADR PARSING & INDEXING TESTS
# =====================================================================

def test_adr_parsing_from_docs(db_session, history_setup):
    """Verify that ADRs are parsed from markdown documentation and indexed into DB."""
    repo = history_setup["repo"]
    count = parse_and_index_adrs(db=db_session, repository_id=repo.id)
    assert count >= 1

    # Check indexed ADRs
    adrs = db_session.query(ArchitectureDecisionRecord).filter_by(repository_id=repo.id).all()
    assert len(adrs) >= 1
    # Check that parsed ADR has required fields
    for adr in adrs:
        assert adr.adr_number.startswith("ADR-")
        assert len(adr.title) > 0
        assert adr.status in ["Confirmed", "Proposed", "Accepted", "Superseded", "Draft"]
        assert len(adr.decision) > 0


def test_adr_indexing_idempotence(db_session, history_setup):
    """Running indexer repeatedly should update existing records without creating duplicates."""
    repo = history_setup["repo"]
    count1 = parse_and_index_adrs(db=db_session, repository_id=repo.id)
    count2 = parse_and_index_adrs(db=db_session, repository_id=repo.id)
    assert count1 == count2

    # Verify no duplicates
    adr_numbers = [
        a.adr_number
        for a in db_session.query(ArchitectureDecisionRecord).filter_by(repository_id=repo.id).all()
    ]
    assert len(adr_numbers) == len(set(adr_numbers))


# =====================================================================
# 2. COMMIT MINING & BUGFIX DETECTION TESTS
# =====================================================================

def test_commit_mining_and_bugfix_heuristics(db_session, history_setup):
    """Verify commit mining detects bugfixes, original decisions, and evidence."""
    repo = history_setup["repo"]
    mined_count = mine_and_index_commits(db=db_session, repository_id=repo.id)
    assert mined_count >= 2

    # Check mined commits
    commits = db_session.query(HistoricalCommitRecord).filter_by(repository_id=repo.id).all()
    assert len(commits) >= 2

    bugfix_commit = next((c for c in commits if c.is_bugfix), None)
    assert bugfix_commit is not None
    assert "deadlock" in bugfix_commit.message.lower() or "fix" in bugfix_commit.message.lower()
    assert bugfix_commit.original_decision_rationale is not None


# =====================================================================
# 3. RECURRING ISSUE HOTSPOT CALCULATION TESTS
# =====================================================================

def test_recurring_issue_hotspots_calculation(db_session, history_setup):
    """Verify hotspot scoring based on bugfixes and recurring review findings."""
    repo = history_setup["repo"]

    # Pre-populate mined commits and calculate hotspots
    mine_and_index_commits(db=db_session, repository_id=repo.id)
    hotspots_count = compute_and_index_hotspots(db=db_session, repository_id=repo.id)
    assert hotspots_count >= 1

    hotspot = db_session.query(RecurringIssueHotspot).filter_by(
        repository_id=repo.id,
        file_path="backend/app/auth/service.py"
    ).first()
    assert hotspot is not None
    assert hotspot.bugfix_commits_count >= 1
    assert hotspot.recurring_findings_count >= 2
    assert hotspot.hotspot_score > 0
    assert hotspot.severity in ["critical", "high", "medium", "low"]
    assert hotspot.file_path == "backend/app/auth/service.py"


# =====================================================================
# 4. HISTORICAL SEARCH SERVICE TESTS
# =====================================================================

def test_search_historical_prs(db_session, history_setup):
    """Verify filtering PRs by keyword, file path, state, and author."""
    repo = history_setup["repo"]

    # Keyword search
    results_kw = search_historical_prs(db=db_session, repository_id=repo.id, q="race condition")
    assert len(results_kw) == 1
    assert results_kw[0].github_number == 101

    # State filter
    results_closed = search_historical_prs(db=db_session, repository_id=repo.id, state="closed")
    assert len(results_closed) == 1
    assert results_closed[0].github_number == 102

    # File path filter
    results_file = search_historical_prs(
        db=db_session,
        repository_id=repo.id,
        file_path="backend/app/auth/service.py"
    )
    assert len(results_file) == 1
    assert results_file[0].github_number == 101

    # Author filter
    results_author = search_historical_prs(db=db_session, repository_id=repo.id, author="alice")
    assert len(results_author) == 1
    assert results_author[0].github_author_login == "alice"


def test_search_previous_changes(db_session, history_setup):
    """Verify searching commits with bugfix filter."""
    repo = history_setup["repo"]
    mine_and_index_commits(db=db_session, repository_id=repo.id)

    # Bugfix only
    bugfixes = search_previous_changes(db=db_session, repository_id=repo.id, is_bugfix=True)
    assert len(bugfixes) >= 1
    for b in bugfixes:
        assert b.is_bugfix is True
        assert b.message is not None


def test_get_recurring_issues_service(db_session, history_setup):
    """Verify retrieving recurring hotspots sorted by severity."""
    repo = history_setup["repo"]
    mine_and_index_commits(db=db_session, repository_id=repo.id)
    compute_and_index_hotspots(db=db_session, repository_id=repo.id)

    hotspots = get_recurring_issues(db=db_session, repository_id=repo.id)
    assert len(hotspots) >= 1
    assert hotspots[0].hotspot_score >= (hotspots[-1].hotspot_score if len(hotspots) > 1 else 0)


def test_get_relevant_adrs_service(db_session, history_setup):
    """Verify retrieving ADRs relevant to a specific file or module."""
    repo = history_setup["repo"]
    adrs = get_relevant_adrs(
        db=db_session,
        repository_id=repo.id,
        file_path="backend/app/auth/service.py"
    )
    assert len(adrs) >= 1
    assert any(a.adr_number == "ADR-099" for a in adrs)


def test_get_similar_resolved_bugs_service(db_session, history_setup):
    """Verify retrieving prior resolved findings and bugfix commits."""
    repo = history_setup["repo"]
    mine_and_index_commits(db=db_session, repository_id=repo.id)

    bugs = get_similar_resolved_bugs(
        db=db_session,
        repository_id=repo.id,
        file_path="backend/app/auth/service.py"
    )
    assert len(bugs) >= 1
    assert any("token" in b.title.lower() or "deadlock" in b.title.lower() or "session" in b.title.lower() for b in bugs)


# =====================================================================
# 5. CHANGE COMPARISON & ZERO-FABRICATION TESTS
# =====================================================================

def test_compare_changes_with_history_known_file(db_session, history_setup):
    """Verify comparison for a previously problematic module surfaces evidence and ADRs."""
    repo = history_setup["repo"]
    mine_and_index_commits(db=db_session, repository_id=repo.id)
    compute_and_index_hotspots(db=db_session, repository_id=repo.id)

    comparison = compare_changes_with_history(
        db=db_session,
        repository_id=repo.id,
        file_path="backend/app/auth/service.py",
        diff_snippet="+token = session.get_token()\n+token.validate()",
    )
    assert comparison.file_path == "backend/app/auth/service.py"
    assert comparison.is_hotspot is True
    assert comparison.hotspot_score > 0
    assert len(comparison.governing_adrs) >= 1
    assert any(a.adr_number == "ADR-099" for a in comparison.governing_adrs)
    assert len(comparison.historical_changes) >= 1
    for commit in comparison.historical_changes:
        assert commit.original_decision is not None
        assert commit.supporting_evidence is not None


def test_zero_fabrication_on_unknown_file(db_session, history_setup):
    """
    CRITICAL AI PRINCIPLE:
    When no historical evidence exists, NEVER fabricate reasons or ADRs.
    Return clean empty lists with explicit explanation.
    """
    repo = history_setup["repo"]

    comparison = compare_changes_with_history(
        db=db_session,
        repository_id=repo.id,
        file_path="brand_new_module/unseen_feature.py",
    )
    assert comparison.is_hotspot is False
    assert comparison.governing_adrs == []
    assert comparison.historical_changes == []
    assert "No previous recorded changes or governing architecture decisions found" in comparison.summary_guidance


# =====================================================================
# 6. REST API & MULTI-TENANT ISOLATION TESTS
# =====================================================================

def test_api_historical_prs_and_changes(db_session, history_setup):
    """Verify API endpoints return valid JSON models."""
    client = TestClient(app)
    repo = history_setup["repo"]
    user = history_setup["user"]
    mine_and_index_commits(db=db_session, repository_id=repo.id)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        # 1. PRs endpoint
        resp_prs = client.get(f"/repositories/{repo.id}/history/prs?q=race")
        assert resp_prs.status_code == 200
        data_prs = resp_prs.json()
        assert len(data_prs) == 1
        assert data_prs[0]["github_number"] == 101

        # 2. Changes endpoint
        resp_changes = client.get(f"/repositories/{repo.id}/history/changes?is_bugfix=true")
        assert resp_changes.status_code == 200
        data_changes = resp_changes.json()
        assert len(data_changes) >= 1

        # 3. Compare endpoint
        resp_comp = client.post(
            f"/repositories/{repo.id}/history/compare",
            json={"file_path": "backend/app/auth/service.py"}
        )
        assert resp_comp.status_code == 200
        data_comp = resp_comp.json()
        assert data_comp["file_path"] == "backend/app/auth/service.py"
    finally:
        app.dependency_overrides.clear()


def test_api_multi_tenant_authorization_isolation(db_session, history_setup):
    """A user from another organization must be strictly forbidden (403 Forbidden)."""
    client = TestClient(app)
    repo = history_setup["repo"]

    # Create unrelated user in unrelated org
    other_org = Organization(name="OtherOrg")
    db_session.add(other_org)
    db_session.commit()

    other_user = User(
        email="outsider@otherorg.com",
        password_hash="pw",
    )
    db_session.add(other_user)
    db_session.commit()

    other_membership = OrganizationMembership(
        user_id=other_user.id,
        organization_id=other_org.id,
        role=RoleEnum.DEVELOPER,
    )
    db_session.add(other_membership)
    db_session.commit()

    app.dependency_overrides[get_current_user] = lambda: other_user
    app.dependency_overrides[get_db] = lambda: db_session

    try:
        # Attempt accessing repo from HistoryOrg (404/403 to prevent enumeration)
        resp = client.get(f"/repositories/{repo.id}/history/prs")
        assert resp.status_code in (403, 404)

        resp2 = client.post(
            f"/repositories/{repo.id}/history/compare",
            json={"file_path": "backend/app/auth/service.py"}
        )
        assert resp2.status_code in (403, 404)
    finally:
        app.dependency_overrides.clear()
