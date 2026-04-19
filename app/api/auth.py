from datetime import timedelta

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.client import Client
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse
from app.schemas.health import RegisterRequest
from app.services.auth_service import (
    authenticate_admin,
    authenticate_client,
    create_access_token,
    create_refresh_token,
    create_token,
    decode_token,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# Secret for the admin-only direct reset endpoint.
# TODO: move to settings / env var before production.
_ADMIN_RESET_SECRET = "OTTO_ADMIN_2026"


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Try admin login first, then client
    user = await authenticate_admin(db, request.email, request.password)
    if user:
        return TokenResponse(
            access_token=create_access_token(str(user.id), user.role.value),
            refresh_token=create_refresh_token(str(user.id), user.role.value),
        )

    client = await authenticate_client(db, request.email, request.password)
    if client:
        return TokenResponse(
            access_token=create_access_token(str(client.id), "client"),
            refresh_token=create_refresh_token(str(client.id), "client"),
        )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Self-registration for new Otto users."""
    existing = await db.execute(select(Client).where(Client.email == request.email))
    if existing.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered.")

    client = Client(
        full_name=request.full_name,
        email=request.email,
        hashed_password=hash_password(request.password),
        date_of_birth=request.date_of_birth,
        sex=request.sex,
        height_cm=request.height_cm,
        weight_kg=request.weight_kg,
    )

    # Auto-set protein target from weight if provided
    if request.weight_kg:
        client.daily_protein_target_g = int(request.weight_kg * 1.8)
        client.daily_fibre_target_g = 30
        client.daily_calories_target = int(request.weight_kg * 30)  # rough TDEE

    db.add(client)
    await db.commit()
    await db.refresh(client)

    return TokenResponse(
        access_token=create_access_token(str(client.id), "client"),
        refresh_token=create_refresh_token(str(client.id), "client"),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    payload = decode_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    return TokenResponse(
        access_token=create_access_token(payload["sub"], payload["role"]),
        refresh_token=create_refresh_token(payload["sub"], payload["role"]),
    )


# ── Password reset ────────────────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    reset_token: str  # returned directly — swap for email delivery in production


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class AdminResetRequest(BaseModel):
    email: str
    new_password: str
    admin_secret: str


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a 1-hour password-reset token for the given email.
    Currently returns the token directly (no email service wired up yet).
    TODO: replace with SendGrid/Resend delivery before production.
    """
    result = await db.execute(select(Client).where(Client.email == request.email))
    client = result.scalars().first()
    # Always return 200 to avoid email enumeration — token is empty if not found
    if not client:
        return ForgotPasswordResponse(reset_token="")

    token = create_token(
        {"sub": str(client.id), "type": "reset"},
        expires_delta=timedelta(hours=1),
    )
    return ForgotPasswordResponse(reset_token=token)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate a reset token and set a new password."""
    if len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters.")

    payload = decode_token(request.token)
    if not payload or payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token.")

    result = await db.execute(select(Client).where(Client.id == payload["sub"]))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Account not found.")

    client.hashed_password = hash_password(request.new_password)
    await db.commit()


@router.post("/admin-reset", status_code=status.HTTP_204_NO_CONTENT)
async def admin_reset_password(
    request: AdminResetRequest,
    db: AsyncSession = Depends(get_db),
):
    """Direct password reset for admins. Protected by admin_secret."""
    if request.admin_secret != _ADMIN_RESET_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden.")

    result = await db.execute(select(Client).where(Client.email == request.email))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="No account found for that email.")

    client.hashed_password = hash_password(request.new_password)
    await db.commit()
