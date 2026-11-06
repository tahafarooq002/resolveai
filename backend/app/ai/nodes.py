import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.ai.llm import get_classification_model, get_response_model
from app.ai.prompts import (
    CLASSIFICATION_SYSTEM_PROMPT,
    RESPONSE_SYSTEM_PROMPT,
    CONFIDENCE_EVAL_PROMPT,
)
from app.ai.state import TicketState
from app.schemas.ai import ClassificationResult, QualityResult


def _json_content(content: Any) -> dict[str, Any]:
    if not isinstance(content, str):
        raise ValueError("LLM returned a non-text response")
    content = content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    value = json.loads(content.strip())
    if not isinstance(value, dict):
        raise ValueError("LLM response must be a JSON object")
    return value


def triage_agent(state: TicketState) -> dict[str, Any]:
    """Triage Agent: Classify ticket, detect intent, sentiment, priority."""
    model = get_classification_model()
    history = state.get("previous_tickets_summary") or "No previous tickets."

    messages = [
        SystemMessage(content=CLASSIFICATION_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Customer Message:
{state['customer_message']}

Subject: {state.get('subject') or 'N/A'}
Customer: {state.get('customer_name') or 'Unknown'} <{state.get('customer_email') or 'N/A'}>

Previous interaction summary:
{history}
"""
        ),
    ]

    try:
        response = model.invoke(messages)
        data = ClassificationResult.model_validate(_json_content(response.content))

        is_sensitive = data.is_sensitive or data.required_action in [
            "refund_request", "account_update", "escalate"
        ] or data.category in ["Refund", "Billing", "Account Issues"]

        return {
            "category": data.category,
            "priority": data.priority,
            "urgency": data.urgency,
            "sentiment": data.sentiment,
            "required_action": data.required_action,
            "customer_intent": data.customer_intent,
            "classification_confidence": data.confidence,
            "is_sensitive": is_sensitive or data.is_sensitive,
            "needs_human_review": data.confidence != "high" or is_sensitive or data.is_sensitive,
        }
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        return {
            "category": "General Inquiry",
            "priority": "medium",
            "urgency": "medium",
            "sentiment": "neutral",
            "required_action": "none",
            "classification_confidence": "low",
            "is_sensitive": True,
            "needs_human_review": True,
            "error": f"Triage failed: {str(e)}",
        }


def resolution_agent(state: TicketState) -> dict[str, Any]:
    """Resolution Agent: Generate grounded response using retrieved knowledge."""
    model = get_response_model()

    context_parts = []
    sources = []
    for i, chunk in enumerate(state.get("retrieved_chunks", [])):
        context_parts.append(f"[Source {i+1}]\n{chunk.get('content', '')}")
        sources.append({
            "index": i + 1,
            "document_id": chunk.get("document_id"),
            "content_preview": chunk.get("content", "")[:220],
            "score": chunk.get("score"),
        })

    context = "\n\n".join(context_parts) if context_parts else "No relevant knowledge found in the company knowledge base."
    tone = state.get("tone", "professional")

    messages = [
        SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
        HumanMessage(
            content=f"""Tone: {tone}

Customer Question:
{state['customer_message']}

Company Knowledge:
{context}

Write a helpful, accurate response based only on the knowledge above.
If knowledge is insufficient, clearly say so and offer to escalate to a human agent.
"""
        ),
    ]

    try:
        response = model.invoke(messages)
        return {
            "generated_response": response.content.strip(),
            "response_sources": sources,
            "citations": sources,
        }
    except Exception as e:
        return {
            "generated_response": None,
            "response_sources": [],
            "citations": [],
            "error": f"Resolution failed: {str(e)}",
            "needs_human_review": True,
        }


def quality_agent(state: TicketState) -> dict[str, Any]:
    """Quality Assurance Agent: Evaluate response quality and grounding."""
    if not state.get("generated_response"):
        return {
            "response_confidence": "low",
            "groundedness_score": "low",
            "needs_human_review": True,
            "qa_notes": "No response generated",
        }

    model = get_classification_model()

    messages = [
        SystemMessage(content=CONFIDENCE_EVAL_PROMPT),
        HumanMessage(
            content=f"""Customer Question:
{state['customer_message']}

Retrieved Knowledge:
{json.dumps([c.get('content', '')[:300] for c in state.get('retrieved_chunks', [])], indent=2)}

Generated Response:
{state['generated_response']}

Is Sensitive: {state.get('is_sensitive', False)}
Category: {state.get('category')}
"""
        ),
    ]

    try:
        response = model.invoke(messages)
        data = QualityResult.model_validate(_json_content(response.content))

        confidence = data.confidence
        needs_review = (
            confidence != "high"
            or data.unsupported_claims
            or state.get("is_sensitive", False)
            or len(state.get("retrieved_chunks", [])) == 0
            or data.needs_human_review
        )

        return {
            "response_confidence": confidence,
            "groundedness_score": data.groundedness,
            "needs_human_review": needs_review,
            "qa_notes": data.qa_notes,
        }
    except (ValueError, TypeError, json.JSONDecodeError):
        return {
            "response_confidence": "low",
            "groundedness_score": "low",
            "needs_human_review": True,
            "qa_notes": "QA evaluation failed",
        }
