"""
CarbonTrack — AuditLog model.
Records auth events and admin actions for security compliance.
Never logs passwords, tokens, or full request bodies.
"""
import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Event info
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # e.g. "auth.login.success", "auth.login.failed", "auth.register", "auth.logout"
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv4/IPv6
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON, no PII

    user: Mapped["User | None"] = relationship(back_populates="audit_logs")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_audit_logs_user_created", "user_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
    )
