"""
PWA asset tests — manifest, service worker, icons, meta tags.
"""
import json

import httpx
import pytest

from tests.live.conftest import FRONTEND_BASE, TIMEOUT

REQUIRED_MANIFEST_FIELDS = ["name", "short_name", "start_url", "display", "icons"]
REQUIRED_ICON_SIZES = {"192x192", "512x512"}


@pytest.fixture(scope="module")
def browser():
    with httpx.Client(base_url=FRONTEND_BASE, timeout=TIMEOUT,
                      follow_redirects=True) as c:
        yield c


# ── manifest.json ─────────────────────────────────────────────────────────────

def test_manifest_accessible(browser):
    r = browser.get("/manifest.json")
    assert r.status_code == 200, f"manifest.json returned {r.status_code}"


def test_manifest_is_valid_json(browser):
    r = browser.get("/manifest.json")
    try:
        data = r.json()
    except Exception:
        pytest.fail("manifest.json is not valid JSON")
    assert isinstance(data, dict)


def test_manifest_has_required_fields(browser):
    data = browser.get("/manifest.json").json()
    for field in REQUIRED_MANIFEST_FIELDS:
        assert field in data, f"manifest.json missing field: {field}"


def test_manifest_display_is_standalone(browser):
    data = browser.get("/manifest.json").json()
    assert data["display"] == "standalone", \
        f"Expected display: standalone, got: {data.get('display')}"


def test_manifest_has_icon_sizes(browser):
    data = browser.get("/manifest.json").json()
    sizes = {icon["sizes"] for icon in data.get("icons", [])}
    for required in REQUIRED_ICON_SIZES:
        assert required in sizes, f"Missing icon size: {required}. Found: {sizes}"


def test_manifest_start_url(browser):
    data = browser.get("/manifest.json").json()
    assert data["start_url"] == "/"


def test_manifest_has_theme_color(browser):
    data = browser.get("/manifest.json").json()
    assert "theme_color" in data or "background_color" in data


def test_manifest_name_is_otto(browser):
    data = browser.get("/manifest.json").json()
    assert "Otto" in data.get("name", "") or "Otto" in data.get("short_name", "")


# ── Service worker ────────────────────────────────────────────────────────────

def test_service_worker_accessible(browser):
    r = browser.get("/sw.js")
    assert r.status_code == 200, f"sw.js returned {r.status_code}"


def test_service_worker_is_javascript(browser):
    r = browser.get("/sw.js")
    ct = r.headers.get("content-type", "")
    assert "javascript" in ct or "text/" in ct, f"sw.js content-type: {ct}"


def test_service_worker_has_install_handler(browser):
    r = browser.get("/sw.js")
    assert "install" in r.text


def test_service_worker_has_fetch_handler(browser):
    r = browser.get("/sw.js")
    assert "fetch" in r.text


# ── Icons ─────────────────────────────────────────────────────────────────────

def test_icon_192_accessible(browser):
    r = browser.get("/icons/icon-192.png")
    assert r.status_code == 200


def test_icon_512_accessible(browser):
    r = browser.get("/icons/icon-512.png")
    assert r.status_code == 200


def test_apple_touch_icon_accessible(browser):
    r = browser.get("/icons/apple-touch-icon.png")
    assert r.status_code == 200


def test_icon_192_is_png(browser):
    r = browser.get("/icons/icon-192.png")
    # PNG magic bytes: 89 50 4E 47
    assert r.content[:4] == b"\x89PNG", "icon-192.png is not a valid PNG"


def test_icon_512_is_png(browser):
    r = browser.get("/icons/icon-512.png")
    assert r.content[:4] == b"\x89PNG", "icon-512.png is not a valid PNG"
