from __future__ import annotations

from typing import Any, Dict, List

from src.mcp_tools.base import BaseTool


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = "Web search and semantic search operations"

    async def web_search(self, query: str) -> List[Dict[str, Any]]:
        ...

    async def semantic_search(
        self, query: str, index: str
    ) -> List[Dict[str, Any]]:
        ...

    async def similarity_search(
        self, text: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        ...

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        if action == "web_search":
            result = await self.web_search(kwargs.get("query", ""))
        elif action == "semantic_search":
            result = await self.semantic_search(
                kwargs.get("query", ""), kwargs.get("index", "")
            )
        elif action == "similarity_search":
            result = await self.similarity_search(
                kwargs.get("text", ""), kwargs.get("top_k", 5)
            )
        else:
            result = {"error": f"Unknown action: {action}"}
        return {"tool": self.name, "action": action, "result": result}
