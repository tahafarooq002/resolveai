from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

TICKET_STATUSES = {
    "new",
    "processing",
    "pending_approval",
    "in_progress",
    "waiting_for_customer",
    "escalated",
    "resolved",
    "closed",
    "open",  # backwards-compatible alias for existing clients
}
TICKET_PRIORITIES = {"critical", "high", "medium", "low", "urgent"}

from app.schemas.common import IDSchema, TimestampSchema


class TicketCreate(BaseModel):
    customer_email: Optional[EmailStr] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = Field(None, min_length=5)
    messages: Optional[List[dict]] = None

    @model_validator(mode="after")
    def require_message(self) -> "TicketCreate":
        if not self.message and not self.messages:
            raise ValueError("message is required")
        if not self.message and self.messages:
            first = self.messages[0]
            self.message = str(first.get("content", "")).strip()
        if not self.message or len(self.message) < 5:
            raise ValueError("message must contain at least 5 characters")
        return self

    @field_validator("subject")
    @classmethod
    def normalize_subject(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value else value


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    category: Optional[str] = None
    assigned_to_id: Optional[UUID] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in TICKET_STATUSES:
            raise ValueError(f"Unsupported ticket status: {value}")
        return value

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and value not in TICKET_PRIORITIES:
            raise ValueError(f"Unsupported ticket priority: {value}")
        return value


class TicketMessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class TicketBulkUpdate(BaseModel):
    ticket_ids: List[UUID] = Field(..., min_length=1)
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to_id: Optional[UUID] = None


class TicketMessageResponse(IDSchema, TimestampSchema):
    ticket_id: UUID
    role: str
    content: str
    is_internal: bool


class AIClassificationResponse(IDSchema, TimestampSchema):
    ticket_id: UUID
    category: str
    priority: str
    urgency: str
    sentiment: str
    required_action: Optional[str] = None
    confidence: str


class GeneratedResponseSchema(IDSchema, TimestampSchema):
    ticket_id: UUID
    content: str
    confidence: str
    sources: Optional[str] = None
    tone: str
    status: str
    edited_content: Optional[str] = None


class TicketResponse(IDSchema, TimestampSchema):
    organization_id: UUID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    status: str
    priority: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
    assigned_to_id: Optional[UUID] = None
    messages: List[TicketMessageResponse] = Field(default_factory=list)
    classifications: List[AIClassificationResponse] = Field(default_factory=list)
    generated_responses: List[GeneratedResponseSchema] = Field(default_factory=list)


class TicketListItem(IDSchema, TimestampSchema):
    organization_id: UUID
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    subject: Optional[str] = None
    status: str
    priority: str
    category: Optional[str] = None
    sentiment: Optional[str] = None
