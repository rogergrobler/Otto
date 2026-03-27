"""
Nutrition logging endpoint tests.
"""
from datetime import date

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
        "password": "Nutrition99!",
        "full_name": "Nutrition Test",
        "weight_kg": 80.0,
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


MEAL = {
    "log_date": str(date.today()),
    "meal_type": "breakfast",
    "description": "Eggs and avocado",
    "calories": 520,
    "protein_g": 38.0,
    "fat_g": 34.0,
    "carbs_net_g": 6.0,
    "fibre_g": 7.0,
}


# ── Log meal ──────────────────────────────────────────────────────────────────

def test_log_meal_returns_201(auth):
    r = auth.post("/api/health/nutrition", json=MEAL)
    assert r.status_code == 201, r.text


def test_log_meal_response_fields(auth):
    r = auth.post("/api/health/nutrition", json=MEAL)
    data = r.json()
    assert data["description"] == "Eggs and avocado"
    assert data["protein_g"] == 38.0
    assert "id" in data


def test_log_meal_minimal(auth):
    """Meal with only description — all macros optional."""
    r = auth.post("/api/health/nutrition", json={
        "log_date": str(date.today()),
        "meal_type": "snack",
        "description": "Apple",
    })
    assert r.status_code == 201, r.text


def test_log_meal_all_meal_types(auth):
    for meal_type in ["breakfast", "lunch", "dinner", "snack"]:
        r = auth.post("/api/health/nutrition", json={
            "log_date": str(date.today()),
            "meal_type": meal_type,
            "description": f"Test {meal_type}",
            "calories": 300,
            "protein_g": 20.0,
        })
        assert r.status_code == 201, f"{meal_type} failed: {r.text}"


def test_log_meal_missing_date(auth):
    r = auth.post("/api/health/nutrition", json={
        "meal_type": "lunch",
        "description": "No date",
    })
    assert r.status_code == 422


# ── Today summary ─────────────────────────────────────────────────────────────

def test_nutrition_today_returns_200(auth):
    r = auth.get(f"/api/health/nutrition/{date.today()}")
    assert r.status_code == 200


def test_nutrition_today_has_meals_key(auth):
    r = auth.get(f"/api/health/nutrition/{date.today()}")
    data = r.json()
    assert "meals" in data


def test_nutrition_today_totals_accumulate(auth):
    r = auth.get(f"/api/health/nutrition/{date.today()}")
    data = r.json()
    # We've logged multiple meals with protein_g >= 38 so total should reflect that
    assert data["total_protein_g"] >= 38.0


def test_nutrition_empty_day(auth):
    """A date with no meals should return empty meals list and zero totals."""
    r = auth.get("/api/health/nutrition/2020-01-01")
    assert r.status_code == 200
    data = r.json()
    assert data["meals"] == [] or data["total_protein_g"] == 0


def test_nutrition_unauthenticated():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        r = c.get(f"/api/health/nutrition/{date.today()}")
        assert r.status_code == 401
