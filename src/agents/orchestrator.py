from __future__ import annotations

from typing import Any, Dict, Optional

from src.agents.base_agent import BaseAgent
from src.agents.data_processor_agent import DataProcessorAgent
from src.agents.query_agent import QueryAgent
from src.agents.research_agent import ResearchAgent


class Orchestrator:
    def __init__(self) -> None:
        self._agents: Dict[str, BaseAgent] = {
            "query": QueryAgent(),
            "processor": DataProcessorAgent(),
            "research": ResearchAgent(),
        }

    def get_agent(self, agent_type: str) -> BaseAgent:
        agent = self._agents.get(agent_type)
        if not agent:
            raise KeyError(f"Unknown agent type: {agent_type}")
        return agent

    async def execute(
        self,
        query: str,
        agent_type: str,
        tools: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        agent = self.get_agent(agent_type)
        return await agent.execute(query, tools=tools, **kwargs)


orchestrator = Orchestrator()
