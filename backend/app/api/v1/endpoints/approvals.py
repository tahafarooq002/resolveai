from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.models.ticket import GeneratedResponse, SupportTicket

router = APIRouter()


class ApprovalAction(BaseModel):
    action: str = Field(..., pattern="^(approve|reject|edit)$")
    edited_content: Optional[str] = None

    @field_validator("edited_content")
    @classmethod
    def validate_edited_content(cls, value: Optional[str], info):
        if info.data.get("action") == "edit" and not value:
            raise ValueError("edited_content is required when action=edit")
        return value


@router.post("/{ticket_id}/response/{response_id}", response_model=dict)
def handle_approval(
    ticket_id: UUID,
    response_id: UUID,
    data: ApprovalAction,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """
    Human-in-the-loop approval actions:
    - approve
    - reject
    - edit (requires edited_content)
    """
    # Verify ticket belongs to organization
    ticket = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.organization_id == organization_id,
        )
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    response = (
        db.query(GeneratedResponse)
        .filter(
            GeneratedResponse.id == response_id,
            GeneratedResponse.ticket_id == ticket_id,
        )
        .first()
    )
    if not response:
        raise HTTPException(status_code=404, detail="Generated response not found")

    if data.action == "approve":
        response.status = "approved"
        response.approved_by_id = current_user.id
        ticket.status = "resolved"

    elif data.action == "reject":
        response.status = "rejected"
        ticket.status = "open"  # back to open for rework

    elif data.action == "edit":
        if not data.edited_content:
            raise HTTPException(
                status_code=400,
                detail="edited_content is required when action=edit",
            )
        response.edited_content = data.edited_content
        response.status = "edited"
        response.approved_by_id = current_user.id
        ticket.status = "resolved"

    db.commit()

    return {
        "ticket_id": str(ticket.id),
        "response_id": str(response.id),
        "status": response.status,
        "ticket_status": ticket.status,
    }
