"""
CarbonTrack — Calculator router.
Endpoints: calculate (unauthenticated preview), save, history.
"""
import json
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis_client import get_redis
from app.models.carbon_log import CarbonLog
from app.models.eco_score import EcoScore
from app.models.user import User
from app.schemas.calculator import CalculationResult, CalculatorInput, SavedLogResponse
from app.services import calculator_service
from app.services.auth_service import get_current_user

router = APIRouter(tags=["calculator"])


@router.post("/calculate", response_model=CalculationResult)
async def calculate_footprint(body: CalculatorInput):
    """
    Calculate carbon footprint without saving.
    Available without authentication (preview mode).
    """
    return calculator_service.compute_carbon(body)


@router.post("/save", response_model=SavedLogResponse, status_code=status.HTTP_201_CREATED)
async def save_footprint(
    body: CalculatorInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    redis: aioredis.Redis = Depends(get_redis),
):
    """Calculate and persist a carbon log for the authenticated user."""
    result = calculator_service.compute_carbon(body)
    bd = result.breakdown

    log = CarbonLog(
        user_id=current_user.id,
        # Transportation
        transport_car=bd.transport_detail.get("car_kg", 0.0),
        transport_public=bd.transport_detail.get("bus_kg", 0.0) + bd.transport_detail.get("rail_kg", 0.0),
        transport_flights=bd.transport_detail.get("flights_kg", 0.0),
        transport_motorcycle=bd.transport_detail.get("motorcycle_kg", 0.0),
        transport_total=bd.transportation_kg,
        # Energy
        energy_electricity=bd.energy_detail.get("electricity_kg", 0.0),
        energy_natural_gas=bd.energy_detail.get("natural_gas_kg", 0.0),
        energy_lpg=bd.energy_detail.get("lpg_kg", 0.0),
        energy_total=bd.home_energy_kg,
        # Food
        food_diet_type=body.food.diet_type,
        food_total=bd.food_kg,
        # Shopping
        shopping_clothing=body.shopping.clothing_usd_per_month * 0.0119,
        shopping_electronics=body.shopping.electronics_usd_per_month * 0.0089,
        shopping_general=body.shopping.general_goods_usd_per_month * 0.0071,
        shopping_total=bd.shopping_kg,
        # Totals
        total_monthly_kg=bd.total_monthly_kg,
        total_annual_kg=bd.total_annual_kg,
        raw_input=json.dumps(body.model_dump()),
        emission_factors_version=result.emission_factors_version,
    )
    db.add(log)
    await db.flush()

    # Calculate Eco Score
    base_score = 100
    penalty = int(bd.total_monthly_kg / 10)
    score_val = max(10, min(100, base_score - penalty))

    tier = "Footprint Saver"
    if score_val >= 85:
        tier = "Climate Champion"
    elif score_val >= 70:
        tier = "Eco Conscious"

    eco_score = EcoScore(
        user_id=current_user.id,
        score=score_val,
        tier=tier,
        carbon_log_id=log.id,
        transport_score=max(10.0, 100.0 - (bd.transportation_kg / 5.0)),
        energy_score=max(10.0, 100.0 - (bd.home_energy_kg / 5.0)),
        food_score=max(10.0, 100.0 - (bd.food_kg / 3.0)),
        shopping_score=max(10.0, 100.0 - (bd.shopping_kg / 2.0)),
    )
    db.add(eco_score)
    await db.flush()

    # Clear analytics cache for this user so the dashboard updates immediately
    try:
        keys = await redis.keys(f"analytics:{current_user.id}:*")
        if keys:
            await redis.delete(*keys)
    except Exception as e:
        # Don't fail the request if redis clear fails
        pass

    return SavedLogResponse.model_validate(log)


@router.get("/history", response_model=List[SavedLogResponse])
async def get_history(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Paginated list of the user's saved carbon logs, newest first."""
    if limit > 100:
        limit = 100
    result = await db.execute(
        select(CarbonLog)
        .where(CarbonLog.user_id == current_user.id)
        .order_by(CarbonLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    logs = result.scalars().all()
    return [SavedLogResponse.model_validate(log) for log in logs]


@router.get("/history/{log_id}", response_model=SavedLogResponse)
async def get_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific saved carbon log by ID."""
    result = await db.execute(
        select(CarbonLog).where(
            CarbonLog.id == log_id,
            CarbonLog.user_id == current_user.id,
        )
    )
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return SavedLogResponse.model_validate(log)
