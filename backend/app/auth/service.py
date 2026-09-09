import bcrypt
import jwt
import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.core.config import settings
from backend.app.auth.models import User, Organization, OrganizationMembership, RoleEnum


JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 12


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(hours=JWT_EXPIRATION_HOURS)

    payload: Dict[str, Any] = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not user.password_hash:
        # Pending account, cannot login
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def bootstrap_system(
    db: Session, email: str, password: str, org_name: str, bootstrap_token: str
) -> User:
    expected_token = settings.BOOTSTRAP_TOKEN
    print(expected_token, bootstrap_token)
    if not expected_token or bootstrap_token != expected_token:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid bootstrap token")

    if db.query(User).count() > 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="System already bootstrapped")

    user = User(
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()

    org = Organization(name=org_name)
    db.add(org)
    db.flush()

    membership = OrganizationMembership(
        user_id=user.id,
        organization_id=org.id,
        role=RoleEnum.ORG_ADMIN,
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


def onboard_user(db: Session, invitation_token: str, new_password: str) -> User:
    token_hash = hash_invitation_token(invitation_token)
    user = db.query(User).filter(User.invitation_token_hash == token_hash).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation token")

    if not user.invitation_expires_at or user.invitation_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitation token expired")

    user.password_hash = hash_password(new_password)
    user.invitation_token_hash = None
    user.invitation_expires_at = None
    db.commit()
    db.refresh(user)
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    
    user.password_hash = hash_password(new_password)
    db.commit()
