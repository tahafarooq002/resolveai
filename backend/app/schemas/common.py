from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str


class ORMBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TimestampSchema(ORMBase):
    created_at: datetime
    updated_at: datetime


class IDSchema(ORMBase):
    id: UUID
