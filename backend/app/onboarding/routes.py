"""
FastAPI Routes for Developer Onboarding & Codebase Blueprint — RepoMind 2.0.

Provides endpoints for:
  - GET /repositories/{repository_id}/onboarding/blueprint (REPOS_READ)
  - POST /repositories/{repository_id}/onboarding/blueprint/refresh (REPOS_INDEX + Team Lead+)
  - GET /repositories/{repository_id}/onboarding/progress (Private to authenticated user)
  - PUT /repositories/{repository_id}/onboarding/progress (Private to authenticated user)
"""
import re
import logging
from typing import Optional, Set
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.auth.models import User, RoleEnum, OrganizationMembership
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.permissions import (
    Permission,
    assert_org_permission,
    ROLE_HIERARCHY,
)
from backend.app.organizations.models import Repository
from backend.app.onboarding.models import RepositoryBlueprint
from backend.app.onboarding.schemas import (
    RepositoryBlueprintResponse,
    UserProgressResponse,
    UpdateProgressRequest,
)
from backend.app.onboarding.service import (
    OnboardingService,
    UnindexedRepositoryError,
    GenerationInProgressError,
    BlueprintGenerationError,
    GroundingValidationError,
    OnboardingServiceError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["onboarding"])

MILESTONE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+$")


def _get_repo_and_verify_access(
    db: Session,
    user_id: int,
    repository_id: int,
    required_permission: Permission,
    min_role: Optional[RoleEnum] = None,
) -> Repository:
    """
    Verify repository existence and enforce organizational RBAC & role hierarchy.
    Returns Repository if authorized; raises 404 or 403 otherwise.
    """
    repo = db.get(Repository, repository_id)
    if not repo or not repo.project:
        # Uniform 404 prevents repository enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found or access denied",
        )

    org_id = repo.project.organization_id

    # 1. Check atomic permission
    assert_org_permission(db, user_id, org_id, required_permission)

    # 2. Check role hierarchy if minimum role specified
    if min_role:
        membership = db.query(OrganizationMembership).filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == org_id,
        ).first()
        if not membership:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization membership not found",
            )
        role_val = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        user_level = ROLE_HIERARCHY.get(role_val, 0)
        required_level = ROLE_HIERARCHY.get(min_role.value, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {min_role.value} role or higher",
            )

    return repo


# ---------------------------------------------------------------------------
# 1. Blueprint Retrieval & Generation
# ---------------------------------------------------------------------------

@router.get(
    "/repositories/{repository_id}/onboarding/blueprint",
    response_model=RepositoryBlueprintResponse,
    status_code=status.HTTP_200_OK,
)
def get_repository_blueprint(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve the cached Codebase Blueprint for a repository.
    Generates blueprint on-demand if no cache exists and repository is indexed.
    Requires REPOS_READ permission in the owning organization.
    """
    _get_repo_and_verify_access(db, current_user.id, repository_id, Permission.REPOS_READ)

    service = OnboardingService(db)
    try:
        return service.get_or_generate_blueprint(repository_id=repository_id, force_refresh=False)
    except UnindexedRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except GenerationInProgressError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except (BlueprintGenerationError, GroundingValidationError, OnboardingServiceError) as exc:
        logger.error("Error retrieving blueprint for repo %d: %s", repository_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve or generate repository blueprint. Please try again later.",
        )
    except Exception as exc:
        logger.error("Unexpected error retrieving blueprint for repo %d: %s", repository_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during blueprint processing.",
        )


@router.post(
    "/repositories/{repository_id}/onboarding/blueprint/refresh",
    response_model=RepositoryBlueprintResponse,
    status_code=status.HTTP_200_OK,
)
def refresh_repository_blueprint(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Force re-analysis of the repository blueprint.
    Requires REPOS_INDEX permission AND at least Team Lead role in the owning organization.
    """
    _get_repo_and_verify_access(
        db,
        current_user.id,
        repository_id,
        required_permission=Permission.REPOS_INDEX,
        min_role=RoleEnum.TEAM_LEAD,
    )

    service = OnboardingService(db)
    try:
        return service.get_or_generate_blueprint(repository_id=repository_id, force_refresh=True)
    except UnindexedRepositoryError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except GenerationInProgressError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )
    except (BlueprintGenerationError, GroundingValidationError, OnboardingServiceError) as exc:
        logger.error("Error refreshing blueprint for repo %d: %s", repository_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blueprint re-analysis failed. Prior valid blueprint has been preserved.",
        )
    except Exception as exc:
        logger.error("Unexpected error refreshing blueprint for repo %d: %s", repository_id, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during blueprint refresh.",
        )


# ---------------------------------------------------------------------------
# 2. Private Developer Onboarding Progress
# ---------------------------------------------------------------------------

@router.get(
    "/repositories/{repository_id}/onboarding/progress",
    response_model=UserProgressResponse,
    status_code=status.HTTP_200_OK,
)
def get_user_onboarding_progress(
    repository_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Retrieve private onboarding checklist progress for the authenticated user.
    Progress is strictly scoped to current_user.id. Client cannot specify a user ID.
    Requires REPOS_READ permission in the owning organization.
    """
    _get_repo_and_verify_access(db, current_user.id, repository_id, Permission.REPOS_READ)

    service = OnboardingService(db)
    return service.get_user_progress(user_id=current_user.id, repository_id=repository_id)


@router.put(
    "/repositories/{repository_id}/onboarding/progress",
    response_model=UserProgressResponse,
    status_code=status.HTTP_200_OK,
)
def update_user_onboarding_progress(
    repository_id: int,
    payload: UpdateProgressRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update private onboarding checklist progress and notes for the authenticated user.
    Validates track and milestone IDs against schema and active blueprint.
    Requires REPOS_READ permission in the owning organization.
    """
    _get_repo_and_verify_access(db, current_user.id, repository_id, Permission.REPOS_READ)

    # Validate completed milestone IDs formatting and membership
    if payload.completed_milestones is not None:
        for mid in payload.completed_milestones:
            if not isinstance(mid, str) or not MILESTONE_ID_PATTERN.match(mid) or len(mid) < 2 or len(mid) > 50:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Malformed milestone ID: '{mid}'. Must be alphanumeric with dashes/underscores.",
                )

        # If a blueprint exists, ensure milestone IDs belong to known blueprint tracks
        bp = db.query(RepositoryBlueprint).filter_by(repository_id=repository_id).first()
        if bp and bp.tracks and isinstance(bp.tracks, dict):
            known_ids: Set[str] = set()
            for track_data in bp.tracks.values():
                if isinstance(track_data, dict):
                    for m in track_data.get("milestones", []):
                        if isinstance(m, dict) and "id" in m:
                            known_ids.add(m["id"])
            if known_ids:
                invalid_ids = set(payload.completed_milestones) - known_ids
                if invalid_ids:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Invalid milestone ID(s) not found in blueprint: {list(invalid_ids)}",
                    )

    service = OnboardingService(db)
    return service.update_user_progress(
        user_id=current_user.id,
        repository_id=repository_id,
        req=payload,
    )

