"""
CarbonTrack — User model.
"""
import uuid

from sqlalchemy import Boolean, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Google OAuth (optional)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    # Gamification
    xp_total: Mapped[int] = mapped_column(default=0, nullable=False)
    level: Mapped[int] = mapped_column(default=1, nullable=False)

    # Relationships
    carbon_logs: Mapped[list["CarbonLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    eco_scores: Mapped[list["EcoScore"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    habit_logs: Mapped[list["HabitLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    challenge_completions: Mapped[list["ChallengeCompletion"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    challenges: Mapped[list["Challenge"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    user_achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    ai_recommendations: Mapped[list["AIRecommendation"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_users_email_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.email})>"
