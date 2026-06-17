"""
CarbonTrack — Habit and HabitLog models.
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class Habit(Base, TimestampMixin):
    """Defines the available habits (seeded at startup)."""
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)  # emoji or icon name
    xp_reward: Mapped[int] = mapped_column(Integer, default=10, nullable=False)  # fixed, deterministic
    co2_saved_kg_per_log: Mapped[float] = mapped_column(default=0.0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    logs: Mapped[list["HabitLog"]] = relationship(back_populates="habit")


class HabitLog(Base, TimestampMixin):
    """Records each time a user logs a habit."""
    __tablename__ = "habit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    habit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("habits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Streak snapshot at log time
    current_streak: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    user: Mapped["User"] = relationship(back_populates="habit_logs")  # type: ignore[name-defined] # noqa: F821
    habit: Mapped["Habit"] = relationship(back_populates="logs")

    __table_args__ = (
        Index("ix_habit_logs_user_date", "user_id", "log_date"),
        Index("ix_habit_logs_user_habit", "user_id", "habit_id"),
    )
