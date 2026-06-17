"""
CarbonTrack — RefreshToken model.
Stores issued refresh tokens for rotation and denylist enforcement.
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class RefreshToken(Base, TimestampMixin):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)
    # We store a hash of the token, never the raw token
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    device_hint: Mapped[str | None] = mapped_column(String(200), nullable=True)  # browser/device info

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_refresh_tokens_user_revoked", "user_id", "is_revoked"),
    )
