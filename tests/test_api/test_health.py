from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    # Patch Telegram bot setup to avoid needing a real token
    with patch("app.telegram.bot.setup_bot", new_callable=AsyncMock):
        with patch("app.telegram.bot.shutdown_bot", new_callable=AsyncMock):
            from app.main import app

            with TestClient(app) as c:
                yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "sofia"
