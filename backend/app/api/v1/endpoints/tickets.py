from typing import Annotated, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.schemas.ticket import (
    TicketCreate,
    TicketResponse,
    TicketListItem,
    TicketMessageCreate,
    TicketMessageResponse,
    TicketBulkUpdate,
    TicketUpdate,
)
from app.services import ticket as ticket_service

router = APIRouter()


@router.post("", response_model=TicketResponse)
def create_ticket(
    data: TicketCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """Create a new support ticket."""
    ticket = ticket_service.create_ticket(db, organization_id, data)
    return ticket_service.get_ticket(db, ticket.id, organization_id)


@router.get("", response_model=List[TicketListItem])
def list_tickets(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None, min_length=2),
    category: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    assigned_to_id: Optional[UUID] = Query(None),
    sort_by: str = Query("created_at", pattern="^(created_at|updated_at|priority|status)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """List tickets for the current organization."""
    return ticket_service.list_tickets(
        db, organization_id, status, skip, limit, search, category,
        priority, assigned_to_id, sort_by, sort_order,
    )


@router.patch("/{ticket_id}", response_model=TicketResponse)
def update_ticket(
    ticket_id: UUID,
    data: TicketUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    return ticket_service.update_ticket(db, ticket_id, organization_id, data)


@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=201)
def add_ticket_message(
    ticket_id: UUID,
    data: TicketMessageCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    return ticket_service.add_message(db, ticket_id, organization_id, data)


@router.post("/bulk", response_model=dict)
def bulk_update_tickets(
    data: TicketBulkUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    update = TicketUpdate(
        status=data.status,
        priority=data.priority,
        assigned_to_id=data.assigned_to_id,
    )
    updated = ticket_service.bulk_update(db, organization_id, data.ticket_ids, update)
    return {"updated_count": updated}


@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """Get full ticket details including messages, classification and AI responses."""
    return ticket_service.get_ticket(db, ticket_id, organization_id)
