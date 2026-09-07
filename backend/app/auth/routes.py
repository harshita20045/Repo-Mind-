from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.auth.models import User
from backend.app.auth.schemas import (
    UserLogin,
    UserRegister,
    AuthResponse,
    UserResponse,
    MembershipResponse,
    OrganizationResponse,
)
from backend.app.auth.service import (
    authenticate_user,
    register_user,
    create_access_token,
    get_user_by_email,
    JWT_EXPIRATION_HOURS,
)
from backend.app.auth.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


def format_auth_response(user: User, message: str = "Success") -> AuthResponse:
    memberships = [
        MembershipResponse(
            id=m.id,
            organization_id=m.organization_id,
            role=m.role.value if hasattr(m.role, "value") else str(m.role),
            organization=OrganizationResponse(
                id=m.organization.id,
                name=m.organization.name,
                created_at=m.organization.created_at,
            ),
        )
        for m in user.memberships
    ]
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            created_at=user.created_at,
        ),
        memberships=memberships,
        message=message,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    credentials: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user_id=user.id, email=user.email)

    # Set JWT in HttpOnly cookie per blueprint architecture decisions
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        samesite="lax",
        secure=False,
    )

    return format_auth_response(user, message="Login successful")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    data: UserRegister,
    response: Response,
    db: Session = Depends(get_db),
):
    existing = get_user_by_email(db, data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )

    user = register_user(
        db,
        email=data.email,
        password=data.password,
        org_name=data.organization_name or "Default Org",
    )

    token = create_access_token(user_id=user.id, email=user.email)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=JWT_EXPIRATION_HOURS * 3600,
        samesite="lax",
        secure=False,
    )

    return format_auth_response(user, message="Registration successful")


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
    )
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=AuthResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return format_auth_response(current_user, message="Current session valid")
