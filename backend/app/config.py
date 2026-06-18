"""
CarbonTrack — Settings
Pydantic BaseSettings reads from environment variables (and .env file).
Fails loudly at startup if required secrets are missing.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ─── Required ───────────────────────────────────────────────────
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str

    # ─── Optional — features degrade gracefully ──────────────────────
    GROQ_API_KEY: str = ""
    OAUTH_GOOGLE_CLIENT_ID: str = ""
    OAUTH_GOOGLE_CLIENT_SECRET: str = ""

    # ─── CORS ────────────────────────────────────────────────────────
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # ─── JWT Config ──────────────────────────────────────────────────
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    GROQ_REQUEST_TIMEOUT_SECONDS: int = 15
    GROQ_MAX_RETRIES: int = 2

    # ─── App Config ──────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    APP_NAME: str = "CarbonTrack API"
    APP_VERSION: str = "1.0.0"

    # ─── Security ────────────────────────────────────────────────────
    BCRYPT_ROUNDS: int = 12
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_AI: str = "10/minute"

    @field_validator("DATABASE_URL", "REDIS_URL", "JWT_SECRET", "JWT_REFRESH_SECRET")
    @classmethod
    def must_not_be_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(
                f"Required environment variable '{info.field_name}' is missing or empty. "
                "Check your .env file against .env.example."
            )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton — fails fast at startup if config is invalid."""
    return Settings()  # type: ignore[call-arg]
