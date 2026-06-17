from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field

class ChallengeResponse(BaseModel):
    id: UUID
    title: str
    description: str
    challenge_type: str
    template_slug: str | None
    xp_reward: int
    co2_saved_estimate_kg: float
    difficulty: str
    is_active: bool
    valid_from: date | None
    valid_until: date | None

    model_config = {"from_attributes": True}

class ChallengeCompletionCreate(BaseModel):
    challenge_id: UUID
    notes: str | None = Field(None, max_length=500)

class ChallengeCompletionResponse(BaseModel):
    id: UUID
    challenge_id: UUID
    completed_at: date
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
