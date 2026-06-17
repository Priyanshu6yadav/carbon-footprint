"""
CarbonTrack — Async Redis client.
"""
from collections.abc import AsyncGenerator
from typing import Optional

import redis.asyncio as aioredis

from app.config import get_settings

settings = get_settings()

_redis_pool: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Return the shared Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def close_redis():
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """FastAPI dependency — yields the Redis client."""
    client = await get_redis_client()
    yield client
