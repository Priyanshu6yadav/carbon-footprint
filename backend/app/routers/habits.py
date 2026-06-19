"""
CarbonTrack — Habits router.
Endpoints: list habits, log habit.
"""
from datetime import date, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.habit import Habit, HabitLog
from app.models.user import User
from app.schemas.habits import HabitResponse, HabitLogCreate, HabitLogResponse
from app.services.auth_service import get_current_user

router = APIRouter(tags=["habits"])


@router.get("/", response_model=List[HabitResponse])
async def list_habits(db: AsyncSession = Depends(get_db)):
    """List all active habits in the catalog."""
    result = await db.execute(select(Habit).where(Habit.is_active == True))  # noqa: E712
    return result.scalars().all()


@router.post("/log", response_model=HabitLogResponse, status_code=status.HTTP_201_CREATED)
async def log_habit_completion(
    body: HabitLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Log a habit completion for today, update user XP/Level, and award rewards."""
    # 1. Verify habit exists
    result = await db.execute(select(Habit).where(Habit.id == body.habit_id, Habit.is_active == True))  # noqa: E712
    habit = result.scalar_one_or_none()
    if not habit:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")

    today = date.today()

    # 2. Check if habit was already logged today
    check_result = await db.execute(
        select(HabitLog).where(
            HabitLog.user_id == current_user.id,
            HabitLog.habit_id == habit.id,
            HabitLog.log_date == today,
        )
    )
    existing_log = check_result.scalar_one_or_none()
    if existing_log:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Habit already logged for today.",
        )

    # 3. Calculate streak
    yesterday = today - timedelta(days=1)
    streak_result = await db.execute(
        select(HabitLog).where(
            HabitLog.user_id == current_user.id,
            HabitLog.habit_id == habit.id,
            HabitLog.log_date == yesterday,
        )
    )
    yesterday_log = streak_result.scalar_one_or_none()
    new_streak = (yesterday_log.current_streak + 1) if yesterday_log else 1

    # 4. Save log
    log = HabitLog(
        user_id=current_user.id,
        habit_id=habit.id,
        log_date=today,
        notes=body.notes,
        current_streak=new_streak,
    )
    db.add(log)

    # 5. Award gamification rewards
    # XP is additive; level = floor(xp / 100) + 1 (level 1 starts at 0 XP, level 2 at 100, etc.)
    current_user.xp_total += habit.xp_reward
    current_user.level = (current_user.xp_total // 100) + 1

    await db.flush()
    return log
