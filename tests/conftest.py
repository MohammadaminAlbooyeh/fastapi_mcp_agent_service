from __future__ import annotations

from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def sample_query() -> str:
    return "Get all users from database where age > 25"


@pytest.fixture
def auth_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test-token"}


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch) -> None:
    monkeypatch.setattr("src.api.auth.settings.environment", "development")


@pytest.fixture
def sample_task_result() -> Dict[str, Any]:
    return {
        "task_id": "test-task-001",
        "query": "test query",
        "agent_type": "query",
        "status": "completed",
        "result": {"answer": 42},
        "execution_time": 1.5,
    }
