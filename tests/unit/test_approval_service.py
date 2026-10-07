from __future__ import annotations

import asyncio
from typing import Dict

import pytest

from src.services.approval_service import ApprovalService, ApprovalStatus, ToolApprovalRequest


class TestApprovalService:
    def setup_method(self) -> None:
        self.service = ApprovalService()

    @pytest.mark.asyncio
    async def test_request_approval(self) -> None:
        req = await self.service.request_approval(
            tool_name="database_tool",
            tool_args={"sql": "SELECT * FROM users"},
            agent_type="query",
            query="Get all users",
            task_id="test-task-1",
        )
        assert req.request_id is not None
        assert req.status == ApprovalStatus.PENDING
        assert req.tool_name == "database_tool"

    @pytest.mark.asyncio
    async def test_approve_request(self) -> None:
        req = await self.service.request_approval(
            tool_name="search_tool",
            tool_args={"query": "AI news"},
            agent_type="research",
            query="Search AI news",
            task_id="test-task-2",
        )
        success = await self.service.approve_request(req.request_id)
        assert success is True
        assert req.status == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_reject_request(self) -> None:
        req = await self.service.request_approval(
            tool_name="file_tool",
            tool_args={"action": "delete", "path": "/data"},
            agent_type="processor",
            query="Delete file",
            task_id="test-task-3",
        )
        success = await self.service.reject_request(req.request_id, "Not authorized")
        assert success is True
        assert req.status == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_approve_nonexistent_request(self) -> None:
        success = await self.service.approve_request("nonexistent-id")
        assert success is False

    @pytest.mark.asyncio
    async def test_reject_nonexistent_request(self) -> None:
        success = await self.service.reject_request("nonexistent-id")
        assert success is False

    @pytest.mark.asyncio
    async def test_get_pending_requests(self) -> None:
        await self.service.request_approval("tool1", {}, "agent1", "query1", "task-p1")
        await self.service.request_approval("tool2", {}, "agent2", "query2", "task-p2")

        pending = await self.service.get_pending_requests()
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_get_pending_after_approval(self) -> None:
        req = await self.service.request_approval("tool1", {}, "agent1", "query1", "task-pa1")
        await self.service.approve_request(req.request_id)

        pending = await self.service.get_pending_requests()
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_wait_for_decision_approve(self) -> None:
        req = await self.service.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
            task_id="test-task-4",
            timeout=5,
        )
        await self.service.approve_request(req.request_id)
        decision = await req.wait_for_decision()
        assert decision == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_wait_for_decision_reject(self) -> None:
        req = await self.service.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
            task_id="test-task-5",
            timeout=5,
        )
        await self.service.reject_request(req.request_id)
        decision = await req.wait_for_decision()
        assert decision == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_decision_timeout(self) -> None:
        req = await self.service.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
            task_id="test-task-6",
            timeout=0.1,
        )
        decision = await req.wait_for_decision()
        assert decision == ApprovalStatus.EXPIRED

    @pytest.mark.asyncio
    async def test_cross_process_approval_detected_via_db_polling(self, monkeypatch) -> None:
        """Simulates two worker processes: service_a holds the request's
        asyncio.Event (it received the original request), service_b receives
        the approve call (e.g. a different API worker). service_b can't see
        service_a's in-memory request, so it must fall back to writing the
        decision to the DB; service_a must pick it up by polling the DB rather
        than waiting on an event that will never fire in its process."""
        shared_db: Dict[str, ApprovalStatus] = {}

        async def fake_decide_in_db(self, request_id, status, approver="", reason=""):
            if shared_db.get(request_id, ApprovalStatus.PENDING) != ApprovalStatus.PENDING:
                return False
            shared_db[request_id] = status
            return True

        async def fake_fetch_db_status(self):
            return shared_db.get(self.request_id)

        monkeypatch.setattr(ApprovalService, "_decide_in_db", fake_decide_in_db)
        monkeypatch.setattr(ToolApprovalRequest, "_fetch_db_status", fake_fetch_db_status)

        service_a = ApprovalService()
        service_b = ApprovalService()

        req = await service_a.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
            task_id="test-task-7",
            timeout=5,
        )
        shared_db[req.request_id] = ApprovalStatus.PENDING

        async def approve_from_other_worker() -> None:
            await asyncio.sleep(0.05)
            success = await service_b.approve_request(req.request_id)
            assert success is True

        decision, _ = await asyncio.gather(
            req.wait_for_decision(poll_interval=0.02),
            approve_from_other_worker(),
        )
        assert decision == ApprovalStatus.APPROVED

    @pytest.mark.asyncio
    async def test_cross_process_rejection_detected_via_db_polling(self, monkeypatch) -> None:
        shared_db: Dict[str, ApprovalStatus] = {}

        async def fake_decide_in_db(self, request_id, status, approver="", reason=""):
            if shared_db.get(request_id, ApprovalStatus.PENDING) != ApprovalStatus.PENDING:
                return False
            shared_db[request_id] = status
            return True

        async def fake_fetch_db_status(self):
            return shared_db.get(self.request_id)

        monkeypatch.setattr(ApprovalService, "_decide_in_db", fake_decide_in_db)
        monkeypatch.setattr(ToolApprovalRequest, "_fetch_db_status", fake_fetch_db_status)

        service_a = ApprovalService()
        service_b = ApprovalService()

        req = await service_a.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
            task_id="test-task-8",
            timeout=5,
        )
        shared_db[req.request_id] = ApprovalStatus.PENDING

        async def reject_from_other_worker() -> None:
            await asyncio.sleep(0.05)
            success = await service_b.reject_request(req.request_id, reason="no")
            assert success is True

        decision, _ = await asyncio.gather(
            req.wait_for_decision(poll_interval=0.02),
            reject_from_other_worker(),
        )
        assert decision == ApprovalStatus.REJECTED

    @pytest.mark.asyncio
    async def test_decide_in_db_returns_false_when_already_decided(self, monkeypatch) -> None:
        """A second, concurrent approve/reject call for the same request_id
        (e.g. two admins clicking at once, or a retried request) must not
        double-apply the decision."""
        shared_db: Dict[str, ApprovalStatus] = {}

        async def fake_decide_in_db(self, request_id, status, approver="", reason=""):
            if shared_db.get(request_id, ApprovalStatus.PENDING) != ApprovalStatus.PENDING:
                return False
            shared_db[request_id] = status
            return True

        monkeypatch.setattr(ApprovalService, "_decide_in_db", fake_decide_in_db)

        shared_db["already-decided"] = ApprovalStatus.APPROVED
        other_service = ApprovalService()
        success = await other_service.reject_request("already-decided")
        assert success is False
