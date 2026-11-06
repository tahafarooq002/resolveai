from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status

from app.models.ticket import (
    SupportTicket,
    TicketMessage,
    AIClassification,
    GeneratedResponse,
)
from app.models.user import OrganizationMember
from app.schemas.ticket import TicketCreate, TicketMessageCreate, TicketUpdate


def create_ticket(
    db: Session,
    organization_id: UUID,
    data: TicketCreate,
) -> SupportTicket:
    ticket = SupportTicket(
        organization_id=organization_id,
        customer_email=data.customer_email,
        customer_name=data.customer_name,
        subject=data.subject,
        status="open",
        priority="medium",
    )
    db.add(ticket)
    db.flush()

    # First message from customer
    message = TicketMessage(
        ticket_id=ticket.id,
        role="customer",
        content=data.message,
        is_internal=False,
    )
    db.add(message)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_ticket(
    db: Session,
    ticket_id: UUID,
    organization_id: UUID,
) -> SupportTicket:
    ticket = (
        db.query(SupportTicket)
        .options(
            joinedload(SupportTicket.messages),
            joinedload(SupportTicket.classifications),
            joinedload(SupportTicket.generated_responses),
        )
        .filter(
            SupportTicket.id == ticket_id,
            SupportTicket.organization_id == organization_id,
        )
        .first()
    )
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


def update_ticket(
    db: Session,
    ticket_id: UUID,
    organization_id: UUID,
    data: TicketUpdate,
) -> SupportTicket:
    ticket = get_ticket(db, ticket_id, organization_id)
    values = data.model_dump(exclude_unset=True)
    if values.get("assigned_to_id") is not None:
        member_exists = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == values["assigned_to_id"],
            )
            .first()
        )
        if not member_exists:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assigned user is not a member of this organization",
            )
    for field, value in values.items():
        setattr(ticket, field, value)
    db.commit()
    return get_ticket(db, ticket_id, organization_id)


def add_message(
    db: Session,
    ticket_id: UUID,
    organization_id: UUID,
    data: TicketMessageCreate,
) -> TicketMessage:
    ticket = get_ticket(db, ticket_id, organization_id)
    message = TicketMessage(
        ticket_id=ticket.id,
        role="agent" if data.is_internal else "customer",
        content=data.content,
        is_internal=data.is_internal,
    )
    db.add(message)
    if not data.is_internal and ticket.status in {"resolved", "closed"}:
        ticket.status = "open"
    db.commit()
    db.refresh(message)
    return message


def list_tickets(
    db: Session,
    organization_id: UUID,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    search: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_id: Optional[UUID] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> List[SupportTicket]:
    query = db.query(SupportTicket).filter(
        SupportTicket.organization_id == organization_id
    )
    if status:
        query = query.filter(SupportTicket.status == status)
    if category:
        query = query.filter(SupportTicket.category == category)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if assigned_to_id:
        query = query.filter(SupportTicket.assigned_to_id == assigned_to_id)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            SupportTicket.subject.ilike(term)
            | SupportTicket.customer_name.ilike(term)
            | SupportTicket.customer_email.ilike(term)
        )

    sort_column = {
        "created_at": SupportTicket.created_at,
        "updated_at": SupportTicket.updated_at,
        "priority": SupportTicket.priority,
        "status": SupportTicket.status,
    }.get(sort_by, SupportTicket.created_at)
    ordering = sort_column.asc() if sort_order == "asc" else sort_column.desc()

    return (
        query.order_by(ordering)
        .offset(skip)
        .limit(limit)
        .all()
    )


def bulk_update(
    db: Session,
    organization_id: UUID,
    ticket_ids: List[UUID],
    data: TicketUpdate,
) -> int:
    updated = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.id.in_(ticket_ids),
        )
        .all()
    )
    values = data.model_dump(exclude_unset=True)
    if values.get("assigned_to_id") is not None:
        member_exists = (
            db.query(OrganizationMember)
            .filter(
                OrganizationMember.organization_id == organization_id,
                OrganizationMember.user_id == values["assigned_to_id"],
            )
            .first()
        )
        if not member_exists:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Assigned user is not a member of this organization",
            )
    for ticket in updated:
        for field, value in values.items():
            setattr(ticket, field, value)
    db.commit()
    return len(updated)


def save_classification(
    db: Session,
    ticket_id: UUID,
    category: str,
    priority: str,
    urgency: str,
    sentiment: str,
    required_action: Optional[str],
    confidence: str,
    raw_response: Optional[str] = None,
) -> AIClassification:
    classification = AIClassification(
        ticket_id=ticket_id,
        category=category,
        priority=priority,
        urgency=urgency,
        sentiment=sentiment,
        required_action=required_action,
        confidence=confidence,
        raw_response=raw_response,
    )
    db.add(classification)

    # Also update ticket fields
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket:
        ticket.category = category
        ticket.priority = priority
        ticket.sentiment = sentiment

    db.commit()
    db.refresh(classification)
    return classification


def save_generated_response(
    db: Session,
    ticket_id: UUID,
    content: str,
    confidence: str,
    sources: Optional[str],
    tone: str = "professional",
) -> GeneratedResponse:
    response = GeneratedResponse(
        ticket_id=ticket_id,
        content=content,
        confidence=confidence,
        sources=sources,
        tone=tone,
        status="pending",
    )
    db.add(response)

    # Move ticket to pending_approval
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if ticket:
        ticket.status = "pending_approval"

    db.commit()
    db.refresh(response)
    return response
