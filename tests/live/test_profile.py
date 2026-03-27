"""
Health profile endpoint tests.
"""
import pytest
from tests.live.conftest import unique_email, API_BASE, TIMEOUT
import httpx


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def token(http):
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "Profile99!",
        "full_name": "Profile Test",
        "weight_kg": 75.0,
        "height_cm": 180.0,
    })
    assert r.status_code == 201
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def auth(http, token):
    http.headers.update({"Authorization": f"Bearer {token}"})
    return http


# ── GET profile ───────────────────────────────────────────────────────────────

def test_get_profile_returns_200(auth):
    r = auth.get("/api/health/profile")
    assert r.status_code == 200


def test_get_profile_has_required_fields(auth):
    r = auth.get("/api/health/profile")
    data = r.json()
    assert "id" in data
    assert "full_name" in data
    assert "email" in data


def test_get_profile_initial_biometrics(auth):
    r = auth.get("/api/health/profile")
    data = r.json()
    assert data["weight_kg"] == 75.0
    assert data["height_cm"] == 180.0


# ── PATCH profile ─────────────────────────────────────────────────────────────

def test_update_weight(auth):
    r = auth.patch("/api/health/profile", json={"weight_kg": 74.5})
    assert r.status_code == 200
    assert r.json()["weight_kg"] == 74.5


def test_update_height(auth):
    r = auth.patch("/api/health/profile", json={"height_cm": 181.0})
    assert r.status_code == 200
    assert r.json()["height_cm"] == 181.0


def test_update_protein_target(auth):
    r = auth.patch("/api/health/profile", json={"daily_protein_target_g": 150})
    assert r.status_code == 200
    assert r.json()["daily_protein_target_g"] == 150


def test_update_multiple_fields(auth):
    r = auth.patch("/api/health/profile", json={
        "weight_kg": 73.0,
        "daily_fibre_target_g": 35,
    })
    assert r.status_code == 200
    data = r.json()
    assert data["weight_kg"] == 73.0
    assert data["daily_fibre_target_g"] == 35


def test_empty_patch_is_ok(auth):
    r = auth.patch("/api/health/profile", json={})
    assert r.status_code == 200


def test_profile_unauthenticated():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        r = c.get("/api/health/profile")
        assert r.status_code == 401
