"""
CarbonTrack — Auth router.
Endpoints: register, login, refresh, logout, me.
Rate-limited on login/register via SlowAPI + Redis.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services import auth_service

settings = get_settings()
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(tags=["auth"])

REFRESH_COOKIE_NAME = "refresh_token"


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.ENVIRONMENT != "development",
        samesite="strict",
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=REFRESH_COOKIE_NAME, path="/api/auth")


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def register(
    request: Request,
    response: Response,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user."""
    # Check for existing email
    if await auth_service.get_user_by_email(db, body.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Check for existing username
    if await auth_service.get_user_by_username(db, body.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    # Create user
    user = User(
        email=body.email.lower(),
        username=body.username.lower(),
        hashed_password=auth_service.hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    await db.flush()

    # Issue tokens
    access_token, expires_in = auth_service.create_access_token(user.id)
    raw_refresh = auth_service.create_refresh_token()
    await auth_service.store_refresh_token(
        db, user.id, raw_refresh,
        device_hint=request.headers.get("User-Agent", "")[:200],
    )

    # Audit log
    await auth_service.log_audit_event(
        db, "auth.register",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    _set_refresh_cookie(response, raw_refresh)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email + password."""
    user = await auth_service.get_user_by_email(db, body.email)

    # Use constant-time comparison to prevent timing attacks
    if not user or not auth_service.verify_password(body.password, user.hashed_password):
        await auth_service.log_audit_event(
            db, "auth.login.failed",
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("User-Agent"),
            details=f'{{"email_domain": "{body.email.split("@")[-1]}"}}',
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    access_token, expires_in = auth_service.create_access_token(user.id)
    raw_refresh = auth_service.create_refresh_token()
    await auth_service.store_refresh_token(
        db, user.id, raw_refresh,
        device_hint=request.headers.get("User-Agent", "")[:200],
    )

    await auth_service.log_audit_event(
        db, "auth.login.success",
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("User-Agent"),
    )

    _set_refresh_cookie(response, raw_refresh)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Rotate refresh token and issue new access token."""
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    result = await auth_service.validate_and_rotate_refresh_token(db, raw_refresh)
    if not result:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")

    user, new_raw_refresh = result
    access_token, expires_in = auth_service.create_access_token(user.id)

    _set_refresh_cookie(response, new_raw_refresh)

    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """Invalidate the refresh token and clear the cookie."""
    raw_refresh = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_refresh:
        await auth_service.revoke_refresh_token(db, raw_refresh)

    await auth_service.log_audit_event(
        db, "auth.logout",
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )

    _clear_refresh_cookie(response)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(auth_service.get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)
