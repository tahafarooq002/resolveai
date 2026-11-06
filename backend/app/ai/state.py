from typing import Any, Dict, List, Optional, TypedDict
from typing_extensions import Annotated
import operator


class TicketState(TypedDict):
    ticket_id: str
    organization_id: str
    customer_message: str
    customer_email: Optional[str]
    customer_name: Optional[str]
    subject: Optional[str]
    previous_tickets_summary: Optional[str]

    category: Optional[str]
    priority: Optional[str]
    urgency: Optional[str]
    sentiment: Optional[str]
    required_action: Optional[str]
    classification_confidence: Optional[str]
    is_sensitive: bool
    customer_intent: Optional[str]

    retrieved_chunks: List[Dict[str, Any]]
    retrieval_scores: List[float]
    citations: List[Dict[str, Any]]

    generated_response: Optional[str]
    response_sources: List[Dict[str, Any]]
    tone: str

    response_confidence: Optional[str]
    groundedness_score: Optional[str]
    needs_human_review: bool
    qa_notes: Optional[str]

    error: Optional[str]
    messages: Annotated[List[Any], operator.add]
