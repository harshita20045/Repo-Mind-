"""
RBAC Permission System — RepoMind 2.0

Defines the Permission enum and the canonical role → permission mapping.
Authorization must ALWAYS happen server-side via this module.
Frontend button hiding is NOT authorization.

Architecture:
    Role → Permissions → Resource Scope → Authorization middleware → API

Usage:
    from backend.app.auth.permissions import Permission, role_has_permission, require_permission

    # In a route:
    @router.get("/organizations/{org_id}/analytics")
    def get_analytics(
        org_id: int,
        db = Depends(get_db),
        current_user = Depends(get_current_user),
        _auth = Depends(require_permission(Permission.ANALYTICS_READ)),
    ):
        ...
"""
import enum
from typing import FrozenSet, Dict
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.models import RoleEnum


# ---------------------------------------------------------------------------
# Permission enum
# ---------------------------------------------------------------------------

class Permission(str, enum.Enum):
    """
    Fine-grained permission atoms used for server-side authorization.
    Roles are mapped to sets of these permissions below.
    """
    # Organization
    ORG_READ = "organization.read"
    ORG_UPDATE = "organization.update"
    ORG_TRANSFER = "organization.transfer"  # org_owner only

    # Members
    MEMBERS_READ = "members.read"
    MEMBERS_INVITE = "members.invite"
    MEMBERS_UPDATE = "members.update"
    MEMBERS_REMOVE = "members.remove"

    # Projects
    PROJECTS_READ = "projects.read"
    PROJECTS_CREATE = "projects.create"
    PROJECTS_UPDATE = "projects.update"
    PROJECTS_DELETE = "projects.delete"

    # Repositories
    REPOS_READ = "repositories.read"
    REPOS_CONNECT = "repositories.connect"
    REPOS_UPDATE = "repositories.update"
    REPOS_DELETE = "repositories.delete"
    REPOS_INDEX = "repositories.index"

    # Pull Requests
    PRS_READ = "prs.read"
    PRS_REVIEW = "prs.review"
    PRS_APPROVE = "prs.approve"
    PRS_REQUEST_CHANGES = "prs.request_changes"

    # Findings
    FINDINGS_READ = "findings.read"
    FINDINGS_DISMISS = "findings.dismiss"
    FINDINGS_FEEDBACK = "findings.feedback"

    # Reviews
    REVIEWS_RUN = "reviews.run"
    REVIEWS_READ = "reviews.read"

    # Analytics
    ANALYTICS_READ = "analytics.read"

    # Policies
    POLICIES_READ = "policies.read"
    POLICIES_UPDATE = "policies.update"

    # Security
    SECURITY_READ = "security.read"
    SECURITY_REVIEW = "security.review"

    # Chat / AI Assistant
    CHAT_USE = "chat.use"

    # Audit
    AUDIT_READ = "audit.read"


# ---------------------------------------------------------------------------
# Role → permission sets
# ---------------------------------------------------------------------------
# Build these as frozensets so they are immutable and hashable.

_READ_ONLY_PERMISSIONS: FrozenSet[Permission] = frozenset([
    Permission.ORG_READ,
    Permission.MEMBERS_READ,
    Permission.PROJECTS_READ,
    Permission.REPOS_READ,
    Permission.PRS_READ,
    Permission.FINDINGS_READ,
    Permission.REVIEWS_READ,
    Permission.ANALYTICS_READ,
    Permission.POLICIES_READ,
    Permission.SECURITY_READ,
])

_DEVELOPER_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_READ_ONLY_PERMISSIONS,
    Permission.REVIEWS_RUN,
    Permission.FINDINGS_FEEDBACK,
    Permission.CHAT_USE,
])

_REVIEWER_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_DEVELOPER_PERMISSIONS,
    Permission.PRS_REVIEW,
    Permission.PRS_REQUEST_CHANGES,
    Permission.FINDINGS_DISMISS,
])

_SECURITY_REVIEWER_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_REVIEWER_PERMISSIONS,
    Permission.SECURITY_REVIEW,
    Permission.PRS_APPROVE,
])

_TECH_LEAD_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_REVIEWER_PERMISSIONS,
    Permission.PRS_APPROVE,
    Permission.REPOS_INDEX,
])

_ENG_MANAGER_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_TECH_LEAD_PERMISSIONS,
    Permission.PROJECTS_CREATE,
    Permission.PROJECTS_UPDATE,
    Permission.POLICIES_READ,
    Permission.AUDIT_READ,
])

_ORG_ADMIN_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_ENG_MANAGER_PERMISSIONS,
    Permission.ORG_UPDATE,
    Permission.MEMBERS_INVITE,
    Permission.MEMBERS_UPDATE,
    Permission.MEMBERS_REMOVE,
    Permission.PROJECTS_DELETE,
    Permission.REPOS_CONNECT,
    Permission.REPOS_UPDATE,
    Permission.REPOS_DELETE,
    Permission.POLICIES_UPDATE,
])

_ORG_OWNER_PERMISSIONS: FrozenSet[Permission] = frozenset([
    *_ORG_ADMIN_PERMISSIONS,
    Permission.ORG_TRANSFER,
])

# Canonical mapping from role → permission set
ROLE_PERMISSIONS: Dict[str, FrozenSet[Permission]] = {
    RoleEnum.READ_ONLY.value: _READ_ONLY_PERMISSIONS,
    RoleEnum.DEVELOPER.value: _DEVELOPER_PERMISSIONS,
    RoleEnum.REVIEWER.value: _REVIEWER_PERMISSIONS,
    RoleEnum.SECURITY_REVIEWER.value: _SECURITY_REVIEWER_PERMISSIONS,
    RoleEnum.TEAM_LEAD.value: _TECH_LEAD_PERMISSIONS,    # legacy alias
    RoleEnum.TECH_LEAD.value: _TECH_LEAD_PERMISSIONS,    # same value, kept for clarity
    RoleEnum.ENG_MANAGER.value: _ENG_MANAGER_PERMISSIONS,
    RoleEnum.ORG_ADMIN.value: _ORG_ADMIN_PERMISSIONS,
    RoleEnum.ORG_OWNER.value: _ORG_OWNER_PERMISSIONS,
}

# Numeric hierarchy for legacy role comparisons (kept for backward compatibility)
ROLE_HIERARCHY: Dict[str, int] = {
    RoleEnum.READ_ONLY.value: 0,
    RoleEnum.DEVELOPER.value: 1,
    RoleEnum.REVIEWER.value: 2,
    RoleEnum.SECURITY_REVIEWER.value: 3,
    RoleEnum.TEAM_LEAD.value: 3,
    RoleEnum.TECH_LEAD.value: 3,
    RoleEnum.ENG_MANAGER.value: 4,
    RoleEnum.ORG_ADMIN.value: 5,
    RoleEnum.ORG_OWNER.value: 6,
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def role_has_permission(role: str, permission: Permission) -> bool:
    """
    Return True if the given role includes the specified permission.
    Unknown roles are treated as having no permissions.
    """
    perms = ROLE_PERMISSIONS.get(role, frozenset())
    return permission in perms


def get_role_permissions(role: str) -> FrozenSet[Permission]:
    """Return the full permission set for a role."""
    return ROLE_PERMISSIONS.get(role, frozenset())


def role_level(role: str) -> int:
    """Return the numeric hierarchy level for a role (higher = more privilege)."""
    return ROLE_HIERARCHY.get(role, -1)


# ---------------------------------------------------------------------------
# FastAPI authorization dependencies
# ---------------------------------------------------------------------------

def require_permission(permission: Permission):
    """
    FastAPI dependency factory: verify the current user has `permission`
    in at least one organization membership.

    For resource-scoped authorization (specific org/repo), use
    require_org_permission() instead.

    This factory returns an async dependency function.
    """
    async def _check(
        current_user=Depends(_get_current_user_lazy()),
    ) -> None:
        memberships = getattr(current_user, "memberships", [])
        for m in memberships:
            role_value = m.role.value if hasattr(m.role, "value") else str(m.role)
            if role_has_permission(role_value, permission):
                return  # Has permission in at least one org
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )
    return _check


def require_org_permission(permission: Permission, org_id_param: str = "organization_id"):
    """
    FastAPI dependency factory: verify the current user has `permission`
    specifically within the organization identified by the path parameter
    named `org_id_param`.

    Usage:
        @router.get("/organizations/{organization_id}/analytics")
        def get_analytics(
            organization_id: int,
            db = Depends(get_db),
            current_user = Depends(get_current_user),
            _auth = Depends(require_org_permission(Permission.ANALYTICS_READ)),
        ):
    """
    from fastapi import Request

    async def _check(
        request: Request,
        current_user=Depends(_get_current_user_lazy()),
    ) -> None:
        try:
            org_id = int(request.path_params[org_id_param])
        except (KeyError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing or invalid path parameter: {org_id_param}",
            )

        memberships = getattr(current_user, "memberships", [])
        for m in memberships:
            if m.organization_id != org_id:
                continue
            role_value = m.role.value if hasattr(m.role, "value") else str(m.role)
            if role_has_permission(role_value, permission):
                return  # Authorized

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )
    return _check


def check_org_permission(
    db: Session,
    user_id: int,
    organization_id: int,
    permission: Permission,
) -> bool:
    """
    Programmatic permission check (for use inside service functions).
    Does NOT raise — returns True/False.
    """
    from backend.app.auth.models import OrganizationMembership
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
        .first()
    )
    if not membership:
        return False
    role_value = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    return role_has_permission(role_value, permission)


def assert_org_permission(
    db: Session,
    user_id: int,
    organization_id: int,
    permission: Permission,
) -> None:
    """
    Programmatic permission assertion (for use inside service functions).
    Raises HTTPException(403) if the user lacks the permission.
    Raises HTTPException(404) if the user is not a member (prevents org enumeration).
    """
    from backend.app.auth.models import OrganizationMembership
    membership = (
        db.query(OrganizationMembership)
        .filter(
            OrganizationMembership.user_id == user_id,
            OrganizationMembership.organization_id == organization_id,
        )
        .first()
    )
    if not membership:
        # Return 404 to prevent organization existence enumeration
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found or access denied",
        )
    role_value = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
    if not role_has_permission(role_value, permission):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Permission denied: {permission.value}",
        )


# ---------------------------------------------------------------------------
# Internal lazy import helper (breaks circular import between auth modules)
# ---------------------------------------------------------------------------

def _get_current_user_lazy():
    """Lazy import of get_current_user to avoid circular dependencies."""
    from backend.app.auth.dependencies import get_current_user
    return get_current_user
