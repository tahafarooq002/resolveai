from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.services.analytics import get_overview

router = APIRouter()


@router.get("/overview")
def analytics_overview(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """
    High-level analytics dashboard data:
    - Ticket counts
    - Category breakdown
    - AI approval rate
    - Low confidence rate
    """
    return get_overview(db, organization_id)
