from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_tools.api_tool import APITool
from src.mcp_tools.calculator_tool import CalculatorTool
from src.mcp_tools.database_tool import DatabaseTool
from src.mcp_tools.file_tool import FileTool
from src.mcp_tools.search_tool import SearchTool
from src.mcp_tools.tools_registry import ToolsRegistry


@pytest.fixture
def registry() -> ToolsRegistry:
    return ToolsRegistry()


class TestMCPIntegration:
    def test_all_tools_registered(self, registry: ToolsRegistry) -> None:
        names = registry.get_tool_names()
        assert "calculator_tool" in names
        assert "database_tool" in names
        assert "file_tool" in names
        assert "search_tool" in names
        assert "api_tool" in names

    def test_tool_types(self, registry: ToolsRegistry) -> None:
        assert isinstance(registry.get("calculator_tool"), CalculatorTool)
        assert isinstance(registry.get("database_tool"), DatabaseTool)
        assert isinstance(registry.get("file_tool"), FileTool)
        assert isinstance(registry.get("search_tool"), SearchTool)
        assert isinstance(registry.get("api_tool"), APITool)

    @pytest.mark.asyncio
    async def test_calculator_execution(self, registry: ToolsRegistry) -> None:
        tool = registry.get("calculator_tool")
        result = await tool.execute(expression="2 * 3 + 1")
        assert result["result"] == 7.0

    @pytest.mark.asyncio
    async def test_unknown_tool_raises(self, registry: ToolsRegistry) -> None:
        with pytest.raises(KeyError):
            registry.get("unknown_tool")

    def test_tool_to_dict(self, registry: ToolsRegistry) -> None:
        tool_dicts = registry.list_tools()
        for t in tool_dicts:
            assert "name" in t
            assert "description" in t

    def test_register_custom_tool(self, registry: ToolsRegistry) -> None:
        class CustomTool:
            name = "custom_tool"
            description = "A custom test tool"

        registry.register(CustomTool())  # type: ignore
        assert registry.get("custom_tool") is not None

    @pytest.mark.asyncio
    async def test_api_tool_execute_http_request(self) -> None:
        tool = APITool()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"ok": true}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await tool.execute(
                action="http_request",
                method="GET",
                url="https://api.example.com",
            )
            assert result["tool"] == "api_tool"
            assert result["action"] == "http_request"
            assert result["result"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_file_tool_write_and_read(self, tmp_path) -> None:
        tool = FileTool()
        tool.ALLOWED_BASE = tmp_path

        result = await tool.execute(action="write", path="test.txt", content="hello world")
        assert result["result"] is True

        result = await tool.execute(action="read", path="test.txt")
        assert result["result"] == "hello world"

        result = await tool.execute(action="list", directory=".")
        assert len(result["result"]) > 0

        result = await tool.execute(action="delete", path="test.txt")
        assert result["result"] is True
