import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, get_user_organization_id
from app.models.user import User
from app.models.ticket import SupportTicket
from app.ai.graph import support_graph
from app.services import ticket as ticket_service
from app.services.rag import hybrid_search

router = APIRouter()


def get_previous_tickets_summary(db: Session, organization_id: UUID, customer_email: str | None, current_ticket_id: UUID) -> str:
    if not customer_email:
        return "No previous tickets."
    prev = (
        db.query(SupportTicket)
        .filter(
            SupportTicket.organization_id == organization_id,
            SupportTicket.customer_email == customer_email,
            SupportTicket.id != current_ticket_id,
        )
        .order_by(SupportTicket.created_at.desc())
        .limit(5)
        .all()
    )
    if not prev:
        return "No previous tickets."
    lines = []
    for t in prev:
        lines.append(f"- [{t.status}] {t.subject or 'No subject'} (priority: {t.priority}, category: {t.category or 'n/a'})")
    return "Previous tickets:\n" + "\n".join(lines)


@router.post("/process-ticket/{ticket_id}", response_model=dict)
def process_ticket(
    ticket_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    organization_id: Annotated[UUID, Depends(get_user_organization_id)],
):
    """
    Full multi-agent AI pipeline:
    1. Triage Agent (classify + intent + sentiment)
    2. Knowledge Retrieval (hybrid RAG)
    3. Resolution Agent (grounded response)
    4. Quality Assurance Agent (confidence + grounding)
    5. Save everything → pending_approval
    """
    ticket = ticket_service.get_ticket(db, ticket_id, organization_id)

    customer_messages = [m for m in ticket.messages if m.role == "customer"]
    if not customer_messages:
        raise HTTPException(status_code=400, detail="Ticket has no customer messages")
    latest_message = customer_messages[-1].content

    # Previous tickets context
    prev_summary = get_previous_tickets_summary(
        db, organization_id, ticket.customer_email, ticket.id
    )

    # Retrieval
    retrieved = hybrid_search(
        db=db,
        organization_id=organization_id,
        query=latest_message,
        top_k=6,
    )

    initial_state = {
        "ticket_id": str(ticket.id),
        "organization_id": str(organization_id),
        "customer_message": latest_message,
        "customer_email": ticket.customer_email,
        "customer_name": ticket.customer_name,
        "subject": ticket.subject,
        "previous_tickets_summary": prev_summary,
        "retrieved_chunks": retrieved,
        "retrieval_scores": [r.get("score", 0) for r in retrieved],
        "citations": [],
        "tone": "professional",
        "needs_human_review": True,
        "is_sensitive": False,
        "error": None,
        "messages": [],
    }

    result = support_graph.invoke(initial_state)

    if result.get("category"):
        ticket_service.save_classification(
            db=db,
            ticket_id=ticket.id,
            category=result["category"],
            priority=result.get("priority", "medium"),
            urgency=result.get("urgency", "medium"),
            sentiment=result.get("sentiment", "neutral"),
            required_action=result.get("required_action"),
            confidence=result.get("classification_confidence", "medium"),
        )

    if result.get("generated_response"):
        sources_json = json.dumps(result.get("response_sources", []))
        ticket_service.save_generated_response(
            db=db,
            ticket_id=ticket.id,
            content=result["generated_response"],
            confidence=result.get("response_confidence", "medium"),
            sources=sources_json,
            tone=result.get("tone", "professional"),
        )

    return {
        "ticket_id": str(ticket.id),
        "category": result.get("category"),
        "priority": result.get("priority"),
        "sentiment": result.get("sentiment"),
        "customer_intent": result.get("customer_intent"),
        "classification_confidence": result.get("classification_confidence"),
        "retrieved_chunks_count": len(retrieved),
        "generated_response": result.get("generated_response"),
        "response_confidence": result.get("response_confidence"),
        "groundedness_score": result.get("groundedness_score"),
        "needs_human_review": result.get("needs_human_review", True),
        "is_sensitive": result.get("is_sensitive", False),
        "qa_notes": result.get("qa_notes"),
        "sources": result.get("response_sources", []),
        "error": result.get("error"),
    }
