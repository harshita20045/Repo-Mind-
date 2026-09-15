import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.app.db import get_db
from backend.app.auth.dependencies import get_current_user
from backend.app.auth.models import User
from backend.app.auth.permissions import require_org_permission, Permission
from backend.app.analytics import service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/organization/{org_id}")
def get_org_analytics(
    org_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    user: User = Depends(require_org_permission(Permission.ANALYTICS_READ))
):
    """
    Get engineering intelligence analytics for an organization.
    Requires ANALYTICS_READ permission.
    """
    try:
        data = service.get_organization_analytics(db, org_id, days)
        return data
    except Exception as e:
        logger.error(f"Error fetching analytics for org {org_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error fetching analytics")
