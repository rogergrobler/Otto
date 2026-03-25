import uuid
from unittest.mock import AsyncMock

import pytest

from app.config import Settings


@pytest.fixture
def mock_settings(monkeypatch):
    """Override settings for testing."""
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///test.db")
    monkeypatch.setenv("LLM_PROVIDER", "claude")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret")


@pytest.fixture
def mock_llm():
    """Mock LLM provider."""
    llm = AsyncMock()
    llm.chat.return_value = "This is a test response from Otto."
    llm.embed.return_value = [[0.1] * 1536]
    return llm


@pytest.fixture
def sample_client_id():
    return uuid.uuid4()
