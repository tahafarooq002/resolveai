from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.schemas.common import IDSchema, TimestampSchema


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, IDSchema, TimestampSchema):
    is_active: bool
    is_superuser: bool


class OrganizationMemberResponse(IDSchema, TimestampSchema):
    organization_id: UUID
    user_id: UUID
    role: str
    user: Optional[UserResponse] = None
