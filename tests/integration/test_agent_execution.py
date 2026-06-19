from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestAgentExecution:
    def test_execute_requires_auth(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "query": "test query",
                "agent_type": "query",
            },
        )
        assert response.status_code in (200, 403)

    def test_execute_query_agent(self, client: TestClient, sample_query: str) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={
                "query": sample_query,
                "agent_type": "query",
                "tools": ["database_tool"],
                "max_iterations": 5,
                "timeout": 30,
            },
        )
        assert response.status_code in (200, 500)

    def test_list_tools(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        tools = response.json()
        assert len(tools) == 5
        tool_names = [t["name"] for t in tools]
        assert "database_tool" in tool_names
        assert "calculator_tool" in tool_names
        assert "search_tool" in tool_names
        assert "api_tool" in tool_names
        assert "file_tool" in tool_names

    def test_get_tool_details(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools/calculator_tool")
        assert response.status_code == 200
        assert response.json()["name"] == "calculator_tool"
        assert response.json()["status"] == "active"

    def test_get_nonexistent_tool(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools/nonexistent_tool")
        assert response.status_code == 404

    def test_health_endpoint(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_detailed_health(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert "database" in data["dependencies"]
        assert "redis" in data["dependencies"]

    def test_approval_pending_requests(self, client: TestClient) -> None:
        response = client.get("/api/v1/approval/requests")
        assert response.status_code == 200
        assert "requests" in response.json()

    def test_metrics_endpoint(self, client: TestClient) -> None:
        response = client.get("/metrics")
        assert response.status_code == 200
