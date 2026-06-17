from __future__ import annotations

from typing import Any, Dict

from src.agents.base_agent import BaseAgent


class DataProcessorAgent(BaseAgent):
    name: str = "processor"
    description: str = "For data transformation and analysis"
    tools: list[str] = ["file_tool", "calculator_tool"]

    async def execute(
        self, query: str, **kwargs: Any
    ) -> Dict[str, Any]:
        return {
            "agent": self.name,
            "query": query,
            "status": "executed",
        }
