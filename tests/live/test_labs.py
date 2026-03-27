"""
Lab results endpoint tests.
"""
import uuid
from datetime import date

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
        "password": "Labs99!",
        "full_name": "Labs Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


LAB_PAYLOAD = {
    "marker_name": "ApoB",
    "value": 0.82,
    "unit": "g/L",
    "flag": "normal",
    "test_date": str(date.today()),
    "lab_name": "Test Lab",
}


# ── Create ────────────────────────────────────────────────────────────────────

def test_create_lab_returns_201(auth):
    r = auth.post("/api/health/labs", json=LAB_PAYLOAD)
    assert r.status_code == 201, r.text


def test_create_lab_response_fields(auth):
    r = auth.post("/api/health/labs", json=LAB_PAYLOAD)
    data = r.json()
    assert data["marker_name"] == "ApoB"
    assert data["value"] == 0.82
    assert data["unit"] == "g/L"
    assert "id" in data


def test_create_multiple_markers(auth):
    markers = [
        {"marker_name": "LDL", "value": 2.8, "unit": "mmol/L",
         "flag": "normal", "test_date": str(date.today())},
        {"marker_name": "HDL", "value": 1.6, "unit": "mmol/L",
         "flag": "optimal", "test_date": str(date.today())},
        {"marker_name": "HbA1c", "value": 5.4, "unit": "%",
         "flag": "optimal", "test_date": str(date.today())},
    ]
    for m in markers:
        r = auth.post("/api/health/labs", json=m)
        assert r.status_code == 201, f"Failed to create {m['marker_name']}: {r.text}"


def test_create_lab_minimal_fields(auth):
    """Only required fields — no flag, lab_name, reference range."""
    r = auth.post("/api/health/labs", json={
        "marker_name": "hsCRP",
        "value": 0.8,
        "unit": "mg/L",
        "test_date": str(date.today()),
    })
    assert r.status_code == 201, r.text


def test_create_lab_missing_marker_name(auth):
    r = auth.post("/api/health/labs", json={
        "value": 1.0, "unit": "mmol/L", "test_date": str(date.today()),
    })
    assert r.status_code == 422


def test_create_lab_missing_value(auth):
    r = auth.post("/api/health/labs", json={
        "marker_name": "X", "unit": "mmol/L", "test_date": str(date.today()),
    })
    assert r.status_code == 422


def test_create_lab_missing_test_date(auth):
    r = auth.post("/api/health/labs", json={
        "marker_name": "X", "value": 1.0, "unit": "mmol/L",
    })
    assert r.status_code == 422


# ── List ──────────────────────────────────────────────────────────────────────

def test_list_labs_returns_200(auth):
    r = auth.get("/api/health/labs")
    assert r.status_code == 200


def test_list_labs_is_list(auth):
    r = auth.get("/api/health/labs")
    assert isinstance(r.json(), list)


def test_list_labs_contains_created(auth):
    r = auth.get("/api/health/labs")
    names = [l["marker_name"] for l in r.json()]
    assert "ApoB" in names


def test_list_labs_filter_by_marker(auth):
    r = auth.get("/api/health/labs?marker_name=ApoB")
    assert r.status_code == 200
    data = r.json()
    assert all("apob" in l["marker_name"].lower() for l in data)


def test_list_labs_filter_no_match(auth):
    r = auth.get("/api/health/labs?marker_name=ZZZNonExistent")
    assert r.status_code == 200
    assert r.json() == []


# ── Delete ────────────────────────────────────────────────────────────────────

def test_delete_lab(auth):
    create = auth.post("/api/health/labs", json={
        "marker_name": "ToDelete",
        "value": 1.0,
        "unit": "mmol/L",
        "test_date": str(date.today()),
    })
    assert create.status_code == 201
    lab_id = create.json()["id"]

    delete = auth.delete(f"/api/health/labs/{lab_id}")
    assert delete.status_code == 204

    labs = auth.get("/api/health/labs")
    ids = [l["id"] for l in labs.json()]
    assert lab_id not in ids


def test_delete_nonexistent_lab(auth):
    r = auth.delete(f"/api/health/labs/{uuid.uuid4()}")
    assert r.status_code == 404


def test_labs_unauthenticated(http):
    r = http.get("/api/health/labs")
    assert r.status_code == 401
