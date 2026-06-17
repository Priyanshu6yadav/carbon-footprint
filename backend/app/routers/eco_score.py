"""
CarbonTrack — EcoScore router.
Endpoints: latest, history.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.eco_score import EcoScore
from app.models.user import User
from app.schemas.eco_score import EcoScoreResponse
from app.services.auth_service import get_current_user

router = APIRouter(tags=["eco-score"])


@router.get("/latest", response_model=EcoScoreResponse)
async def get_latest_score(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the user's latest computed eco-score entry."""
    result = await db.execute(
        select(EcoScore)
        .where(EcoScore.user_id == current_user.id)
        .order_by(EcoScore.created_at.desc())
        .limit(1)
    )
    score = result.scalar_one_or_none()
    if not score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No eco-score data available yet. Please complete a carbon calculation.",
        )
    return score


@router.get("/history", response_model=List[EcoScoreResponse])
async def get_score_history(
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve historical eco-score snapshots, newest first."""
    if limit > 100:
        limit = 100
    result = await db.execute(
        select(EcoScore)
        .where(EcoScore.user_id == current_user.id)
        .order_by(EcoScore.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    scores = result.scalars().all()
    return scores
