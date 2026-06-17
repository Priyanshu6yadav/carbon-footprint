"""
CarbonTrack — Challenge and ChallengeCompletion models.
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Challenge(Base, TimestampMixin):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    challenge_type: Mapped[str] = mapped_column(String(50), nullable=False)  # daily, weekly
    template_slug: Mapped[str | None] = mapped_column(String(100), nullable=True)  # AI template used
    xp_reward: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    co2_saved_estimate_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )

    user: Mapped["User"] = relationship(back_populates="challenges")  # type: ignore[name-defined] # noqa: F821
    completions: Mapped[list["ChallengeCompletion"]] = relationship(back_populates="challenge")


class ChallengeCompletion(Base, TimestampMixin):
    __tablename__ = "challenge_completions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    completed_at: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship(back_populates="challenge_completions")  # type: ignore[name-defined] # noqa: F821
    challenge: Mapped["Challenge"] = relationship(back_populates="completions")

    __table_args__ = (
        Index("ix_challenge_completions_user", "user_id", "completed_at"),
    )
