from __future__ import annotations

from typing import Any, Dict

from src.agents.base_agent import BaseAgent


class ResearchAgent(BaseAgent):
    name: str = "research"
    description: str = "For information gathering and research"
    tools: list[str] = ["search_tool", "api_tool"]

    async def execute(
        self, query: str, **kwargs: Any
    ) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "query": query,
            "status": "executed",
        }
