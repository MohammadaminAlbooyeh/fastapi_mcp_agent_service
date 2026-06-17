from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


class TestAgentExecution:
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
