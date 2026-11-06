from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User, OrganizationMember
from app.models.organization import Organization
from app.schemas.auth import RegisterRequest


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_user_with_organization(db: Session, data: RegisterRequest) -> User:
    # Check if email already exists
    if get_user_by_email(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create organization
    slug = data.organization_name.lower().replace(" ", "-")[:80]
    # Make slug unique
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        slug = f"{slug}-{str(UUID(int=0))[:8]}"  # simple uniqueness

    org = Organization(
        name=data.organization_name,
        slug=slug,
        description=f"Organization for {data.organization_name}",
    )
    db.add(org)
    db.flush()

    # Create user
    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        is_active=True,
        is_superuser=False,
    )
    db.add(user)
    db.flush()

    # Create membership as owner
    membership = OrganizationMember(
        organization_id=org.id,
        user_id=user.id,
        role="owner",
    )
    db.add(membership)
    db.commit()
    db.refresh(user)
    return user


def create_token_for_user(user: User) -> str:
    return create_access_token(subject=str(user.id))
