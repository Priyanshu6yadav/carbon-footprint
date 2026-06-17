"""
CarbonTrack — AIRecommendation model.
Stores AI-generated recommendations for users based on their carbon logs.
"""
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class AIRecommendation(Base, TimestampMixin):
    __tablename__ = "ai_recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    carbon_log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("carbon_logs.id", ondelete="SET NULL"), nullable=True
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    estimated_co2_saving_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="ai_recommendations")  # type: ignore[name-defined] # noqa: F821

    __table_args__ = (
        Index("ix_ai_recommendations_user_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AIRecommendation user={self.user_id} category={self.category}>"
