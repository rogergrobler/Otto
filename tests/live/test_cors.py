"""
CORS tests — verify the backend sends correct headers for browser requests
originating from the Vercel frontend.

This is the root cause of login/register failing in the browser.
"""
import httpx
import pytest

from tests.live.conftest import API_BASE, TIMEOUT, VERCEL_ORIGIN

LOCALHOST_ORIGIN = "http://localhost:3000"


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


# ── Preflight (OPTIONS) from Vercel origin ────────────────────────────────────

def test_preflight_register_from_vercel(http):
    """Browser sends OPTIONS before POST /api/auth/register."""
    r = http.options(
        "/api/auth/register",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code in (200, 204), \
        f"Preflight failed with {r.status_code}: {r.text}"


def test_preflight_returns_allow_origin_vercel(http):
    r = http.options(
        "/api/auth/login",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )
    acao = r.headers.get("access-control-allow-origin", "")
    assert acao == VERCEL_ORIGIN or acao == "*", \
        f"Expected ACAO header to be Vercel origin or *, got: '{acao}'"


def test_preflight_returns_allow_credentials(http):
    r = http.options(
        "/api/auth/login",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    acac = r.headers.get("access-control-allow-credentials", "")
    assert acac.lower() == "true", \
        f"Expected ACAC: true, got: '{acac}'"


def test_preflight_allows_authorization_header(http):
    r = http.options(
        "/api/health/profile",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    acah = r.headers.get("access-control-allow-headers", "").lower()
    assert "authorization" in acah or "*" in acah, \
        f"Authorization not in allowed headers: '{acah}'"


# ── Actual request carries CORS headers ──────────────────────────────────────

def test_actual_request_has_acao_header(http):
    """A real GET request with Origin should return ACAO header."""
    r = http.get(
        "/health",
        headers={"Origin": VERCEL_ORIGIN},
    )
    assert r.status_code == 200
    acao = r.headers.get("access-control-allow-origin", "")
    assert acao, f"No Access-Control-Allow-Origin header on response"


def test_preflight_localhost_allowed(http):
    """localhost:3000 (dev) should also be permitted."""
    r = http.options(
        "/api/auth/login",
        headers={
            "Origin": LOCALHOST_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert r.status_code in (200, 204), \
        f"localhost preflight failed: {r.status_code}"
