from __future__ import annotations

import pytest

from src.agents.data_processor_agent import DataProcessorAgent
from src.agents.orchestrator import Orchestrator
from src.agents.query_agent import QueryAgent
from src.agents.research_agent import ResearchAgent


class TestAgents:
    def setup_method(self) -> None:
        self.orchestrator = Orchestrator()

    def test_query_agent_creation(self) -> None:
        agent = QueryAgent()
        assert agent.name == "query"
        assert "database_tool" in agent.tools

    def test_processor_agent_creation(self) -> None:
        agent = DataProcessorAgent()
        assert agent.name == "processor"

    def test_research_agent_creation(self) -> None:
        agent = ResearchAgent()
        assert agent.name == "research"

    def test_orchestrator_get_agent(self) -> None:
        agent = self.orchestrator.get_agent("query")
        assert isinstance(agent, QueryAgent)

    def test_orchestrator_invalid_agent(self) -> None:
        with pytest.raises(KeyError):
            self.orchestrator.get_agent("invalid")
