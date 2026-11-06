from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.common import IDSchema, TimestampSchema


class OrganizationBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None


class OrganizationResponse(OrganizationBase, IDSchema, TimestampSchema):
    slug: str
