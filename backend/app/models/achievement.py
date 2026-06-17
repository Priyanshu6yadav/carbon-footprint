"""
CarbonTrack — Achievement and UserAchievement models.
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Achievement(Base, TimestampMixin):
    """Defines all available achievements/badges (seeded at startup)."""
    __tablename__ = "achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    xp_reward: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    trigger_rule: Mapped[str] = mapped_column(Text, nullable=False)  # JSON rule definition
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    user_achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="achievement")


class UserAchievement(Base, TimestampMixin):
    """Records when a user unlocked a specific achievement."""
    __tablename__ = "user_achievements"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    achievement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False
    )
    notified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship(back_populates="user_achievements")  # type: ignore[name-defined] # noqa: F821
    achievement: Mapped["Achievement"] = relationship(back_populates="user_achievements")

    __table_args__ = (
        Index("ix_user_achievements_user", "user_id", "created_at"),
    )
