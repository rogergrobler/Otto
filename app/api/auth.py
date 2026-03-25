from fastapi import APIRouter, Depends, HTTPException, status
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
    decode_token,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


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
