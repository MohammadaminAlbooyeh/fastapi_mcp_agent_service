from __future__ import annotations

import pytest

from src.mcp_tools.calculator_tool import CalculatorTool
from src.mcp_tools.database_tool import DatabaseTool
from src.mcp_tools.file_tool import FileTool
from src.mcp_tools.search_tool import SearchTool
from src.mcp_tools.tools_registry import ToolsRegistry


class TestToolsRegistry:
    def setup_method(self) -> None:
        self.registry = ToolsRegistry()

    def test_register_tool(self) -> None:
        tool = CalculatorTool()
        self.registry.register(tool)
        assert self.registry.get("calculator_tool") == tool

    def test_list_tools(self) -> None:
        tools = self.registry.list_tools()
        assert len(tools) > 0

    def test_get_nonexistent_tool(self) -> None:
        with pytest.raises(KeyError):
            self.registry.get("nonexistent_tool")


class TestCalculatorTool:
    def setup_method(self) -> None:
        self.tool = CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculation(self) -> None:
        ...

    def test_tool_name(self) -> None:
        assert self.tool.name == "calculator_tool"
