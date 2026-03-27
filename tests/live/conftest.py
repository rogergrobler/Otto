"""
Shared fixtures for live integration tests.

All tests run against the deployed Railway API and the Vercel frontend.
Each module-scoped test session creates its own isolated user.
"""
import os
import uuid

import httpx
import pytest

API_BASE = os.getenv("OTTO_API_URL", "https://otto-production-924c.up.railway.app")
FRONTEND_BASE = os.getenv("OTTO_FRONTEND_URL", "https://frontend-lyart-ten-72.vercel.app")
VERCEL_ORIGIN = FRONTEND_BASE

# Standard timeouts
TIMEOUT = 30


def unique_email() -> str:
    return f"test-{uuid.uuid4().hex[:10]}@example.com"


def make_client() -> httpx.Client:
    return httpx.Client(base_url=API_BASE, timeout=TIMEOUT)


def register_and_login(client: httpx.Client, email: str, password: str, name: str) -> str:
    """Register a new user and return an access token."""
    reg = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": name,
    })
    assert reg.status_code == 201, f"Registration failed: {reg.text}"
    return reg.json()["access_token"]


def authed_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Module-scoped fixtures ─────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def http():
    """Plain httpx client (no auth)."""
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def user_credentials():
    """One set of credentials shared across a test module."""
    return {
        "email": unique_email(),
        "password": "TestPass99!",
        "name": "Live Test User",
    }


@pytest.fixture(scope="module")
def token(http, user_credentials):
    """Register a user and return access token."""
    return register_and_login(
        http,
        user_credentials["email"],
        user_credentials["password"],
        user_credentials["name"],
    )


@pytest.fixture(scope="module")
def auth(http, token):
    """httpx client with Authorization header pre-set."""
    http.headers.update(authed_headers(token))
    return http
