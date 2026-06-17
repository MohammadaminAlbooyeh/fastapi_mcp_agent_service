from __future__ import annotations

import pytest
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
