"""
FastAPI Routes for Historical Code Intelligence — RepoMind 2.0.

Provides endpoints to:
1. Search historical PRs
2. Search previous code changes & commits
3. Identify recurring issue hotspots
4. Retrieve relevant Architecture Decision Records (ADRs)
5. Identify previously resolved similar bugs
6. Compare current changes with history and original decisions
7. Trigger automated historical indexing
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.auth.permissions import Permission, assert_org_permission
from backend.app.organizations.models import Repository
from backend.app.history.schemas import (
    HistoricalPRResponse,
    HistoricalCommitResponse,
    RecurringHotspotResponse,
    ADRResponse,
    SimilarBugResponse,
    ChangeComparisonRequest,
    ChangeComparisonResponse,
    HistoricalIndexRequest,
    HistoricalIndexResponse,
)
from backend.app.history.service import (
    search_historical_prs,
    search_previous_changes,
    get_recurring_issues,
    get_relevant_adrs,
    get_similar_resolved_bugs,
    compare_changes_with_history,
)
from backend.app.history.indexer import (
    parse_and_index_adrs,
    mine_and_index_commits,
    compute_and_index_hotspots,
)

router = APIRouter(prefix="/repositories/{repository_id}/history", tags=["historical-intelligence"])


def _get_authorized_repo(repository_id: int, user: User, db: Session) -> Repository:
    """Verifies that the repository exists and user has REPOS_READ permission in its organization."""
    repo = db.get(Repository, repository_id)
    if not repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )
    assert_org_permission(db, user.id, repo.project.organization_id, Permission.REPOS_READ)
    return repo


@router.get("/prs", response_model=List[HistoricalPRResponse])
def get_historical_prs(
    repository_id: int,
    q: Optional[str] = Query(None, description="Keyword search in PR title or description"),
    file_path: Optional[str] = Query(None, description="Filter by touched file path"),
    state: Optional[str] = Query(None, description="Filter by state (merged, closed, open, all)"),
    author: Optional[str] = Query(None, description="Filter by author username"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search historical pull requests with tenant scoping."""
    repo = _get_authorized_repo(repository_id, user, db)
    return search_historical_prs(
        db=db,
        repository_id=repo.id,
        q=q,
        file_path=file_path,
        state=state,
        author=author,
        limit=limit,
        offset=offset,
    )


@router.get("/changes", response_model=List[HistoricalCommitResponse])
def get_previous_changes(
    repository_id: int,
    q: Optional[str] = Query(None, description="Search in commit message or SHA"),
    file_path: Optional[str] = Query(None, description="Filter by touched file path"),
    is_bugfix: Optional[bool] = Query(None, description="Filter by bugfix commits only"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search previous code changes, commit logs, and original decisions."""
    repo = _get_authorized_repo(repository_id, user, db)
    return search_previous_changes(
        db=db,
        repository_id=repo.id,
        q=q,
        file_path=file_path,
        is_bugfix=is_bugfix,
        limit=limit,
        offset=offset,
    )


@router.get("/recurring-issues", response_model=List[RecurringHotspotResponse])
def get_recurring_issue_hotspots(
    repository_id: int,
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    min_score: Optional[float] = Query(None, description="Filter by minimum hotspot score"),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List recurring issue hotspots and high-churn bug modules."""
    repo = _get_authorized_repo(repository_id, user, db)
    return get_recurring_issues(
        db=db,
        repository_id=repo.id,
        severity=severity,
        min_score=min_score,
        limit=limit,
    )


@router.get("/adrs", response_model=List[ADRResponse])
def get_architecture_decision_records(
    repository_id: int,
    file_path: Optional[str] = Query(None, description="Filter by affected file path"),
    module: Optional[str] = Query(None, description="Filter by module or architectural keyword"),
    status: Optional[str] = Query(None, description="Filter by status (Confirmed, Proposed, etc.)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve Architecture Decision Records governing the repository or specific file."""
    repo = _get_authorized_repo(repository_id, user, db)
    return get_relevant_adrs(
        db=db,
        repository_id=repo.id,
        file_path=file_path,
        module=module,
        status=status,
    )


@router.get("/similar-bugs", response_model=List[SimilarBugResponse])
def get_similar_bugs(
    repository_id: int,
    file_path: Optional[str] = Query(None, description="Target file path"),
    symbol: Optional[str] = Query(None, description="Target function or class symbol"),
    category: Optional[str] = Query(None, description="Bug or finding category"),
    limit: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve previously resolved similar bugs and patches with supporting evidence."""
    repo = _get_authorized_repo(repository_id, user, db)
    return get_similar_resolved_bugs(
        db=db,
        repository_id=repo.id,
        file_path=file_path,
        symbol=symbol,
        category=category,
        limit=limit,
    )


@router.post("/compare", response_model=ChangeComparisonResponse)
def compare_change_with_history(
    repository_id: int,
    request: ChangeComparisonRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Compare current changes / PR diff with historical changes and original decisions.
    Surfaces why changes were made, supporting evidence, and hotspot warnings.
    """
    repo = _get_authorized_repo(repository_id, user, db)
    return compare_changes_with_history(
        db=db,
        repository_id=repo.id,
        file_path=request.file_path,
        diff_snippet=request.diff_snippet,
        pull_request_id=request.pull_request_id,
    )


@router.post("/index", response_model=HistoricalIndexResponse)
def trigger_historical_index(
    repository_id: int,
    request: HistoricalIndexRequest = HistoricalIndexRequest(),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger on-demand indexing of ADRs, commit mining, and recurring hotspot calculation."""
    repo = _get_authorized_repo(repository_id, user, db)

    adrs_count = 0
    commits_count = 0
    hotspots_count = 0

    if request.parse_adrs:
        adrs_count = parse_and_index_adrs(db=db, repository_id=repo.id)
    if request.mine_commits:
        commits_count = mine_and_index_commits(db=db, repository_id=repo.id)
    if request.compute_hotspots:
        hotspots_count = compute_and_index_hotspots(db=db, repository_id=repo.id)

    return HistoricalIndexResponse(
        status="completed",
        indexed_adrs_count=adrs_count,
        indexed_commits_count=commits_count,
        hotspots_detected_count=hotspots_count,
    )

