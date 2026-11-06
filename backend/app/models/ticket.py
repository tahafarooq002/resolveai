import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.organization import Organization
    from app.models.user import User


class SupportTicket(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "support_tickets"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    customer_email: Mapped[Optional[str]] = mapped_column(String(320), nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default="open", nullable=False, index=True
    )  # open | pending_approval | resolved | closed
    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False
    )  # low | medium | high | urgent
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    assigned_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    organization: Mapped["Organization"] = relationship("Organization", back_populates="tickets")
    assigned_to: Mapped[Optional["User"]] = relationship("User")
    messages: Mapped[List["TicketMessage"]] = relationship(
        "TicketMessage", back_populates="ticket", cascade="all, delete-orphan"
    )
    classifications: Mapped[List["AIClassification"]] = relationship(
        "AIClassification", back_populates="ticket", cascade="all, delete-orphan"
    )
    generated_responses: Mapped[List["GeneratedResponse"]] = relationship(
        "GeneratedResponse", back_populates="ticket", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<SupportTicket {self.id} status={self.status}>"


class TicketMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ticket_messages"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)  # customer | agent | system
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_internal: Mapped[bool] = mapped_column(default=False, nullable=False)

    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="messages")


class AIClassification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ai_classifications"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    priority: Mapped[str] = mapped_column(String(20), nullable=False)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False)
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False)
    required_action: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)  # high | medium | low
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="classifications")


class GeneratedResponse(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "generated_responses"

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)  # high | medium | low
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON list of sources
    tone: Mapped[str] = mapped_column(String(50), default="professional", nullable=False)
    status: Mapped[str] = mapped_column(
        String(50), default="pending", nullable=False
    )  # pending | approved | rejected | edited
    approved_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    edited_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    ticket: Mapped["SupportTicket"] = relationship("SupportTicket", back_populates="generated_responses")
