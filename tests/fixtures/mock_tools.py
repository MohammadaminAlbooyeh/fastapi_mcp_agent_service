from __future__ import annotations

from typing import Any, Dict


class MockDatabaseTool:
    name: str = "database_tool"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return {"tool": self.name, "result": "mock_result"}


class MockSearchTool:
    name: str = "search_tool"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        return {"tool": self.name, "result": ["mock_result_1", "mock_result_2"]}
