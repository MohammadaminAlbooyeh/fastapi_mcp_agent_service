from __future__ import annotations

from src.utils.validators import validate_agent_type, validate_query, validate_tools


class TestValidators:
    def test_validate_agent_type_valid(self) -> None:
        assert validate_agent_type("query") is True
        assert validate_agent_type("research") is True
        assert validate_agent_type("processor") is True

    def test_validate_agent_type_invalid(self) -> None:
        assert validate_agent_type("unknown") is False
        assert validate_agent_type("") is False

    def test_validate_tools_all_valid(self) -> None:
        available = ["database_tool", "search_tool", "calculator_tool"]
        assert validate_tools(["database_tool"], available) is True
        assert validate_tools(["database_tool", "search_tool"], available) is True

    def test_validate_tools_some_invalid(self) -> None:
        available = ["database_tool", "search_tool"]
        assert validate_tools(["unknown_tool"], available) is False
        assert validate_tools(["database_tool", "unknown_tool"], available) is False

    def test_validate_query_valid(self) -> None:
        assert validate_query("SELECT * FROM users") is True
        assert validate_query("a") is True

    def test_validate_query_invalid(self) -> None:
        assert validate_query("") is False
        assert validate_query("   ") is False
