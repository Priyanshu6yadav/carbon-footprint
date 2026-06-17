"""
CarbonTrack — EcoScore model.
Stores computed eco-score snapshots over time.
"""
import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class EcoScore(Base, TimestampMixin):
    __tablename__ = "eco_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0–100
    tier: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "Eco Conscious"
    carbon_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carbon_logs.id", ondelete="SET NULL"), nullable=True
    )
    # Snapshot details
    transport_score: Mapped[float] = mapped_column(Float, default=0.0)
    energy_score: Mapped[float] = mapped_column(Float, default=0.0)
    food_score: Mapped[float] = mapped_column(Float, default=0.0)
    shopping_score: Mapped[float] = mapped_column(Float, default=0.0)

    user: Mapped["User"] = relationship(back_populates="eco_scores")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_eco_scores_user_created", "user_id", "created_at"),
    )
