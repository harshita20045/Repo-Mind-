from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.auth.models import User, RoleEnum
from backend.app.auth.service import decode_access_token, get_user_by_id


def extract_token_from_request(request: Request) -> Optional[str]:
    # 1. Check HttpOnly cookie
    token = request.cookies.get("access_token")
    if token:
        return token

    # 2. Check Authorization header: Bearer <token>
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None


async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    token = extract_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token",
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


def require_role(min_role: RoleEnum):
    role_hierarchy = {
        RoleEnum.DEVELOPER: 1,
        RoleEnum.REVIEWER: 2,
        RoleEnum.TEAM_LEAD: 3,
        RoleEnum.ORG_ADMIN: 4,
    }

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        user_roles = [m.role for m in current_user.memberships]
        max_user_level = max([role_hierarchy.get(r, 0) for r in user_roles], default=0)
        required_level = role_hierarchy.get(min_role, 1)

        if max_user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires '{min_role.value}' role or higher",
            )
        return current_user

    return role_checker
