from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from src.api.exceptions import TokenBudgetExceededError
from src.config.settings import settings
from src.services.agent_service import AgentService


class TestAgentServiceTimeout:
    @pytest.mark.asyncio
    async def test_execute_times_out_on_a_hanging_tool_call(self) -> None:
        """A stuck external call (slow API, hung LLM stream, etc.) must not be
        able to tie up a request forever just because the caller's requested
        `timeout` previously had no effect anywhere in the pipeline."""

        async def hang_forever(*args, **kwargs):
            await asyncio.sleep(10)
            return {"result": "should never get here"}

        task = SimpleNamespace(task_id="task-timeout-1")

        with patch(
            "src.services.agent_service.task_service.create_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.services.agent_service.task_service.save_error", AsyncMock()
        ) as save_error, patch(
            "src.services.agent_service.notification_service.notify_task_failed",
            AsyncMock(),
        ), patch(
            "src.services.agent_service.orchestrator.execute",
            AsyncMock(side_effect=hang_forever),
        ):
            service = AgentService()
            result = await service.execute(
                query="do something slow",
                agent_type="query",
                timeout=0.05,
            )

        assert result["status"] == "timeout"
        assert "timed out" in result["error"]
        save_error.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_hides_raw_error_outside_debug(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "debug", False)
        task = SimpleNamespace(task_id="task-timeout-3")

        with patch(
            "src.services.agent_service.task_service.create_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.services.agent_service.task_service.save_error", AsyncMock()
        ), patch(
            "src.services.agent_service.notification_service.notify_task_failed",
            AsyncMock(),
        ), patch(
            "src.services.agent_service.orchestrator.execute",
            AsyncMock(
                side_effect=RuntimeError(
                    "connection to postgresql://admin:s3cr3t@10.0.0.5/prod failed"
                )
            ),
        ):
            service = AgentService()
            result = await service.execute(query="do something", agent_type="query")

        assert result["status"] == "failed"
        assert result["error"] == "Agent execution failed"
        assert "s3cr3t" not in result["error"]

    @pytest.mark.asyncio
    async def test_execute_stops_mid_run_when_cancellation_flag_flips(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """cancel() only flips a DB flag — a still-running execute() must
        actually observe it and stop, not just let the run finish to
        completion regardless."""
        monkeypatch.setattr(
            "src.services.agent_service.CANCELLATION_POLL_INTERVAL", 0.01
        )

        async def hang_forever(*args, **kwargs):
            await asyncio.sleep(10)

        task = SimpleNamespace(task_id="task-cancel-1")
        cancelled_task = SimpleNamespace(task_id="task-cancel-1", cancel_requested=True)

        with patch(
            "src.services.agent_service.task_service.create_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.services.agent_service.task_service.get_task",
            AsyncMock(return_value=cancelled_task),
        ), patch(
            "src.services.agent_service.task_service.save_error", AsyncMock()
        ) as save_error, patch(
            "src.services.agent_service.notification_service.notify_task_failed",
            AsyncMock(),
        ), patch(
            "src.services.agent_service.orchestrator.execute",
            AsyncMock(side_effect=hang_forever),
        ):
            service = AgentService()
            result = await service.execute(query="slow", agent_type="query", timeout=5)

        assert result["status"] == "cancelled"
        save_error.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_execute_reports_budget_exceeded_without_generic_500(self) -> None:
        task = SimpleNamespace(task_id="task-budget-1")

        with patch(
            "src.services.agent_service.task_service.create_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.services.agent_service.task_service.save_error", AsyncMock()
        ), patch(
            "src.services.agent_service.notification_service.notify_task_failed",
            AsyncMock(),
        ), patch(
            "src.services.agent_service.orchestrator.execute",
            AsyncMock(
                side_effect=TokenBudgetExceededError("Request would use ~20000 tokens")
            ),
        ):
            service = AgentService()
            result = await service.execute(query="huge prompt", agent_type="query")

        assert result["status"] == "budget_exceeded"
        assert "tokens" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_completes_normally_within_timeout(self) -> None:
        task = SimpleNamespace(task_id="task-timeout-2")

        with patch(
            "src.services.agent_service.task_service.create_task",
            AsyncMock(return_value=task),
        ), patch(
            "src.services.agent_service.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.services.agent_service.task_service.save_result", AsyncMock()
        ), patch(
            "src.services.agent_service.notification_service.notify_task_completed",
            AsyncMock(),
        ), patch(
            "src.services.agent_service.orchestrator.execute",
            AsyncMock(return_value={"result": "ok"}),
        ):
            service = AgentService()
            result = await service.execute(query="quick", agent_type="query", timeout=5)

        assert result["status"] == "completed"
        assert result["result"] == {"result": "ok"}
