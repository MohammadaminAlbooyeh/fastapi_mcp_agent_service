from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.logger import logger
from src.database.connection import AsyncSessionLocal
from src.database.models import ApprovalRequest as ApprovalRequestModel


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
        task_id: str,
        timeout: int = 300,
    ):
        self.request_id: str = str(uuid4())
        self.task_id = task_id
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.agent_type = agent_type
        self.query = query
        self.status = ApprovalStatus.PENDING
        self.timeout = timeout
        self.created_at = datetime.now()
        self.expires_at = self.created_at + timedelta(seconds=timeout)
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
        task_id: str,
        timeout: int = 300,
    ) -> ToolApprovalRequest:
        request = ToolApprovalRequest(
            tool_name=tool_name,
            tool_args=tool_args,
            agent_type=agent_type,
            query=query,
            task_id=task_id,
            timeout=timeout,
        )
        self._pending_requests[request.request_id] = request

        try:
            async with AsyncSessionLocal() as session:
                db_request = ApprovalRequestModel(
                    request_id=request.request_id,
                    task_id=task_id,
                    tool_name=tool_name,
                    tool_args=tool_args,
                    agent_type=agent_type,
                    query=query,
                    status=ApprovalStatus.PENDING.value,
                    expires_at=request.expires_at,
                )
                session.add(db_request)
                await session.commit()
                logger.info(f"Approval request {request.request_id} created for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to save approval request to database: {e}")

        return request

    async def approve_request(self, request_id: str, approver: str = "") -> bool:
        request = self._pending_requests.get(request_id)
        if request and request.status == ApprovalStatus.PENDING:
            await request.approve()

            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(ApprovalRequestModel).where(
                            ApprovalRequestModel.request_id == request_id
                        )
                    )
                    db_request = result.scalar_one_or_none()
                    if db_request:
                        db_request.status = ApprovalStatus.APPROVED.value
                        db_request.approver = approver
                        db_request.updated_at = datetime.now()
                        await session.commit()
                        logger.info(f"Approval request {request_id} approved by {approver}")
            except Exception as e:
                logger.error(f"Failed to update approval request in database: {e}")

            return True
        return False

    async def reject_request(
        self, request_id: str, approver: str = "", reason: str = ""
    ) -> bool:
        request = self._pending_requests.get(request_id)
        if request and request.status == ApprovalStatus.PENDING:
            await request.reject(reason)

            try:
                async with AsyncSessionLocal() as session:
                    result = await session.execute(
                        select(ApprovalRequestModel).where(
                            ApprovalRequestModel.request_id == request_id
                        )
                    )
                    db_request = result.scalar_one_or_none()
                    if db_request:
                        db_request.status = ApprovalStatus.REJECTED.value
                        db_request.approver = approver
                        db_request.rejection_reason = reason
                        db_request.updated_at = datetime.now()
                        await session.commit()
                        logger.info(f"Approval request {request_id} rejected by {approver}")
            except Exception as e:
                logger.error(f"Failed to update approval request in database: {e}")

            return True
        return False

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        return [
            {
                "request_id": r.request_id,
                "task_id": r.task_id,
                "tool_name": r.tool_name,
                "tool_args": r.tool_args,
                "agent_type": r.agent_type,
                "query": r.query,
                "status": r.status.value,
                "created_at": r.created_at.isoformat(),
                "expires_at": r.expires_at.isoformat(),
            }
            for r in self._pending_requests.values()
            if r.status == ApprovalStatus.PENDING
        ]


approval_service = ApprovalService()
