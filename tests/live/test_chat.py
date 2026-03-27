"""
Chat endpoint tests.
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
        "password": "Chat99!",
        "full_name": "Chat Test",
    })
    assert r.status_code == 201
    http.headers.update({"Authorization": f"Bearer {r.json()['access_token']}"})
    return http


# ── Send message ──────────────────────────────────────────────────────────────

def test_chat_returns_200(auth):
    r = auth.post("/api/chat", json={"message": "Hello"}, timeout=60)
    assert r.status_code == 200, r.text


def test_chat_has_reply(auth):
    r = auth.post("/api/chat", json={"message": "What is my health score?"}, timeout=60)
    assert r.status_code == 200
    data = r.json()
    # Backend returns either 'reply' or nested 'message' field
    reply = data.get("reply") or data.get("message")
    assert reply, f"No reply in response: {data}"
    assert len(reply) > 0


def test_chat_response_is_string(auth):
    r = auth.post("/api/chat", json={"message": "Hi"}, timeout=60)
    assert r.status_code == 200
    data = r.json()
    reply = data.get("reply") or data.get("message", "")
    assert isinstance(reply, str)


def test_chat_health_question(auth):
    r = auth.post("/api/chat",
                  json={"message": "Can you summarise my health data?"},
                  timeout=60)
    assert r.status_code == 200


def test_chat_missing_message(auth):
    r = auth.post("/api/chat", json={}, timeout=30)
    assert r.status_code == 422


def test_chat_unauthenticated(http):
    r = http.post("/api/chat", json={"message": "Hello"}, timeout=30)
    assert r.status_code == 401
