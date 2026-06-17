"""
CarbonTrack — CarbonLog model.
Stores each user's carbon footprint calculation.
"""
import uuid

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class CarbonLog(Base, TimestampMixin):
    __tablename__ = "carbon_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # ─── Transportation (kg CO₂e / month) ─────────────────────────
    transport_car: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transport_public: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transport_flights: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transport_motorcycle: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    transport_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Home Energy (kg CO₂e / month) ────────────────────────────
    energy_electricity: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    energy_natural_gas: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    energy_lpg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    energy_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Food (kg CO₂e / month) ───────────────────────────────────
    food_diet_type: Mapped[str] = mapped_column(String(50), default="average", nullable=False)
    food_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Shopping / Lifestyle (kg CO₂e / month) ───────────────────
    shopping_clothing: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shopping_electronics: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shopping_general: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    shopping_total: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # ─── Totals ────────────────────────────────────────────────────
    total_monthly_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_annual_kg: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Raw input snapshot for auditability
    raw_input: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON string
    emission_factors_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)

    # Relationship
    user: Mapped["User"] = relationship(back_populates="carbon_logs")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_carbon_logs_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<CarbonLog user={self.user_id} monthly={self.total_monthly_kg:.1f}kg>"
