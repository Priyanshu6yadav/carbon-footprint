from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field

class HabitResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    icon: str | None
    xp_reward: int
    co2_saved_kg_per_log: float
    is_active: bool

    model_config = {"from_attributes": True}

class HabitLogCreate(BaseModel):
    habit_id: UUID
    notes: str | None = Field(None, max_length=500)

class HabitLogResponse(BaseModel):
    id: UUID
    habit_id: UUID
    log_date: date
    notes: str | None
    current_streak: int
    created_at: datetime

    model_config = {"from_attributes": True}
