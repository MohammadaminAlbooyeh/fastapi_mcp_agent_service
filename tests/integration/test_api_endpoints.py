from __future__ import annotations

from fastapi.testclient import TestClient


class TestAPIEndpoints:
    def test_health_check(self, client: TestClient) -> None:
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    def test_detailed_health(self, client: TestClient) -> None:
        response = client.get("/api/v1/health/detailed")
        assert response.status_code == 200

    def test_list_tools(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        assert len(response.json()) > 0

    def test_get_tool(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools/database_tool")
        assert response.status_code == 200

    def test_get_nonexistent_tool(self, client: TestClient) -> None:
        response = client.get("/api/v1/tools/nonexistent")
        assert response.status_code == 404

    def test_execute_rejects_unknown_agent_type(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={"query": "hello", "agent_type": "not-a-real-agent"},
        )
        assert response.status_code == 400

    def test_stream_rejects_unknown_agent_type(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/stream",
            json={"query": "hello", "agent_type": "not-a-real-agent"},
        )
        assert response.status_code == 400

    def test_execute_rejects_oversized_query(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={"query": "x" * 10_001, "agent_type": "query"},
        )
        assert response.status_code == 422

    def test_execute_rejects_empty_query(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={"query": "", "agent_type": "query"},
        )
        assert response.status_code == 422

    def test_execute_rejects_out_of_range_timeout(self, client: TestClient) -> None:
        response = client.post(
            "/api/v1/agent/execute",
            json={"query": "hi", "agent_type": "query", "timeout": 100_000},
        )
        assert response.status_code == 422
