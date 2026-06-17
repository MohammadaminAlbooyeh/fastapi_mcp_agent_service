from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Optional

from src.agents.orchestrator import orchestrator


class AgentService:
    async def execute(
        self,
        query: str,
        agent_type: str,
        tools: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return await orchestrator.execute(
            query=query,
            agent_type=agent_type,
            tools=tools,
            **kwargs,
        )

    async def stream(
        self,
        query: str,
        agent_type: str,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        yield f"Starting {agent_type} agent...\n"
        yield f"Processing query: {query}\n"
        yield "Done.\n"

    async def cancel(self, task_id: str) -> bool:
        return True


agent_service = AgentService()
