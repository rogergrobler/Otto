"""
Auth endpoint tests — register, login, refresh, access control.
"""
import uuid
import httpx
import pytest
from tests.live.conftest import API_BASE, TIMEOUT, unique_email


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


EMAIL = unique_email()
PASSWORD = "AuthTest99!"
NAME = "Auth Test User"


# ── Register ──────────────────────────────────────────────────────────────────

def test_register_success(client):
    r = client.post("/api/auth/register", json={
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": NAME,
    })
    assert r.status_code == 201, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_returns_valid_jwt(client):
    email = unique_email()
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": PASSWORD,
        "full_name": NAME,
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    # Token must be usable immediately
    profile = client.get("/api/health/profile",
                         headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200


def test_register_with_biometrics(client):
    email = unique_email()
    r = client.post("/api/auth/register", json={
        "email": email,
        "password": PASSWORD,
        "full_name": "Bio User",
        "weight_kg": 80.0,
        "height_cm": 175.0,
    })
    assert r.status_code == 201
    token = r.json()["access_token"]
    profile = client.get("/api/health/profile",
                         headers={"Authorization": f"Bearer {token}"})
    assert profile.status_code == 200
    data = profile.json()
    assert data["weight_kg"] == 80.0
    assert data["height_cm"] == 175.0


def test_register_duplicate_email(client):
    r = client.post("/api/auth/register", json={
        "email": EMAIL,
        "password": PASSWORD,
        "full_name": NAME,
    })
    assert r.status_code in (400, 409), r.text


def test_register_missing_email(client):
    r = client.post("/api/auth/register", json={
        "password": PASSWORD,
        "full_name": NAME,
    })
    assert r.status_code == 422


def test_register_missing_password(client):
    r = client.post("/api/auth/register", json={
        "email": unique_email(),
        "full_name": NAME,
    })
    assert r.status_code == 422


def test_register_missing_name(client):
    r = client.post("/api/auth/register", json={
        "email": unique_email(),
        "password": PASSWORD,
    })
    assert r.status_code == 422


# ── Login ─────────────────────────────────────────────────────────────────────

def test_login_success(client):
    r = client.post("/api/auth/login", json={
        "email": EMAIL,
        "password": PASSWORD,
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    r = client.post("/api/auth/login", json={
        "email": EMAIL,
        "password": "WrongPassword999",
    })
    assert r.status_code == 401


def test_login_nonexistent_email(client):
    r = client.post("/api/auth/login", json={
        "email": f"nobody-{uuid.uuid4().hex}@example.com",
        "password": PASSWORD,
    })
    assert r.status_code == 401


def test_login_missing_email(client):
    r = client.post("/api/auth/login", json={"password": PASSWORD})
    assert r.status_code == 422


def test_login_missing_password(client):
    r = client.post("/api/auth/login", json={"email": EMAIL})
    assert r.status_code == 422


# ── Token refresh ─────────────────────────────────────────────────────────────

def test_refresh_token(client):
    login = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    refresh_token = login.json()["refresh_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "access_token" in data


def test_refresh_with_access_token_fails(client):
    login = client.post("/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    access_token = login.json()["access_token"]

    r = client.post("/api/auth/refresh", json={"refresh_token": access_token})
    assert r.status_code == 401


def test_refresh_with_garbage_fails(client):
    r = client.post("/api/auth/refresh", json={"refresh_token": "not.a.token"})
    assert r.status_code == 401


# ── Protected routes without token ───────────────────────────────────────────

@pytest.mark.parametrize("path", [
    "/api/health/profile",
    "/api/health/labs",
    "/api/health/nutrition/today",
    "/api/health/goals",
    "/api/health/wearables",
    "/api/health/risk",
    "/api/nudges",
])
def test_protected_route_no_token(client, path):
    r = client.get(path)
    assert r.status_code == 401, f"{path} should require auth, got {r.status_code}"


def test_protected_route_bad_token(client):
    r = client.get("/api/health/profile",
                   headers={"Authorization": "Bearer this.is.garbage"})
    assert r.status_code == 401
