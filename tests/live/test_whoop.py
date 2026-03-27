"""
WHOOP integration endpoint tests.
Full OAuth callback cannot be automated, but we verify all reachable states.
"""
import httpx
import pytest

from tests.live.conftest import API_BASE, TIMEOUT, unique_email

WHOOP_AUTH_HOST = "api.prod.whoop.com"


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def auth(http):
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "Whoop99!",
        "full_name": "WHOOP Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


# ── Status ────────────────────────────────────────────────────────────────────

def test_whoop_status_returns_200(auth):
    r = auth.get("/api/integrations/whoop/status")
    assert r.status_code == 200, r.text


def test_whoop_status_not_connected(auth):
    r = auth.get("/api/integrations/whoop/status")
    data = r.json()
    assert "connected" in data
    assert data["connected"] is False


def test_whoop_status_unauthenticated(http):
    r = http.get("/api/integrations/whoop/status")
    assert r.status_code == 401


# ── Connect URL ───────────────────────────────────────────────────────────────

def test_whoop_connect_url_returns_200(auth):
    r = auth.get("/api/integrations/whoop/connect-url")
    assert r.status_code == 200, r.text


def test_whoop_connect_url_has_url_field(auth):
    r = auth.get("/api/integrations/whoop/connect-url")
    data = r.json()
    assert "url" in data


def test_whoop_connect_url_points_to_whoop(auth):
    r = auth.get("/api/integrations/whoop/connect-url")
    url = r.json()["url"]
    assert WHOOP_AUTH_HOST in url, f"Expected WHOOP URL, got: {url}"


def test_whoop_connect_url_has_required_params(auth):
    r = auth.get("/api/integrations/whoop/connect-url")
    url = r.json()["url"]
    assert "client_id=" in url
    assert "redirect_uri=" in url
    assert "state=" in url
    assert "scope=" in url


def test_whoop_connect_url_unauthenticated(http):
    r = http.get("/api/integrations/whoop/connect-url")
    assert r.status_code == 401


# ── Sync (without connection) ─────────────────────────────────────────────────

def test_whoop_sync_without_connection_returns_400(auth):
    r = auth.post("/api/integrations/whoop/sync")
    assert r.status_code == 400, r.text
    assert "not connected" in r.json().get("detail", "").lower()
