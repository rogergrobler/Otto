"""
Health goals endpoint tests.
"""
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
        "password": "Goals99!",
        "full_name": "Goals Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


GOAL = {
    "domain": "cardiovascular",
    "goal_text": "Reduce ApoB below 0.7 g/L",
    "target_value": "0.70",
    "current_value": "0.82",
    "deadline": "2026-12-31",
}


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_goal_returns_201(auth):
    r = auth.post("/api/health/goals", json=GOAL)
    assert r.status_code == 201, r.text


def test_create_goal_response_fields(auth):
    r = auth.post("/api/health/goals", json=GOAL)
    data = r.json()
    assert data["domain"] == "cardiovascular"
    assert data["status"] == "active"
    assert "id" in data


def test_create_goal_all_domains(auth):
    for domain in ["cardiovascular", "metabolic", "neurological", "cancer_prevention", "general"]:
        r = auth.post("/api/health/goals", json={
            "domain": domain,
            "goal_text": f"Test goal for {domain}",
        })
        assert r.status_code == 201, f"{domain} failed: {r.text}"


def test_create_goal_minimal(auth):
    """Only domain and goal_text required."""
    r = auth.post("/api/health/goals", json={
        "domain": "general",
        "goal_text": "Exercise more",
    })
    assert r.status_code == 201, r.text


def test_create_goal_missing_domain(auth):
    r = auth.post("/api/health/goals", json={"goal_text": "No domain"})
    assert r.status_code == 422


def test_create_goal_missing_text(auth):
    r = auth.post("/api/health/goals", json={"domain": "general"})
    assert r.status_code == 422


def test_create_goal_invalid_domain(auth):
    r = auth.post("/api/health/goals", json={
        "domain": "not_a_domain",
        "goal_text": "Invalid domain",
    })
    assert r.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_goals_returns_200(auth):
    r = auth.get("/api/health/goals")
    assert r.status_code == 200


def test_list_goals_is_list(auth):
    r = auth.get("/api/health/goals")
    assert isinstance(r.json(), list)


def test_list_goals_contains_created(auth):
    r = auth.get("/api/health/goals")
    domains = [g["domain"] for g in r.json()]
    assert "cardiovascular" in domains


def test_goals_unauthenticated():
    with httpx.Client(base_url=API_BASE, timeout=TIMEOUT) as c:
        r = c.get("/api/health/goals")
        assert r.status_code == 401
