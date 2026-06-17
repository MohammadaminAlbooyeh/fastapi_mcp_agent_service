from __future__ import annotations

from typing import Any, Dict, List

from src.mcp_tools.api_tool import APITool
from src.mcp_tools.base import BaseTool
from src.mcp_tools.calculator_tool import CalculatorTool
from src.mcp_tools.database_tool import DatabaseTool
from src.mcp_tools.file_tool import FileTool
from src.mcp_tools.search_tool import SearchTool


class ToolsRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self) -> None:
        self.register(DatabaseTool())
        self.register(FileTool())
        self.register(SearchTool())
        self.register(APITool())
        self.register(CalculatorTool())

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"Tool '{name}' not found")
        return tool

    def list_tools(self) -> List[Dict[str, Any]]:
        return [t.to_dict() for t in self._tools.values()]

    def get_tool_names(self) -> List[str]:
        return list(self._tools.keys())


tools_registry = ToolsRegistry()
