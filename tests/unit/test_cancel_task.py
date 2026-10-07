from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.services.agent_service import AgentService


class TestCancelTask:
    @pytest.mark.asyncio
    async def test_cancel_records_reason_without_losing_cancelled_status(
        self,
    ) -> None:
        """Cancelling with a reason must not let the reason-storing write
        clobber the 'cancelled' status back to something else (e.g. the
        generic save_error helper always sets status='failed')."""
        task = SimpleNamespace(task_id="t1", status="running")
        service = AgentService()

        with patch(
            "src.services.agent_service.task_service.get_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status",
            AsyncMock(),
        ) as update_status:
            result = await service.cancel("t1", reason="user requested")

        assert result is True
        update_status.assert_awaited_once_with(
            "t1", "cancelled", error="Cancelled: user requested"
        )

    @pytest.mark.asyncio
    async def test_cancel_without_reason_does_not_touch_error_field(self) -> None:
        task = SimpleNamespace(task_id="t2", status="pending")
        service = AgentService()

        with patch(
            "src.services.agent_service.task_service.get_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status",
            AsyncMock(),
        ) as update_status:
            result = await service.cancel("t2")

        assert result is True
        update_status.assert_awaited_once_with("t2", "cancelled", error=None)

    @pytest.mark.asyncio
    async def test_cancel_returns_false_for_already_finished_task(self) -> None:
        task = SimpleNamespace(task_id="t3", status="completed")
        service = AgentService()

        with patch(
            "src.services.agent_service.task_service.get_task",
            AsyncMock(return_value=task),
        ):
            result = await service.cancel("t3", reason="too late")

        assert result is False
