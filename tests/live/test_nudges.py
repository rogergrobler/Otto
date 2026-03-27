"""
Nudges endpoint tests.
"""
import uuid

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
        "password": "Nudge99!",
        "full_name": "Nudge Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


# Second user for isolation tests
@pytest.fixture(scope="module")
def auth2(http):
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "Nudge99!",
        "full_name": "Nudge Test 2",
    })
    assert r.status_code == 201
    # Return a separate client with second user's token
    client2 = httpx.Client(base_url=API_BASE, timeout=TIMEOUT)
    client2.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return client2


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_nudges_returns_200(auth):
    r = auth.get("/api/nudges")
    assert r.status_code == 200, r.text


def test_list_nudges_is_list(auth):
    r = auth.get("/api/nudges")
    assert isinstance(r.json(), list)


def test_list_nudges_unread_only_default(auth):
    """Default behaviour is unread_only=true."""
    r = auth.get("/api/nudges")
    for nudge in r.json():
        assert nudge["acknowledged_at"] is None


def test_list_nudges_all(auth):
    r = auth.get("/api/nudges?unread_only=false")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_nudge_response_schema(auth):
    """Any nudge returned must have the expected fields."""
    r = auth.get("/api/nudges?unread_only=false")
    for nudge in r.json():
        assert "id" in nudge
        assert "message" in nudge
        assert "nudge_type" in nudge
        assert "scheduled_at" in nudge
        assert "acknowledged_at" in nudge


# ── Acknowledge ───────────────────────────────────────────────────────────────

def test_acknowledge_nonexistent_nudge(auth):
    r = auth.post(f"/api/nudges/{uuid.uuid4()}/acknowledge")
    assert r.status_code == 404


def test_acknowledge_other_users_nudge(auth, auth2):
    """User cannot acknowledge another user's nudge."""
    # Get nudges for user1 (may be empty for a new test user)
    nudges1 = auth.get("/api/nudges?unread_only=false").json()
    if not nudges1:
        pytest.skip("No nudges available for cross-user test")

    nudge_id = nudges1[0]["id"]
    r = auth2.post(f"/api/nudges/{nudge_id}/acknowledge")
    assert r.status_code == 404  # Returns 404 (not found for that user), not 403


def test_nudges_unauthenticated():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        r = c.get("/api/nudges")
        assert r.status_code == 401
