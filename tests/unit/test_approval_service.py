from __future__ import annotations

import pytest

from src.services.approval_service import ApprovalService, ApprovalStatus


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
        await self.service.request_approval("tool1", {}, "agent1", "query1")
        await self.service.request_approval("tool2", {}, "agent2", "query2")

        pending = self.service.get_pending_requests()
        assert len(pending) == 2

    @pytest.mark.asyncio
    async def test_get_pending_after_approval(self) -> None:
        req = await self.service.request_approval("tool1", {}, "agent1", "query1")
        await self.service.approve_request(req.request_id)

        pending = self.service.get_pending_requests()
        assert len(pending) == 0

    @pytest.mark.asyncio
    async def test_wait_for_decision_approve(self) -> None:
        req = await self.service.request_approval(
            tool_name="tool",
            tool_args={},
            agent_type="agent",
            query="query",
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
            timeout=0.1,
        )
        decision = await req.wait_for_decision()
        assert decision == ApprovalStatus.EXPIRED
