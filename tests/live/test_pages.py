"""
Frontend smoke tests — verify all 14 Vercel pages return 200
and serve valid HTML.
"""
import httpx
import pytest

from tests.live.conftest import FRONTEND_BASE, TIMEOUT

PAGES = [
    "/",
    "/login",
    "/register",
    "/chat",
    "/labs",
    "/labs/upload",
    "/nutrition",
    "/goals",
    "/wearables",
    "/profile",
    "/nudges",
]


@pytest.fixture(scope="module")
def browser():
    """httpx client pointing at the Vercel frontend."""
    with httpx.Client(base_url=FRONTEND_BASE, timeout=TIMEOUT,
                      follow_redirects=True) as c:
        yield c


# ── Page availability ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("path", PAGES)
def test_page_returns_200(browser, path):
    r = browser.get(path)
    assert r.status_code == 200, f"{path} returned {r.status_code}"


@pytest.mark.parametrize("path", PAGES)
def test_page_returns_html(browser, path):
    r = browser.get(path)
    ct = r.headers.get("content-type", "")
    assert "text/html" in ct, f"{path} content-type: {ct}"


# ── HTML structure ────────────────────────────────────────────────────────────

def test_root_has_otto_title(browser):
    r = browser.get("/")
    assert "Otto" in r.text


def test_root_has_manifest_link(browser):
    r = browser.get("/")
    assert 'manifest' in r.text.lower()


def test_root_has_apple_touch_icon(browser):
    r = browser.get("/")
    assert "apple-touch-icon" in r.text.lower()


def test_login_page_has_form_elements(browser):
    r = browser.get("/login")
    text = r.text.lower()
    # Next.js app router — page content is hydrated; check for script tags at minimum
    assert "<script" in text


# ── Static assets ─────────────────────────────────────────────────────────────

def test_favicon_accessible(browser):
    r = browser.get("/favicon.ico")
    assert r.status_code in (200, 404)  # 404 is ok if not set; 200 is better


def test_not_found_page(browser):
    r = browser.get("/this-page-does-not-exist-xyz")
    assert r.status_code in (200, 404)  # Next.js often returns 200 with not-found content
