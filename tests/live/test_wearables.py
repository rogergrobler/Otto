"""
Wearable data endpoint tests.
"""
from datetime import date, timedelta

import httpx
import pytest

from tests.live.conftest import API_BASE, TIMEOUT, unique_email


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def auth(http):
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "Wearable99!",
        "full_name": "Wearable Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


TODAY = str(date.today())
YESTERDAY = str(date.today() - timedelta(days=1))

FULL_PAYLOAD = {
    "data_date": TODAY,
    "source": "manual",
    "sleep_hours": 7.2,
    "hrv_ms": 58.0,
    "resting_hr": 52,
    "recovery_score": 74.0,
    "zone2_minutes": 45,
    "steps": 9200,
}


# ── Create / Upsert ───────────────────────────────────────────────────────────

def test_log_wearable_returns_201(auth):
    r = auth.post("/api/health/wearables", json=FULL_PAYLOAD)
    assert r.status_code == 201, r.text


def test_log_wearable_response_fields(auth):
    r = auth.post("/api/health/wearables", json=FULL_PAYLOAD)
    data = r.json()
    assert data["sleep_hours"] == 7.2
    assert data["hrv_ms"] == 58.0
    assert data["recovery_score"] == 74.0
    assert data["zone2_minutes"] == 45
    assert "id" in data


def test_log_wearable_minimal(auth):
    """Only date required, all metrics optional."""
    r = auth.post("/api/health/wearables", json={
        "data_date": YESTERDAY,
        "source": "manual",
    })
    assert r.status_code == 201, r.text


def test_upsert_same_date_updates(auth):
    """Posting same date+source should update, not duplicate."""
    auth.post("/api/health/wearables", json={
        "data_date": TODAY, "source": "manual", "sleep_hours": 7.0,
    })
    auth.post("/api/health/wearables", json={
        "data_date": TODAY, "source": "manual", "sleep_hours": 8.0,
    })
    r = auth.get("/api/health/wearables")
    todays = [w for w in r.json() if w["data_date"] == TODAY]
    assert len(todays) == 1
    assert todays[0]["sleep_hours"] == 8.0


def test_log_multiple_dates(auth):
    for i in range(1, 4):
        d = str(date.today() - timedelta(days=i))
        r = auth.post("/api/health/wearables", json={
            "data_date": d,
            "source": "manual",
            "hrv_ms": 50.0 + i,
            "sleep_hours": 7.0,
        })
        assert r.status_code == 201, f"day -{i} failed: {r.text}"


def test_sleep_hours_bounds(auth):
    """sleep_hours must be between 0 and 24."""
    r = auth.post("/api/health/wearables", json={
        "data_date": TODAY, "source": "manual", "sleep_hours": 25.0,
    })
    assert r.status_code == 422


def test_resting_hr_bounds(auth):
    r = auth.post("/api/health/wearables", json={
        "data_date": TODAY, "source": "manual", "resting_hr": 5,
    })
    assert r.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_wearables_returns_200(auth):
    r = auth.get("/api/health/wearables")
    assert r.status_code == 200


def test_list_wearables_is_list(auth):
    r = auth.get("/api/health/wearables")
    assert isinstance(r.json(), list)


def test_list_wearables_has_data(auth):
    r = auth.get("/api/health/wearables")
    assert len(r.json()) >= 1


def test_list_wearables_ordered_desc(auth):
    r = auth.get("/api/health/wearables")
    dates = [w["data_date"] for w in r.json()]
    assert dates == sorted(dates, reverse=True)


def test_wearables_unauthenticated(http):
    r = http.get("/api/health/wearables")
    assert r.status_code == 401
