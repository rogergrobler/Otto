"""
WHOOP OAuth integration routes.

GET  /integrations/whoop/connect      → redirect to WHOOP auth (requires auth)
GET  /integrations/whoop/callback     → OAuth callback (public, state carries JWT)
POST /integrations/whoop/sync         → pull latest data into wearable_data (requires auth)
GET  /integrations/whoop/status       → check if connected (requires auth)
"""
import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.wearable_integration import IntegrationProvider, WearableIntegration
from app.services.auth_service import decode_token
from app.services.whoop_service import (
    build_auth_url,
    exchange_code_for_tokens,
    save_integration,
    sync_whoop_data,
)

router = APIRouter(prefix="/integrations/whoop", tags=["integrations"])

# In-memory state store (state token → client_id). Fine for single-instance.
# For multi-instance deploy, use Redis or DB.
_pending_states: dict[str, str] = {}


@router.get("/connect-url")
async def connect_whoop_url(
    client: Client = Depends(get_current_client),
):
    """Return the WHOOP OAuth URL as JSON (for frontend use)."""
    state = secrets.token_urlsafe(32)
    _pending_states[state] = str(client.id)
    return {"url": build_auth_url(state)}


@router.get("/connect")
async def connect_whoop(
    client: Client = Depends(get_current_client),
):
    """Generate WHOOP OAuth URL and redirect the client."""
    state = secrets.token_urlsafe(32)
    _pending_states[state] = str(client.id)
    auth_url = build_auth_url(state)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def whoop_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """
    WHOOP redirects here after the user authorises.
    State token maps back to the client_id.
    """
    client_id = _pending_states.pop(state, None)
    if not client_id:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state.")

    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")

    token_data = await exchange_code_for_tokens(code)
    await save_integration(db, client, token_data)
    await db.commit()

    return {"status": "connected", "message": "WHOOP connected successfully."}


@router.post("/sync")
async def sync_whoop(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Fetch latest WHOOP data and upsert into wearable_data."""
    try:
        summary = await sync_whoop_data(db, client)
        await db.commit()
        return {
            "status": "ok",
            "synced": summary,
            "message": f"Synced {sum(summary.values())} WHOOP records.",
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status")
async def whoop_status(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Check whether WHOOP is connected for this client."""
    result = await db.execute(
        select(WearableIntegration).where(
            WearableIntegration.client_id == client.id,
            WearableIntegration.provider == IntegrationProvider.WHOOP,
        )
    )
    integration = result.scalars().first()
    if not integration:
        return {"connected": False}
    return {
        "connected": True,
        "provider_user_id": integration.provider_user_id,
        "token_expiry": integration.token_expiry.isoformat() if integration.token_expiry else None,
    }
