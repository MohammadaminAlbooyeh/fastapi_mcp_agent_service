from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from fastapi.responses import JSONResponse

from src.api.exceptions import (
    AgentException,
    AgentExecutionException,
    ToolNotFoundException,
    agent_exception_handler,
)


class TestExceptions:
    def test_agent_exception_default_status(self) -> None:
        exc = AgentException("Something went wrong")
        assert exc.message == "Something went wrong"
        assert exc.status_code == 400

    def test_agent_exception_custom_status(self) -> None:
        exc = AgentException("Not found", status_code=404)
        assert exc.status_code == 404

    def test_tool_not_found_exception(self) -> None:
        exc = ToolNotFoundException("my_tool")
        assert "my_tool" in exc.message
        assert exc.status_code == 404

    def test_agent_execution_exception(self) -> None:
        exc = AgentExecutionException("Execution failed")
        assert exc.status_code == 500
        assert "Execution failed" in exc.message

    @pytest.mark.asyncio
    async def test_agent_exception_handler(self) -> None:
        request = MagicMock(spec=Request)
        exc = AgentException("Test error", status_code=400)
        response = await agent_exception_handler(request, exc)
        assert isinstance(response, JSONResponse)
        assert response.status_code == 400
