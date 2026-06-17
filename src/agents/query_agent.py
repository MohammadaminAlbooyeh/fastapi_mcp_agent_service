from __future__ import annotations

from typing import Any, Dict

from src.agents.base_agent import BaseAgent


class QueryAgent(BaseAgent):
    name: str = "query"
    description: str = "Specialized for executing database queries"
    tools: list[str] = ["database_tool", "cache_service"]

    async def execute(
        self, query: str, **kwargs: Any
    ) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "query": query,
            "status": "executed",
        }
