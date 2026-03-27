"""
Risk score endpoint tests.
"""
import httpx
import pytest

from tests.live.conftest import API_BASE, TIMEOUT, unique_email

VALID_STATUSES = {"green", "amber", "red", "insufficient_data"}
VALID_DOMAINS = {"cardiovascular", "metabolic", "neurological", "cancer"}


@pytest.fixture(scope="module")
def http():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def auth(http):
    r = http.post("/api/auth/register", json={
        "email": unique_email(),
        "password": "RiskTest99!",
        "full_name": "Risk Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


def test_risk_returns_200(auth):
    r = auth.get("/api/health/risk")
    assert r.status_code == 200, r.text


def test_risk_has_health_score(auth):
    data = auth.get("/api/health/risk").json()
    assert "health_score" in data
    score = data["health_score"]
    assert 0 <= score <= 100


def test_risk_has_domains(auth):
    data = auth.get("/api/health/risk").json()
    assert "domains" in data
    assert isinstance(data["domains"], (dict, list))


def test_risk_domain_statuses_valid(auth):
    data = auth.get("/api/health/risk").json()
    domains = data.get("domains", {})
    if isinstance(domains, dict):
        for domain, status in domains.items():
            assert status in VALID_STATUSES, f"Domain {domain} has invalid status: {status}"


def test_risk_unauthenticated():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        r = c.get("/api/health/risk")
        assert r.status_code == 401
