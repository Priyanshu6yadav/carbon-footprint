"""
CarbonTrack — FastAPI application factory.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.config import get_settings
from app.middleware.security import SecurityHeadersMiddleware
from app.redis_client import close_redis, get_redis_client
from app.routers import auth, calculator, health, eco_score, habits, challenges, analytics, chat

settings = get_settings()

limiter = Limiter(
    key_func=get_remote_address,
    enabled=settings.ENVIRONMENT != "testing",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: verify connectivity. Shutdown: close connections."""
    # Verify Redis on startup
    redis = await get_redis_client()
    await redis.ping()

    yield

    # Cleanup
    await close_redis()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="CarbonTrack — Carbon Footprint Awareness Platform API",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# ─── Rate limiter state ───────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware (order matters — outermost first) ─────────────────
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

# ─── Routers ──────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(calculator.router, prefix="/api/calculator")
app.include_router(eco_score.router, prefix="/api/eco-score")
app.include_router(habits.router, prefix="/api/habits")
app.include_router(challenges.router, prefix="/api/challenges")
app.include_router(analytics.router, prefix="/api/analytics")
app.include_router(chat.router, prefix="/api/chat")


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": "/health",
    }
