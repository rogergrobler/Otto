"""
Live integration tests against the deployed Railway API.

Run with:
    pytest tests/test_live_api.py -v

Requires OTTO_API_URL env var (defaults to Railway production URL).
Each test run creates a fresh test user so tests are isolated.
"""
import os
import uuid
from datetime import date

import httpx
import pytest

BASE_URL = os.getenv("OTTO_API_URL", "https://otto-production-924c.up.railway.app")
TEST_EMAIL = f"ci-test-{uuid.uuid4().hex[:8]}@example.com"
TEST_PASSWORD = "CiTestPass99"
TEST_NAME = "CI Test User"


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30) as c:
        yield c


@pytest.fixture(scope="module")
def auth_token(client):
    """Register a fresh test user and return a JWT token."""
    reg = client.post("/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    assert reg.status_code == 201, f"Registration failed: {reg.text}"

    login = client.post("/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
    })
    assert login.status_code == 200, f"Login failed: {login.text}"
    return login.json()["access_token"]


@pytest.fixture(scope="module")
def authed(client, auth_token):
    """httpx client with auth header pre-set."""
    client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


# ── Health ────────────────────────────────────────────────────────────────────

def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "service": "otto"}


def test_openapi_schema(client):
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_duplicate_email(client, auth_token):
    """Second registration with same email should 409."""
    r = client.post("/api/auth/register", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD,
        "full_name": TEST_NAME,
    })
    assert r.status_code in (400, 409)


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": "wrongpassword",
    })
    assert r.status_code == 401


def test_protected_route_no_token(client):
    r = client.get("/api/health/profile")
    assert r.status_code == 401


# ── Health Profile ────────────────────────────────────────────────────────────

def test_get_profile(authed):
    r = authed.get("/api/health/profile")
    assert r.status_code == 200
    data = r.json()
    assert data["full_name"] == TEST_NAME
    assert data["email"] == TEST_EMAIL


def test_update_profile(authed):
    r = authed.patch("/api/health/profile", json={
        "weight_kg": 82.5,
        "height_cm": 178.0,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["weight_kg"] == 82.5
    assert data["height_cm"] == 178.0


# ── Labs ──────────────────────────────────────────────────────────────────────

def test_create_lab_result(authed):
    r = authed.post("/api/health/labs", json={
        "marker_name": "ApoB",
        "value": 0.82,
        "unit": "g/L",
        "flag": "normal",
        "test_date": str(date.today()),
        "lab_name": "CI Lab",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["marker_name"] == "ApoB"
    assert data["value"] == 0.82
    return data["id"]


def test_list_labs(authed):
    r = authed.get("/api/health/labs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert any(l["marker_name"] == "ApoB" for l in r.json())


# ── Nutrition ─────────────────────────────────────────────────────────────────

def test_log_nutrition(authed):
    r = authed.post("/api/health/nutrition", json={
        "log_date": str(date.today()),
        "meal_type": "breakfast",
        "description": "Eggs and avocado",
        "calories": 520,
        "protein_g": 38.0,
        "fat_g": 34.0,
        "carbs_net_g": 6.0,
        "fibre_g": 7.0,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["description"] == "Eggs and avocado"
    assert data["protein_g"] == 38.0


def test_nutrition_today(authed):
    r = authed.get(f"/api/health/nutrition/{date.today()}")
    assert r.status_code == 200
    data = r.json()
    assert "meals" in data
    assert data["total_protein_g"] >= 38.0


# ── Goals ─────────────────────────────────────────────────────────────────────

def test_create_goal(authed):
    r = authed.post("/api/health/goals", json={
        "domain": "cardiovascular",
        "goal_text": "Reduce ApoB below 0.7 g/L",
        "target_value": "0.70",
        "current_value": "0.82",
        "deadline": "2026-12-31",
    })
    assert r.status_code == 201
    data = r.json()
    assert data["domain"] == "cardiovascular"
    assert data["status"] == "active"


def test_list_goals(authed):
    r = authed.get("/api/health/goals")
    assert r.status_code == 200
    goals = r.json()
    assert isinstance(goals, list)
    assert any(g["domain"] == "cardiovascular" for g in goals)


# ── Wearables ─────────────────────────────────────────────────────────────────

def test_log_wearable(authed):
    r = authed.post("/api/health/wearables", json={
        "data_date": str(date.today()),
        "source": "manual",
        "sleep_hours": 7.2,
        "hrv_ms": 58.0,
        "resting_hr": 52,
        "recovery_score": 74.0,
        "zone2_minutes": 45,
        "steps": 9200,
    })
    assert r.status_code == 201
    data = r.json()
    assert data["sleep_hours"] == 7.2
    assert data["hrv_ms"] == 58.0


def test_list_wearables(authed):
    r = authed.get("/api/health/wearables")
    assert r.status_code == 200
    records = r.json()
    assert isinstance(records, list)
    assert len(records) >= 1


def test_wearable_upsert(authed):
    """Posting same date+source again should update, not create duplicate."""
    r = authed.post("/api/health/wearables", json={
        "data_date": str(date.today()),
        "source": "manual",
        "sleep_hours": 7.5,
        "hrv_ms": 62.0,
    })
    assert r.status_code == 201
    r2 = authed.get("/api/health/wearables")
    todays = [w for w in r2.json() if w["data_date"] == str(date.today())]
    assert len(todays) == 1
    assert todays[0]["sleep_hours"] == 7.5


# ── Nudges ────────────────────────────────────────────────────────────────────

def test_list_nudges(authed):
    r = authed.get("/api/nudges")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ── Coach Portal access control ───────────────────────────────────────────────

def test_coach_routes_require_admin(authed):
    """A regular client token must not access coach routes."""
    r = authed.get("/api/coach/patients")
    assert r.status_code in (401, 403)


# ── Risk (smoke) ──────────────────────────────────────────────────────────────

def test_get_risk_scores_empty(authed):
    """Fresh user has no risk scores yet — should return empty domains list."""
    r = authed.get("/api/health/risk")
    assert r.status_code == 200
    data = r.json()
    assert "health_score" in data
    assert "domains" in data
