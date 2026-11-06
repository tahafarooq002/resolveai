from typing import Any, Dict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.ticket import SupportTicket, GeneratedResponse, AIClassification


def get_overview(db: Session, organization_id: UUID) -> Dict[str, Any]:
    """Return high-level analytics for the organization."""

    total_tickets = (
        db.query(func.count(SupportTicket.id))
        .filter(SupportTicket.organization_id == organization_id)
        .scalar()
        or 0
    )

    resolved = (
        db.query(func.count(SupportTicket.id))
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.status == "resolved",
        )
        .scalar()
        or 0
    )

    pending = (
        db.query(func.count(SupportTicket.id))
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.status == "pending_approval",
        )
        .scalar()
        or 0
    )

    high_priority = (
        db.query(func.count(SupportTicket.id))
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.priority.in_(["high", "urgent"]),
        )
        .scalar()
        or 0
    )

    # Category breakdown
    categories = (
        db.query(SupportTicket.category, func.count(SupportTicket.id))
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.category.isnot(None),
        )
        .group_by(SupportTicket.category)
        .all()
    )
    category_counts = {cat or "Unknown": count for cat, count in categories}

    # Approval stats
    total_responses = (
        db.query(func.count(GeneratedResponse.id))
        .join(SupportTicket)
        .filter(SupportTicket.organization_id == organization_id)
        .scalar()
        or 0
    )

    approved = (
        db.query(func.count(GeneratedResponse.id))
        .join(SupportTicket)
        .filter(
            SupportTicket.organization_id == organization_id,
            GeneratedResponse.status.in_(["approved", "edited"]),
        )
        .scalar()
        or 0
    )

    low_confidence = (
        db.query(func.count(GeneratedResponse.id))
        .join(SupportTicket)
        .filter(
            SupportTicket.organization_id == organization_id,
            GeneratedResponse.confidence == "low",
        )
        .scalar()
        or 0
    )

    approval_rate = round((approved / total_responses) * 100, 1) if total_responses > 0 else 0.0

    return {
        "total_tickets": total_tickets,
        "resolved_tickets": resolved,
        "pending_approval": pending,
        "high_priority_tickets": high_priority,
        "category_breakdown": category_counts,
        "total_ai_responses": total_responses,
        "approved_responses": approved,
        "approval_rate_percent": approval_rate,
        "low_confidence_responses": low_confidence,
    }
