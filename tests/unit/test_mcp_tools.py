from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp_tools.api_tool import APITool
from src.mcp_tools.calculator_tool import CalculatorTool
from src.mcp_tools.database_tool import DatabaseTool
from src.mcp_tools.file_tool import FileTool
from src.mcp_tools.search_tool import SearchTool
from src.mcp_tools.tools_registry import ToolsRegistry


class TestToolsRegistry:
    def setup_method(self) -> None:
        self.registry = ToolsRegistry()

    def test_register_tool(self) -> None:
        tool = CalculatorTool()
        self.registry.register(tool)
        assert self.registry.get("calculator_tool") == tool

    def test_list_tools(self) -> None:
        tools = self.registry.list_tools()
        assert len(tools) > 0
        names = [t["name"] for t in tools]
        assert "database_tool" in names
        assert "file_tool" in names
        assert "search_tool" in names
        assert "api_tool" in names
        assert "calculator_tool" in names

    def test_get_nonexistent_tool(self) -> None:
        with pytest.raises(KeyError):
            self.registry.get("nonexistent_tool")

    def test_get_tool_names(self) -> None:
        names = self.registry.get_tool_names()
        assert len(names) == 5
        assert "database_tool" in names

    def test_get_existing_tool(self) -> None:
        tool = self.registry.get("calculator_tool")
        assert isinstance(tool, CalculatorTool)
        assert tool.name == "calculator_tool"


class TestCalculatorTool:
    def setup_method(self) -> None:
        self.tool = CalculatorTool()

    @pytest.mark.asyncio
    async def test_simple_addition(self) -> None:
        result = await self.tool.execute(expression="2 + 3")
        assert result["result"] == 5.0

    @pytest.mark.asyncio
    async def test_complex_expression(self) -> None:
        result = await self.tool.execute(expression="(10 + 5) * 2 - 3")
        assert result["result"] == 27.0

    @pytest.mark.asyncio
    async def test_division(self) -> None:
        result = await self.tool.execute(expression="10 / 3")
        assert abs(result["result"] - 3.3333) < 0.01

    @pytest.mark.asyncio
    async def test_invalid_expression(self) -> None:
        result = await self.tool.execute(expression="invalid + 1")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_power(self) -> None:
        result = await self.tool.execute(expression="2 ** 10")
        assert result["result"] == 1024.0

    def test_tool_name(self) -> None:
        assert self.tool.name == "calculator_tool"

    def test_tool_description(self) -> None:
        assert "calculation" in self.tool.description.lower()


class TestFileTool:
    def setup_method(self) -> None:
        self.tool = FileTool()

    @pytest.mark.asyncio
    async def test_file_not_found(self) -> None:
        result = await self.tool.execute(
            action="read", path="_nonexistent_file_xyz.txt"
        )
        assert "error" in result

    @pytest.mark.asyncio
    async def test_list_nonexistent_directory(self) -> None:
        result = await self.tool.execute(
            action="list", directory="_nonexistent_dir_xyz"
        )
        assert result["result"] == []

    @pytest.mark.asyncio
    async def test_unknown_action(self) -> None:
        result = await self.tool.execute(action="unknown")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_file_exists_nonexistent(self) -> None:
        result = await self.tool.execute(
            action="exists", path="_nonexistent_file_xyz.txt"
        )
        assert result["result"] is False


class TestDatabaseTool:
    def setup_method(self) -> None:
        self.tool = DatabaseTool()

    @pytest.mark.asyncio
    async def test_unknown_action(self) -> None:
        result = await self.tool.execute(action="unknown")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_query_no_sql(self) -> None:
        result = await self.tool.execute(action="query", sql="")
        assert "error" in result or "result" in result

    @pytest.mark.asyncio
    async def test_execute_query_rejects_non_select(self) -> None:
        result = await self.tool.execute(
            action="query", sql="DELETE FROM tasks WHERE 1=1"
        )
        assert "error" in result
        assert "SELECT" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_query_rejects_stacked_statements(self) -> None:
        result = await self.tool.execute(
            action="query", sql="SELECT 1; DROP TABLE tasks"
        )
        assert "error" in result
        assert "SELECT" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_query_allows_select(self) -> None:
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.returns_rows = True
        mock_result.__iter__.return_value = iter([])
        mock_db.execute.return_value = mock_result

        with patch(
            "src.mcp_tools.database_tool.SessionLocal", return_value=mock_db
        ):
            result = await self.tool.execute(
                action="query", sql="SELECT * FROM tasks"
            )
        assert result["result"] == []

    @pytest.mark.asyncio
    async def test_insert_record_rejects_unknown_table(self) -> None:
        result = await self.tool.execute(
            action="insert", table="users; DROP TABLE tasks", data={"query": "x"}
        )
        assert "error" in result
        assert "table" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_insert_record_rejects_unknown_column(self) -> None:
        result = await self.tool.execute(
            action="insert", table="tasks", data={"malicious_column": "x"}
        )
        assert "error" in result
        assert "column" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_insert_record_allows_known_table_and_columns(self) -> None:
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)
        mock_db.execute.return_value = mock_result

        with patch(
            "src.mcp_tools.database_tool.SessionLocal", return_value=mock_db
        ):
            result = await self.tool.execute(
                action="insert",
                table="tasks",
                data={"query": "hello", "agent_type": "query"},
            )
        assert result["result"] == 1

    @pytest.mark.asyncio
    async def test_update_record_rejects_unknown_table(self) -> None:
        result = await self.tool.execute(
            action="update", table="not_a_table", id=1, data={"status": "done"}
        )
        assert "error" in result
        assert "table" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_update_record_rejects_unknown_column(self) -> None:
        result = await self.tool.execute(
            action="update", table="tasks", id=1, data={"is_admin": True}
        )
        assert "error" in result
        assert "column" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_delete_record_rejects_unknown_table(self) -> None:
        result = await self.tool.execute(action="delete", table="not_a_table", id=1)
        assert "error" in result
        assert "table" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_list_records_rejects_unknown_table(self) -> None:
        result = await self.tool.execute(action="list", table="not_a_table")
        assert "error" in result
        assert "table" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_list_records_rejects_unknown_filter_column(self) -> None:
        result = await self.tool.execute(
            action="list", table="tasks", filters={"1=1 OR ": "x"}
        )
        assert "error" in result
        assert "column" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_list_records_allows_known_table_and_filters(self) -> None:
        mock_db = MagicMock()
        mock_result = MagicMock()
        mock_result.returns_rows = True
        mock_result.__iter__.return_value = iter([])
        mock_db.execute.return_value = mock_result

        with patch(
            "src.mcp_tools.database_tool.SessionLocal", return_value=mock_db
        ):
            result = await self.tool.execute(
                action="list", table="tasks", filters={"status": "pending"}
            )
        assert result["result"] == []


class TestSearchTool:
    def setup_method(self) -> None:
        self.tool = SearchTool()

    @pytest.mark.asyncio
    async def test_unknown_action(self) -> None:
        result = await self.tool.execute(action="unknown")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_semantic_search_no_api_key(self, monkeypatch) -> None:
        monkeypatch.setattr("src.mcp_tools.search_tool.settings.openai_api_key", "")
        result = await self.tool.execute(
            action="semantic_search", query="test", index="docs"
        )
        assert "result" in result
        assert "Set OPENAI_API_KEY" in str(result["result"])

    @pytest.mark.asyncio
    async def test_similarity_search_no_api_key(self, monkeypatch) -> None:
        monkeypatch.setattr("src.mcp_tools.search_tool.settings.openai_api_key", "")
        result = await self.tool.execute(
            action="similarity_search", text="test", top_k=3
        )
        assert "result" in result
        assert "Set OPENAI_API_KEY" in str(result["result"])


class TestAPITool:
    def setup_method(self) -> None:
        self.tool = APITool()

    @pytest.mark.asyncio
    async def test_http_request_success(self, monkeypatch) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.text = '{"ok": true}'

        mock_client = AsyncMock()
        mock_client.request.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_client), patch(
            "socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]
        ):
            result = await self.tool.execute(
                action="http_request",
                method="GET",
                url="https://api.example.com/data",
            )
            assert result["result"]["status_code"] == 200
            assert "ok" in result["result"]["body"]

    @pytest.mark.asyncio
    async def test_rest_api_success(self, monkeypatch) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"items": []}'

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_client), patch(
            "socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]
        ):
            result = await self.tool.execute(
                action="rest_api",
                endpoint="https://api.example.com/items",
            )
            assert result["result"]["status_code"] == 200

    @pytest.mark.asyncio
    async def test_graphql(self, monkeypatch) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '{"data": {"user": {"id": 1}}}'

        mock_client = AsyncMock()
        mock_client.post.return_value = mock_response
        mock_client.__aenter__.return_value = mock_client

        with patch("httpx.AsyncClient", return_value=mock_client), patch(
            "socket.getaddrinfo", return_value=[(2, 1, 6, "", ("93.184.216.34", 0))]
        ):
            result = await self.tool.execute(
                action="graphql",
                endpoint="https://api.example.com/graphql",
                query="{ user(id: 1) { id } }",
            )
            assert result["result"]["status_code"] == 200
            assert "user" in result["result"]["body"]

    @pytest.mark.asyncio
    async def test_unknown_action(self) -> None:
        result = await self.tool.execute(action="unknown")
        assert "error" in result
