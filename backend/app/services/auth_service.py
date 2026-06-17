"""
CarbonTrack — Auth service.
Handles JWT creation/validation, bcrypt hashing, and refresh token management.
"""
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.audit_log import AuditLog
from app.models.refresh_token import RefreshToken
from app.models.user import User

settings = get_settings()


# ─── Password ─────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    """Hash a password using native bcrypt."""
    password_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against a native bcrypt hash."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ─── JWT ──────────────────────────────────────────────────────────

def create_access_token(user_id: uuid.UUID) -> tuple[str, int]:
    """Returns (token, expires_in_seconds)."""
    expire_minutes = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expire_minutes * 60


def create_refresh_token() -> str:
    """Returns a cryptographically secure random refresh token."""
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    """Hash a token for storage — never store raw tokens."""
    return hashlib.sha256(token.encode()).hexdigest()


def decode_access_token(token: str) -> Optional[str]:
    """Decode and validate access token. Returns user_id str or None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ─── User Queries ─────────────────────────────────────────────────

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username.lower()))
    return result.scalar_one_or_none()


# ─── Refresh Token Management ──────────────────────────────────────

async def store_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    raw_token: str,
    device_hint: Optional[str] = None,
) -> RefreshToken:
    """Store a hashed refresh token in DB."""
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_hint=device_hint,
    )
    db.add(refresh_token)
    await db.flush()
    return refresh_token


async def validate_and_rotate_refresh_token(
    db: AsyncSession, raw_token: str
) -> Optional[tuple[User, str]]:
    """
    Validate a refresh token. If valid:
    - Revoke the old one
    - Issue a new one
    Returns (user, new_raw_token) or None if invalid.
    """
    token_hash = hash_token(raw_token)
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
            RefreshToken.expires_at > now,
        )
    )
    stored = result.scalar_one_or_none()
    if not stored:
        return None

    # Revoke old token
    stored.is_revoked = True

    # Get user
    user = await get_user_by_id(db, stored.user_id)
    if not user or not user.is_active:
        return None

    # Issue new token
    new_raw = create_refresh_token()
    await store_refresh_token(db, user.id, new_raw, stored.device_hint)

    return user, new_raw


async def revoke_refresh_token(db: AsyncSession, raw_token: str) -> bool:
    """Revoke a specific refresh token on logout."""
    token_hash = hash_token(raw_token)
    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.is_revoked == False,  # noqa: E712
        )
    )
    stored = result.scalar_one_or_none()
    if stored:
        stored.is_revoked = True
        return True
    return False


# ─── Audit Logging ────────────────────────────────────────────────

async def log_audit_event(
    db: AsyncSession,
    action: str,
    user_id: Optional[uuid.UUID] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    details: Optional[str] = None,
) -> None:
    """Log auth/security events to audit_logs — no PII in details."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip_address,
        user_agent=user_agent[:500] if user_agent else None,
        details=details,
    )
    db.add(entry)
    await db.flush()


# ─── Current User Dependency ──────────────────────────────────────

from fastapi import Depends, HTTPException, status  # noqa: E402
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer  # noqa: E402

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(__import__("app.database", fromlist=["get_db"]).get_db),
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise unauthorized
    user_id_str = decode_access_token(credentials.credentials)
    if not user_id_str:
        raise unauthorized
    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise unauthorized
    user = await get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise unauthorized
    return user
