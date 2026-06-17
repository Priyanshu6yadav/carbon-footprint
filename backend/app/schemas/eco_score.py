from datetime import datetime
from uuid import UUID
from pydantic import BaseModel

class EcoScoreResponse(BaseModel):
    id: UUID
    score: int
    tier: str
    carbon_log_id: UUID | None
    transport_score: float
    energy_score: float
    food_score: float
    shopping_score: float
    created_at: datetime

    model_config = {"from_attributes": True}
