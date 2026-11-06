from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import LoginRequest, RegisterRequest, Token
from app.schemas.user import UserResponse
from app.services.auth import (
    authenticate_user,
    create_token_for_user,
    create_user_with_organization,
)

router = APIRouter()


@router.post("/register", response_model=dict)
def register(
    data: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register a new user + create their organization."""
    user = create_user_with_organization(db, data)
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
        "access_token": create_token_for_user(user),
        "token_type": "bearer",
    }


@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
):
    """OAuth2 compatible token login. Use email as username."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token_for_user(user)
    return Token(access_token=access_token)


@router.post("/login/json", response_model=Token)
def login_json(
    data: LoginRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """JSON body login (convenient for frontend)."""
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_token_for_user(user)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Get current logged-in user."""
    return current_user


@router.get("/organization")
def get_my_organization(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """Return current organization info including public support link slug."""
    org = db.query(Organization).filter(Organization.id == organization_id).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {
        "id": str(org.id),
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
        "support_url": f"/submit/{org.slug}",
    }
