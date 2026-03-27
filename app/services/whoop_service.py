"""
WHOOP OAuth 2.0 integration service.

OAuth flow:
  1. GET /integrations/whoop/connect  → redirect to WHOOP auth URL
  2. WHOOP redirects to /integrations/whoop/callback?code=...&state=...
  3. Exchange code for tokens → store in wearable_integrations
  4. POST /integrations/whoop/sync → fetch latest data and upsert into wearable_data
"""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.wearable_data import WearableData, WearableSource
from app.models.wearable_integration import IntegrationProvider, WearableIntegration

logger = logging.getLogger(__name__)

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v1"
WHOOP_SCOPES = "offline read:recovery read:sleep read:workout read:profile read:body_measurement"


def get_redirect_uri() -> str:
    base = settings.TELEGRAM_WEBHOOK_URL  # reuse the base URL setting
    # Extract just the origin
    if base:
        parts = base.split("/")
        origin = "/".join(parts[:3])  # https://otto-production-xxxx.up.railway.app
    else:
        origin = "https://otto-production-924c.up.railway.app"
    return f"{origin}/api/integrations/whoop/callback"


def build_auth_url(state: str) -> str:
    params = {
        "client_id": settings.WHOOP_CLIENT_ID,
        "redirect_uri": get_redirect_uri(),
        "response_type": "code",
        "scope": WHOOP_SCOPES,
        "state": state,
    }
    return f"{WHOOP_AUTH_URL}?{urlencode(params)}"


async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange OAuth authorization code for access + refresh tokens."""
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": get_redirect_uri(),
                "client_id": settings.WHOOP_CLIENT_ID,
                "client_secret": settings.WHOOP_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Refresh an expired WHOOP access token."""
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            WHOOP_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.WHOOP_CLIENT_ID,
                "client_secret": settings.WHOOP_CLIENT_SECRET,
            },
        )
        resp.raise_for_status()
        return resp.json()


async def _get_valid_token(db: AsyncSession, integration: WearableIntegration) -> str:
    """Return a valid access token, refreshing if needed."""
    if integration.token_expiry and integration.token_expiry <= datetime.now(timezone.utc) + timedelta(minutes=5):
        token_data = await refresh_access_token(integration.refresh_token)
        integration.access_token = token_data["access_token"]
        integration.refresh_token = token_data.get("refresh_token", integration.refresh_token)
        integration.token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=token_data.get("expires_in", 3600)
        )
        await db.flush()
    return integration.access_token


async def save_integration(
    db: AsyncSession, client: Client, token_data: dict
) -> WearableIntegration:
    """Upsert WHOOP integration record after OAuth callback."""
    result = await db.execute(
        select(WearableIntegration).where(
            WearableIntegration.client_id == client.id,
            WearableIntegration.provider == IntegrationProvider.WHOOP,
        )
    )
    integration = result.scalars().first()

    expiry = datetime.now(timezone.utc) + timedelta(seconds=token_data.get("expires_in", 3600))

    if integration:
        integration.access_token = token_data["access_token"]
        integration.refresh_token = token_data.get("refresh_token", integration.refresh_token)
        integration.token_expiry = expiry
    else:
        integration = WearableIntegration(
            client_id=client.id,
            provider=IntegrationProvider.WHOOP,
            access_token=token_data["access_token"],
            refresh_token=token_data.get("refresh_token"),
            token_expiry=expiry,
        )
        db.add(integration)

    # Fetch WHOOP user ID and store it
    try:
        async with httpx.AsyncClient() as http:
            profile_resp = await http.get(
                f"{WHOOP_API_BASE}/user/profile/basic",
                headers={"Authorization": f"Bearer {token_data['access_token']}"},
            )
            if profile_resp.status_code == 200:
                integration.provider_user_id = str(profile_resp.json().get("user_id", ""))
    except Exception:
        pass

    await db.flush()
    return integration


async def sync_whoop_data(db: AsyncSession, client: Client) -> dict:
    """
    Fetch the last 30 days of WHOOP data and upsert into wearable_data.
    Returns a summary of what was synced.
    """
    result = await db.execute(
        select(WearableIntegration).where(
            WearableIntegration.client_id == client.id,
            WearableIntegration.provider == IntegrationProvider.WHOOP,
        )
    )
    integration = result.scalars().first()
    if not integration:
        raise ValueError("WHOOP not connected. Please connect WHOOP first.")

    token = await _get_valid_token(db, integration)
    headers = {"Authorization": f"Bearer {token}"}

    synced = {"recovery": 0, "sleep": 0, "workouts": 0}

    async with httpx.AsyncClient(timeout=30) as http:
        # Fetch recovery (contains HRV, resting HR, recovery score)
        rec_resp = await http.get(
            f"{WHOOP_API_BASE}/recovery",
            headers=headers,
            params={"limit": 25},
        )
        if rec_resp.status_code == 200:
            for rec in rec_resp.json().get("records", []):
                cycle_start = rec.get("created_at", "")[:10]  # YYYY-MM-DD
                if not cycle_start:
                    continue
                try:
                    from datetime import date
                    data_date = date.fromisoformat(cycle_start)
                except ValueError:
                    continue

                score = rec.get("score", {})
                await _upsert_wearable(db, client.id, data_date, {
                    "hrv_ms": score.get("hrv_rmssd_milli"),
                    "resting_hr": score.get("resting_heart_rate"),
                    "recovery_score": score.get("recovery_score"),
                    "skin_temp_deviation": score.get("skin_temp_deviation_fahrenheit"),
                })
                synced["recovery"] += 1

        # Fetch sleep
        sleep_resp = await http.get(
            f"{WHOOP_API_BASE}/activity/sleep",
            headers=headers,
            params={"limit": 25},
        )
        if sleep_resp.status_code == 200:
            for s in sleep_resp.json().get("records", []):
                start = s.get("start", "")[:10]
                if not start:
                    continue
                try:
                    data_date = date.fromisoformat(start)
                except ValueError:
                    continue

                score = s.get("score", {})
                stage_summary = score.get("stage_summary", {})
                total_ms = stage_summary.get("total_in_bed_time_milli", 0)
                sleep_hours = round(total_ms / 3_600_000, 2) if total_ms else None
                deep_ms = stage_summary.get("total_slow_wave_sleep_time_milli", 0)
                rem_ms = stage_summary.get("total_rem_sleep_time_milli", 0)

                await _upsert_wearable(db, client.id, data_date, {
                    "sleep_hours": sleep_hours,
                    "sleep_efficiency": score.get("sleep_efficiency_percentage"),
                    "deep_sleep_hours": round(deep_ms / 3_600_000, 2) if deep_ms else None,
                    "rem_sleep_hours": round(rem_ms / 3_600_000, 2) if rem_ms else None,
                    "readiness_score": score.get("respiratory_rate"),  # proxy
                })
                synced["sleep"] += 1

        # Fetch workouts (for zone 2 / strain)
        workout_resp = await http.get(
            f"{WHOOP_API_BASE}/activity/workout",
            headers=headers,
            params={"limit": 25},
        )
        if workout_resp.status_code == 200:
            for w in workout_resp.json().get("records", []):
                start = w.get("start", "")[:10]
                if not start:
                    continue
                try:
                    data_date = date.fromisoformat(start)
                except ValueError:
                    continue

                score = w.get("score", {})
                zone_duration = score.get("zone_duration", {})
                # Zone 2 = zones 3+4 in WHOOP's 5-zone model (moderate intensity)
                zone2_ms = (
                    zone_duration.get("zone_three_milli", 0) +
                    zone_duration.get("zone_four_milli", 0)
                )
                zone2_minutes = round(zone2_ms / 60_000) if zone2_ms else None

                await _upsert_wearable(db, client.id, data_date, {
                    "strain_score": score.get("strain"),
                    "active_calories": score.get("kilojoule") and int(score["kilojoule"] / 4.184),
                    "zone2_minutes": zone2_minutes,
                })
                synced["workouts"] += 1

    await db.flush()
    return synced


async def _upsert_wearable(
    db: AsyncSession, client_id, data_date, fields: dict
) -> None:
    """Upsert a WearableData record for a given date from WHOOP."""
    from datetime import date as _date
    result = await db.execute(
        select(WearableData).where(
            WearableData.client_id == client_id,
            WearableData.data_date == data_date,
            WearableData.source == WearableSource.WHOOP,
        )
    )
    record = result.scalars().first()
    if not record:
        record = WearableData(
            client_id=client_id,
            data_date=data_date,
            source=WearableSource.WHOOP,
        )
        db.add(record)

    for field, value in fields.items():
        if value is not None:
            setattr(record, field, value)
