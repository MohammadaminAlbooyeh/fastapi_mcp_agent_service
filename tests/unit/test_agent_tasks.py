from __future__ import annotations

from unittest.mock import AsyncMock, patch

from src.tasks.agent_tasks import execute_agent_task


class TestExecuteAgentTask:
    def test_completes_successfully(self) -> None:
        with patch(
            "src.tasks.agent_tasks.task_service.update_task_status", AsyncMock()
        ), patch("src.tasks.agent_tasks.task_service.save_result", AsyncMock()), patch(
            "src.agents.orchestrator.orchestrator.execute",
            AsyncMock(return_value={"status": "completed"}),
        ):
            result = execute_agent_task.run(
                task_id="t1", query="hello", agent_type="query"
            )

        assert result["status"] == "completed"
        assert result["task_id"] == "t1"

    def test_does_not_retry_on_unknown_agent_type(self) -> None:
        """A bad agent_type is a deterministic failure (KeyError from the
        orchestrator) — it will fail identically every time, so it must be
        reported immediately rather than burning through Celery retries."""
        with patch(
            "src.tasks.agent_tasks.task_service.update_task_status", AsyncMock()
        ), patch(
            "src.tasks.agent_tasks.task_service.save_error", AsyncMock()
        ) as save_error, patch(
            "src.agents.orchestrator.orchestrator.execute",
            AsyncMock(side_effect=KeyError("Unknown agent type: bogus")),
        ):
            result = execute_agent_task.run(
                task_id="t2", query="hello", agent_type="bogus"
            )

        assert result["status"] == "failed"
        save_error.assert_awaited_once()

    def test_retries_on_transient_error(self) -> None:
        with patch(
            "src.tasks.agent_tasks.task_service.update_task_status", AsyncMock()
        ), patch("src.tasks.agent_tasks.task_service.save_error", AsyncMock()), patch(
            "src.agents.orchestrator.orchestrator.execute",
            AsyncMock(side_effect=ConnectionError("db unreachable")),
        ), patch.object(
            execute_agent_task, "retry", side_effect=RuntimeError("retry scheduled")
        ) as mock_retry:
            try:
                execute_agent_task.run(task_id="t3", query="hello", agent_type="query")
            except RuntimeError:
                pass

        mock_retry.assert_called_once()
