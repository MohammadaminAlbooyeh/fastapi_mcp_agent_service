from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.services.cache_service import cache_service


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ToolApprovalRequest:
    def __init__(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        agent_type: str,
        query: str,
        timeout: int = 60,
    ):
        self.request_id: str = str(uuid4())
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.agent_type = agent_type
        self.query = query
        self.status = ApprovalStatus.PENDING
        self.timeout = timeout
        self.created_at = datetime.now().isoformat()
        self._event = asyncio.Event()

    async def approve(self) -> None:
        self.status = ApprovalStatus.APPROVED
        self._event.set()

    async def reject(self, reason: str = "") -> None:
        self.status = ApprovalStatus.REJECTED
        self._event.set()

    async def wait_for_decision(self) -> ApprovalStatus:
        try:
            await asyncio.wait_for(self._event.wait(), timeout=self.timeout)
        except asyncio.TimeoutError:
            self.status = ApprovalStatus.EXPIRED
        return self.status


class ApprovalService:
    def __init__(self):
        self._pending_requests: Dict[str, ToolApprovalRequest] = {}

    async def request_approval(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        agent_type: str,
        query: str,
    ) -> ToolApprovalRequest:
        request = ToolApprovalRequest(
            tool_name=tool_name,
            tool_args=tool_args,
            agent_type=agent_type,
            query=query,
        )
        self._pending_requests[request.request_id] = request
        return request

    async def approve_request(self, request_id: str) -> bool:
        request = self._pending_requests.get(request_id)
        if request and request.status == ApprovalStatus.PENDING:
            await request.approve()
            return True
        return False

    async def reject_request(self, request_id: str, reason: str = "") -> bool:
        request = self._pending_requests.get(request_id)
        if request and request.status == ApprovalStatus.PENDING:
            await request.reject(reason)
            return True
        return False

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        return [
            {
                "request_id": r.request_id,
                "tool_name": r.tool_name,
                "tool_args": r.tool_args,
                "agent_type": r.agent_type,
                "query": r.query,
                "status": r.status.value,
                "created_at": r.created_at,
            }
            for r in self._pending_requests.values()
            if r.status == ApprovalStatus.PENDING
        ]


approval_service = ApprovalService()
