from typing import Literal, Optional

from pydantic import BaseModel, Field


class ClassificationResult(BaseModel):
    category: Literal[
        "Billing", "Refund", "Technical Support", "Order Status",
        "Product Information", "Account Issues", "Subscription",
        "Delivery", "Cancellation", "General Inquiry",
    ]
    priority: Literal["critical", "high", "medium", "low"]
    urgency: Literal["critical", "high", "medium", "low"]
    sentiment: Literal["positive", "neutral", "negative", "frustrated", "angry"]
    required_action: Literal[
        "none", "refund_request", "account_update", "order_lookup",
        "escalate", "provide_info",
    ]
    customer_intent: Optional[str] = None
    confidence: Literal["high", "medium", "low"]
    is_sensitive: bool = False


class QualityResult(BaseModel):
    confidence: Literal["high", "medium", "low"]
    groundedness: Literal["high", "medium", "low"]
    unsupported_claims: bool = False
    policy_compliant: bool = True
    needs_human_review: bool = True
    qa_notes: str = Field(default="")
