from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pytest import MonkeyPatch

from src.database.models import TaskRecord
from src.models.schemas import Task
from src.services.cache_service import CacheService
from src.services.notification_service import NotificationService
from src.services.task_service import TaskService


@pytest.fixture
def mock_db() -> MagicMock:
    return MagicMock()


@pytest.fixture
def sample_task_record() -> TaskRecord:
    return TaskRecord(
        task_id="test-task-001",
        query="test query",
        agent_type="query",
        tools=["database_tool"],
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


class _MockCRUD:
    def __init__(self, db):
        self.db = db

    def create_task(self, query, agent_type, tools=None):
        return MagicMock(
            task_id="new-task-id",
            query=query,
            agent_type=agent_type,
            tools=tools or [],
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def get_task(self, task_id):
        if task_id == "nonexistent":
            return None
        return MagicMock(
            task_id=task_id,
            query="test",
            agent_type="query",
            tools=[],
            status="completed" if task_id != "not-found" else "pending",
            result={"data": "test"},
            error=None,
            execution_time=1.5,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def update_task(self, task_id, updates):
        return MagicMock(
            task_id=task_id,
            query="test",
            agent_type="query",
            tools=[],
            status=updates.get("status", "pending"),
            result=updates.get("result"),
            error=updates.get("error"),
            execution_time=updates.get("execution_time", 0.0),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )

    def list_tasks(self, filters=None):
        return [
            MagicMock(
                task_id="task-1",
                query="test",
                agent_type="query",
                tools=[],
                status="completed",
                result=None,
                error=None,
                execution_time=1.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        ]


class TestTaskService:
    def setup_method(self) -> None:
        self.service = TaskService()

    @pytest.mark.asyncio
    async def test_create_task(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr(
            "src.services.task_service.CRUD",
            _MockCRUD,
        )
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.create_task("test query", "query", ["database_tool"])
        assert task.task_id == "new-task-id"
        assert task.query == "test query"
        assert task.agent_type == "query"
        assert task.tools == ["database_tool"]

    @pytest.mark.asyncio
    async def test_get_task_found(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.get_task("test-id")
        assert task is not None
        assert task.task_id == "test-id"
        assert task.status == "completed"

    @pytest.mark.asyncio
    async def test_get_task_not_found(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.get_task("nonexistent")
        assert task is None

    @pytest.mark.asyncio
    async def test_update_task_status(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.update_task_status("test-id", "running")
        assert task is not None
        assert task.status == "running"

    @pytest.mark.asyncio
    async def test_save_result(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.save_result("test-id", {"answer": 42}, 2.5)
        assert task is not None
        assert task.status == "completed"
        assert task.execution_time == 2.5

    @pytest.mark.asyncio
    async def test_save_error(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        task = await self.service.save_error("test-id", "something went wrong")
        assert task is not None
        assert task.status == "failed"
        assert task.error == "something went wrong"

    @pytest.mark.asyncio
    async def test_retrieve_task_history(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.task_service.CRUD", _MockCRUD)
        monkeypatch.setattr("src.services.task_service.SessionLocal", MagicMock)

        tasks = await self.service.retrieve_task_history({"status": "completed"})
        assert len(tasks) == 1
        assert tasks[0].task_id == "task-1"


class TestCacheService:
    def setup_method(self) -> None:
        self.service = CacheService()

    @pytest.mark.asyncio
    async def test_cache_and_get(self, monkeypatch: MonkeyPatch) -> None:
        mock_redis = AsyncMock()
        mock_redis.setex.return_value = True
        mock_redis.get.return_value = '{"answer": 42}'
        monkeypatch.setattr(self.service, "_get_client", AsyncMock(return_value=mock_redis))

        cached = await self.service.cache_result("test-key", {"answer": 42})
        assert cached is True

        result = await self.service.get_cached("test-key")
        assert result == {"answer": 42}

    @pytest.mark.asyncio
    async def test_cache_fallback_to_local(self, monkeypatch: MonkeyPatch) -> None:
        mock_redis = AsyncMock()
        mock_redis.setex.side_effect = Exception("Redis down")
        monkeypatch.setattr(self.service, "_get_client", AsyncMock(return_value=mock_redis))

        cached = await self.service.cache_result("local-key", "local-value")
        assert cached is True
        assert self.service._local.get("local-key") == "local-value"

    @pytest.mark.asyncio
    async def test_get_cached_miss(self, monkeypatch: MonkeyPatch) -> None:
        mock_redis = AsyncMock()
        mock_redis.get.return_value = None
        monkeypatch.setattr(self.service, "_get_client", AsyncMock(return_value=mock_redis))

        result = await self.service.get_cached("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_invalidate_cache(self, monkeypatch: MonkeyPatch) -> None:
        mock_redis = AsyncMock()
        mock_redis.scan.return_value = (0, ["key1", "key2"])
        mock_redis.delete.return_value = 2
        monkeypatch.setattr(self.service, "_get_client", AsyncMock(return_value=mock_redis))

        result = await self.service.invalidate_cache("prefix:*")
        assert result is True

    @pytest.mark.asyncio
    async def test_close(self, monkeypatch: MonkeyPatch) -> None:
        mock_redis = AsyncMock()
        self.service._client = mock_redis
        await self.service.close()
        mock_redis.close.assert_awaited_once()
        assert self.service._client is None


class TestNotificationService:
    def setup_method(self) -> None:
        self.service = NotificationService()

    @pytest.mark.asyncio
    async def test_send_event_no_webhook(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.notification_service.settings.webhook_url", "")
        result = await self.service.send_event("test.event", {"key": "value"})
        assert result is True

    @pytest.mark.asyncio
    async def test_send_event_success(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.notification_service.settings.webhook_url", "https://example.com/hook")
        mock_post = AsyncMock()
        mock_post.return_value.raise_for_status.return_value = None
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        result = await self.service.send_event("test.event", {"key": "value"})
        assert result is True

    @pytest.mark.asyncio
    async def test_send_event_failure(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.notification_service.settings.webhook_url", "https://example.com/hook")
        mock_post = AsyncMock(side_effect=Exception("Network error"))
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        result = await self.service.send_event("test.event", {"key": "value"})
        assert result is False

    @pytest.mark.asyncio
    async def test_notify_task_completed(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.notification_service.settings.webhook_url", "https://example.com/hook")
        mock_post = AsyncMock()
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        result = await self.service.notify_task_completed("task-123", {"answer": 42})
        assert result is True

    @pytest.mark.asyncio
    async def test_notify_task_failed(self, monkeypatch: MonkeyPatch) -> None:
        monkeypatch.setattr("src.services.notification_service.settings.webhook_url", "https://example.com/hook")
        mock_post = AsyncMock()
        monkeypatch.setattr("httpx.AsyncClient.post", mock_post)

        result = await self.service.notify_task_failed("task-123", "error message")
        assert result is True
