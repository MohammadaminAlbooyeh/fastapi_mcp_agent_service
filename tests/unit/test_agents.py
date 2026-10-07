from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


def _llm_generate_by_prompt(responses: dict[str, str]):
    """llm_service.generate is a single shared singleton used by both the
    agent's own analyze/routing step and BaseAgent's final `respond` step, so
    tests must use one mock with a routing side_effect keyed by prompt
    content — patching it under two different import paths just reassigns
    the same underlying attribute twice and silently drops the first mock."""

    async def _generate(prompt: str, system_prompt: str | None = None) -> str:
        for marker, response in responses.items():
            if marker in prompt:
                return response
        return "default response"

    return AsyncMock(side_effect=_generate)


class TestQueryAgentExecution:
    @pytest.mark.asyncio
    async def test_generates_sql_via_llm_and_executes_it(self) -> None:
        agent = QueryAgent()
        mock_tool = AsyncMock()
        mock_tool.execute.return_value = {"result": [{"id": 1}]}

        mock_generate = _llm_generate_by_prompt(
            {
                "Convert the following request": "```sql\nSELECT * FROM tasks\n```",
                "Tool results": "Here are the results",
            }
        )
        with patch(
            "src.services.llm_service.llm_service.generate", mock_generate
        ), patch("src.agents.query_agent.tools_registry.get", return_value=mock_tool):
            result = await agent.execute("show me all tasks")

        assert result["status"] == "completed"
        mock_tool.execute.assert_awaited_once_with(
            action="query", sql="SELECT * FROM tasks"
        )


class TestDataProcessorAgentExecution:
    @pytest.mark.asyncio
    async def test_routes_to_calculator_for_math_requests(self) -> None:
        agent = DataProcessorAgent()
        mock_calc = AsyncMock()
        mock_calc.execute.return_value = {"result": 7.0}

        def get_tool(name: str):
            assert name == "calculator_tool"
            return mock_calc

        mock_generate = _llm_generate_by_prompt(
            {
                "Classify the following request": '{"intent": "calculation", "expression": "2 + 5"}',
                "Tool results": "The answer is 7",
            }
        )
        with patch(
            "src.services.llm_service.llm_service.generate", mock_generate
        ), patch(
            "src.agents.data_processor_agent.tools_registry.get", side_effect=get_tool
        ):
            result = await agent.execute("what is 2 plus 5?")

        assert result["status"] == "completed"
        mock_calc.execute.assert_awaited_once_with(expression="2 + 5")

    @pytest.mark.asyncio
    async def test_routes_to_file_tool_for_file_requests(self) -> None:
        agent = DataProcessorAgent()
        mock_file_tool = AsyncMock()
        mock_file_tool.execute.return_value = {"result": "file contents"}

        def get_tool(name: str):
            assert name == "file_tool"
            return mock_file_tool

        plan = (
            '{"intent": "file_operation", "file_action": "read", "path": "notes.txt"}'
        )
        mock_generate = _llm_generate_by_prompt(
            {
                "Classify the following request": plan,
                "Tool results": "Here is the file",
            }
        )
        with patch(
            "src.services.llm_service.llm_service.generate", mock_generate
        ), patch(
            "src.agents.data_processor_agent.tools_registry.get", side_effect=get_tool
        ):
            result = await agent.execute("read notes.txt")

        assert result["status"] == "completed"
        mock_file_tool.execute.assert_awaited_once_with(
            action="read", path="notes.txt", directory="notes.txt", content=""
        )

    @pytest.mark.asyncio
    async def test_falls_back_to_calculation_on_unparseable_llm_output(self) -> None:
        agent = DataProcessorAgent()
        mock_calc = AsyncMock()
        mock_calc.execute.return_value = {"error": "Unsupported expression"}

        mock_generate = _llm_generate_by_prompt(
            {
                "Classify the following request": "not valid json at all",
                "Tool results": "I couldn't process that",
            }
        )
        with patch(
            "src.services.llm_service.llm_service.generate", mock_generate
        ), patch(
            "src.agents.data_processor_agent.tools_registry.get",
            return_value=mock_calc,
        ):
            result = await agent.execute("do something ambiguous")

        assert result["status"] == "completed"
        mock_calc.execute.assert_awaited_once_with(expression="")


class TestResearchAgentExecution:
    @pytest.mark.asyncio
    async def test_executes_web_search_and_summarizes(self) -> None:
        agent = ResearchAgent()
        mock_search = AsyncMock()
        mock_search.execute.return_value = {"result": [{"title": "AI news"}]}

        with patch(
            "src.agents.research_agent.tools_registry.get", return_value=mock_search
        ), patch(
            "src.agents.base_agent.llm_service.generate",
            AsyncMock(return_value="Summary of AI news"),
        ):
            result = await agent.execute("latest AI news")

        assert result["status"] == "completed"
        mock_search.execute.assert_awaited_once_with(
            action="web_search", query="latest AI news"
        )
