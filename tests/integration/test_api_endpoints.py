from __future__ import annotations

from unittest.mock import AsyncMock, patch

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

    def test_cancel_with_reason_passes_it_through(self, client: TestClient) -> None:
        with patch(
            "src.api.routes.agent.agent_service.cancel", AsyncMock(return_value=True)
        ) as mock_cancel:
            response = client.post(
                "/api/v1/agent/cancel/some-task-id",
                json={"reason": "user requested"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"
        mock_cancel.assert_awaited_once_with("some-task-id", reason="user requested")

    def test_cancel_without_body_works(self, client: TestClient) -> None:
        with patch(
            "src.api.routes.agent.agent_service.cancel", AsyncMock(return_value=True)
        ) as mock_cancel:
            response = client.post("/api/v1/agent/cancel/some-task-id")

        assert response.status_code == 200
        mock_cancel.assert_awaited_once_with("some-task-id", reason="")

    def test_approve_request_passes_approver_through(self, client: TestClient) -> None:
        with patch(
            "src.api.routes.approval.approval_service.approve_request",
            AsyncMock(return_value=True),
        ) as mock_approve:
            response = client.post(
                "/api/v1/approval/requests/req-1/approve",
                json={"approver": "alice"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "approved"
        mock_approve.assert_awaited_once_with("req-1", approver="alice")

    def test_reject_request_passes_approver_and_reason_through(
        self, client: TestClient
    ) -> None:
        with patch(
            "src.api.routes.approval.approval_service.reject_request",
            AsyncMock(return_value=True),
        ) as mock_reject:
            response = client.post(
                "/api/v1/approval/requests/req-1/reject",
                json={"approver": "alice", "reason": "not authorized"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        mock_reject.assert_awaited_once_with(
            "req-1", approver="alice", reason="not authorized"
        )

    def test_approve_request_without_body_works(self, client: TestClient) -> None:
        with patch(
            "src.api.routes.approval.approval_service.approve_request",
            AsyncMock(return_value=True),
        ) as mock_approve:
            response = client.post("/api/v1/approval/requests/req-1/approve")

        assert response.status_code == 200
        mock_approve.assert_awaited_once_with("req-1", approver="")
