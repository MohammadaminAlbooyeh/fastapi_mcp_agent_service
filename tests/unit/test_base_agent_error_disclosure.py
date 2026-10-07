from __future__ import annotations

import pytest
from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.config.settings import settings


class _FailingAgent(BaseAgent):
    name = "failing"

    def build_graph(self) -> StateGraph:
        async def boom(state):
            raise RuntimeError(
                "connection to postgresql://admin:s3cr3t@10.0.0.5/prod failed"
            )

        graph = StateGraph(dict)
        graph.add_node("boom", boom)
        graph.add_edge(START, "boom")
        graph.add_edge("boom", END)
        return graph


class TestBaseAgentErrorDisclosure:
    @pytest.mark.asyncio
    async def test_hides_raw_exception_message_outside_debug(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "debug", False)
        agent = _FailingAgent()

        result = await agent.execute("do something")

        assert result["status"] == "failed"
        assert result["error"] == "Agent execution failed"

    @pytest.mark.asyncio
    async def test_shows_exception_message_in_debug(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "debug", True)
        agent = _FailingAgent()

        result = await agent.execute("do something")

        assert result["status"] == "failed"
        assert "s3cr3t" in result["error"]
