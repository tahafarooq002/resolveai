"""
Public (customer-facing) endpoints.
No authentication required.
Customers submit tickets using the organization slug.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.models.organization import Organization
from app.schemas.ticket import TicketCreate
from app.services import ticket as ticket_service

router = APIRouter()


class PublicTicketCreate(BaseModel):
    customer_email: EmailStr
    customer_name: str = Field(..., min_length=1, max_length=150)
    subject: str = Field(..., min_length=3, max_length=255)
    message: str = Field(..., min_length=10)


class PublicTicketResponse(BaseModel):
    ticket_id: UUID
    message: str
    status: str


@router.post(
    "/{org_slug}/tickets",
    response_model=PublicTicketResponse,
    status_code=201,
    summary="Customer submits a support ticket",
)
def public_create_ticket(
    org_slug: str,
    data: PublicTicketCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Public endpoint for customers.
    Anyone can submit a ticket to an organization using its public slug.
    No login required.
    """
    # Find organization by slug
    org = db.query(Organization).filter(Organization.slug == org_slug).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found. Please check the support link.",
        )

    # Create ticket using existing service
    ticket_data = TicketCreate(
        customer_email=data.customer_email,
        customer_name=data.customer_name,
        subject=data.subject,
        message=data.message,
    )
    ticket = ticket_service.create_ticket(db, org.id, ticket_data)

    return PublicTicketResponse(
        ticket_id=ticket.id,
        message="Your support request has been submitted successfully. Our team will get back to you soon.",
        status=ticket.status,
    )


@router.get("/{org_slug}/info")
def public_org_info(
    org_slug: str,
    db: Annotated[Session, Depends(get_db)],
):
    """Return basic public info about the organization (for the customer form header)."""
    org = db.query(Organization).filter(Organization.slug == org_slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {
        "name": org.name,
        "slug": org.slug,
        "description": org.description,
    }
