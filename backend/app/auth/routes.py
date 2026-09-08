from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from backend.app.db import get_db
from backend.app.auth.models import User
from backend.app.auth.schemas import (
    UserLogin,
    BootstrapRequest,
    OnboardRequest,
    PasswordChangeRequest,
    AuthResponse,
    UserResponse,
    MembershipResponse,
    OrganizationResponse,
)
from backend.app.auth.service import (
    authenticate_user,
    bootstrap_system,
    onboard_user,
    change_password,
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


@router.post("/bootstrap", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def bootstrap(
    data: BootstrapRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = bootstrap_system(
        db,
        email=data.email,
        password=data.password,
        org_name=data.organization_name,
        bootstrap_token=data.bootstrap_token,
    )
    token = create_access_token(user_id=user.id, email=user.email)
    response.set_cookie(
        key="access_token", value=token, httponly=True, max_age=JWT_EXPIRATION_HOURS * 3600, samesite="lax", secure=False
    )
    return format_auth_response(user, message="Bootstrap successful")


@router.post("/onboard", response_model=AuthResponse)
def onboard(
    data: OnboardRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = onboard_user(
        db,
        invitation_token=data.invitation_token,
        new_password=data.new_password,
    )
    token = create_access_token(user_id=user.id, email=user.email)
    response.set_cookie(
        key="access_token", value=token, httponly=True, max_age=JWT_EXPIRATION_HOURS * 3600, samesite="lax", secure=False
    )
    return format_auth_response(user, message="Onboarding successful")


@router.post("/change-password")
def change_password_route(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    change_password(
        db,
        user=current_user,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return {"message": "Password changed successfully"}


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
