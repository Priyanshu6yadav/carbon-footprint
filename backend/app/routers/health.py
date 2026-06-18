"""
CarbonTrack — Health check router.
Verifies DB and Redis connectivity.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import redis.asyncio as aioredis

from app.database import get_db
from app.redis_client import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    """
    Health check endpoint.
    Returns 200 if DB and Redis are both reachable, 503 otherwise.
    """
    db_status = "ok"
    redis_status = "ok"
    errors = []

    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = "error"
        errors.append(f"DB: {str(e)}")

    try:
        await redis.ping()
    except Exception as e:
        redis_status = "error"
        errors.append(f"Redis: {str(e)}")

    response.status_code = 200 if not errors else 503
    return {
        "status": "ok" if not errors else "degraded",
        "db": db_status,
        "redis": redis_status,
        "errors": errors,
    }
