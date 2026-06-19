"""
CarbonTrack — Challenges router.
Endpoints: list active challenges, complete challenge, generate personalized challenges.
"""
from datetime import date, timedelta
import logging
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as aioredis
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis
from app.models.challenge import Challenge, ChallengeCompletion
from app.models.carbon_log import CarbonLog
from app.models.habit import Habit, HabitLog
from app.models.user import User
from app.schemas.challenges import ChallengeResponse, ChallengeCompletionCreate, ChallengeCompletionResponse
from app.services.auth_service import get_current_user
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["challenges"])
ai_service = AIService()


@router.get("/", response_model=List[ChallengeResponse])
async def list_challenges(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List active global challenges and user-specific generated challenges."""
    stmt = select(Challenge).where(
        Challenge.is_active == True,  # noqa: E712
        or_(
            Challenge.user_id == None,  # noqa: E711
            Challenge.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/generate", response_model=List[ChallengeResponse], status_code=status.HTTP_201_CREATED)
async def generate_personalized_challenges(
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    Generate 1-3 daily challenges tailored to the user's carbon footprint and habit gaps.
    Enforces a strict limit of one generation request per user per day using Redis.
    """
    today = date.today()
    limit_key = f"challenges:generate_limit:{current_user.id}:{today.isoformat()}"
    
    # Check rate limit in Redis
    try:
        already_generated = await redis.get(limit_key)
        if already_generated:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="You have already generated challenges for today. Try again tomorrow."
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning("Error reading Redis limit: %s", e)

    # Gather user context: Carbon log totals in last 30 days
    thirty_days_ago = today - timedelta(days=30)
    
    carbon_stmt = select(
        func.sum(CarbonLog.transport_total).label("transport"),
        func.sum(CarbonLog.energy_total).label("energy"),
        func.sum(CarbonLog.food_total).label("food"),
        func.sum(CarbonLog.shopping_total).label("shopping"),
    ).where(
        CarbonLog.user_id == current_user.id,
        CarbonLog.created_at >= thirty_days_ago
    )
    carbon_res = await db.execute(carbon_stmt)
    carbon_row = carbon_res.first()
    
    recent_footprint = {
        "transport": float((carbon_row.transport if carbon_row else 0.0) or 0.0),
        "energy": float((carbon_row.energy if carbon_row else 0.0) or 0.0),
        "food": float((carbon_row.food if carbon_row else 0.0) or 0.0),
        "shopping": float((carbon_row.shopping if carbon_row else 0.0) or 0.0),
    }

    # Gather user context: Habit completions in last 30 days
    habit_stmt = select(
        Habit.slug,
        func.count(HabitLog.id).label("logged_days")
    ).select_from(Habit).outerjoin(
        HabitLog,
        (HabitLog.habit_id == Habit.id)
        & (HabitLog.user_id == current_user.id)
        & (HabitLog.log_date >= thirty_days_ago)
    ).where(Habit.is_active == True).group_by(Habit.slug)  # noqa: E712
    
    habit_res = await db.execute(habit_stmt)
    habit_rows = habit_res.all()
    habit_completions = [{"slug": r.slug, "logged_days": r.logged_days} for r in habit_rows]

    # Generate custom challenges from AIService
    challenge_payloads = await ai_service.generate_challenges(
        str(current_user.id),
        recent_footprint,
        habit_completions
    )

    created_challenges = []
    for payload in challenge_payloads:
        challenge = Challenge(
            title=payload["title"],
            description=payload["description"],
            challenge_type=payload["challenge_type"],
            template_slug=payload["template_slug"],
            difficulty=payload["difficulty"],
            co2_saved_estimate_kg=payload["co2_saved_estimate_kg"],
            xp_reward=payload["xp_reward"],
            user_id=current_user.id,
            is_active=True,
        )
        db.add(challenge)
        created_challenges.append(challenge)

    await db.flush()

    # Set rate limit in Redis (expires in 24 hours to cover same-day blocks)
    try:
        await redis.set(limit_key, "1", ex=86400)
    except Exception as e:
        logger.warning("Error writing Redis limit: %s", e)

    return created_challenges


@router.post("/{challenge_id}/complete", response_model=ChallengeCompletionResponse, status_code=status.HTTP_201_CREATED)
async def complete_challenge(
    challenge_id: UUID,
    body: ChallengeCompletionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a challenge as completed by the current user and award deterministic XP rewards."""
    # 1. Verify challenge exists and is active for this user (or global)
    stmt = select(Challenge).where(
        Challenge.id == challenge_id,
        Challenge.is_active == True,  # noqa: E712
        or_(
            Challenge.user_id == None,  # noqa: E711
            Challenge.user_id == current_user.id
        )
    )
    result = await db.execute(stmt)
    challenge = result.scalar_one_or_none()
    if not challenge:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found or inactive.")

    today = date.today()

    # 2. Check if already completed
    check_result = await db.execute(
        select(ChallengeCompletion).where(
            ChallengeCompletion.user_id == current_user.id,
            ChallengeCompletion.challenge_id == challenge.id,
        )
    )
    existing_completion = check_result.scalar_one_or_none()
    if existing_completion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Challenge already completed.",
        )

    # 3. Create completion
    completion = ChallengeCompletion(
        user_id=current_user.id,
        challenge_id=challenge.id,
        completed_at=today,
        notes=body.notes,
    )
    db.add(completion)

    # 4. Award gamification rewards deterministically based on challenge definition
    # XP is additive; level = floor(xp / 100) + 1 (level 1 starts at 0 XP, level 2 at 100, etc.)
    current_user.xp_total += challenge.xp_reward
    current_user.level = (current_user.xp_total // 100) + 1

    await db.flush()
    return completion
