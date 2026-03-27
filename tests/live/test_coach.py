"""
Coach portal access control tests.
Regular clients must be blocked from all coach routes.
"""
import httpx
import pytest

from tests.live.conftest import API_BASE, TIMEOUT, unique_email

COACH_ROUTES = [
    ("GET", "/api/coach/patients"),
    ("GET", "/api/coach/patients/00000000-0000-0000-0000-000000000000"),
    ("GET", "/api/coach/patients/00000000-0000-0000-0000-000000000000/notes"),
]


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def client_token(http):
    """A standard (non-coach) client token."""
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "Coach99!",
        "full_name": "Regular Client",
    })
    assert r.status_code == 201
    return r.json()["access_token"]


# ── Client cannot access coach routes ─────────────────────────────────────────

@pytest.mark.parametrize("method,path", COACH_ROUTES)
def test_coach_route_blocked_for_client(http, client_token, method, path):
    headers = {"Authorization": f"Bearer {client_token}"}
    r = http.request(method, path, headers=headers)
    assert r.status_code in (401, 403), \
        f"{method} {path} returned {r.status_code} for regular client — should be 401/403"


# ── Unauthenticated access blocked ────────────────────────────────────────────

@pytest.mark.parametrize("method,path", COACH_ROUTES)
def test_coach_route_blocked_unauthenticated(http, method, path):
    r = http.request(method, path)
    assert r.status_code == 401, \
        f"{method} {path} returned {r.status_code} without auth — should be 401"
