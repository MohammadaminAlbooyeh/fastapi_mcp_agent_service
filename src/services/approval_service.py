from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import select

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

    async def wait_for_decision(
        self,
        poll_interval: float = 0.5,
        max_poll_interval: float = 10.0,
        poll_backoff: float = 2.0,
    ) -> ApprovalStatus:
        """Polls the DB with exponential backoff when the local event doesn't
        fire (i.e. the decision came from a different worker process). Backoff
        keeps DB load low for approvals that sit pending for a while, while
        still reacting quickly to approvals decided soon after the request."""
        deadline = asyncio.get_event_loop().time() + self.timeout
        current_interval = poll_interval
        while True:
            remaining = deadline - asyncio.get_event_loop().time()
            if remaining <= 0:
                self.status = ApprovalStatus.EXPIRED
                return self.status
            try:
                await asyncio.wait_for(
                    self._event.wait(), timeout=min(current_interval, remaining)
                )
                return self.status
            except asyncio.TimeoutError:
                # The decision may have been made by a different worker process
                # (e.g. the approve/reject API call landed on another process),
                # in which case our local event never fires. Poll the DB instead.
                db_status = await self._fetch_db_status()
                if db_status is not None and db_status != ApprovalStatus.PENDING:
                    self.status = db_status
                    self._event.set()
                    return self.status
                current_interval = min(
                    current_interval * poll_backoff, max_poll_interval
                )

    async def _fetch_db_status(self) -> Optional["ApprovalStatus"]:
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ApprovalRequestModel).where(
                        ApprovalRequestModel.request_id == self.request_id
                    )
                )
                db_request = result.scalar_one_or_none()
                if db_request is None:
                    return None
                return ApprovalStatus(db_request.status)
        except Exception as e:
            logger.error(
                f"Failed to poll approval request {self.request_id} from database: {e}"
            )
            return None


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
                logger.info(
                    f"Approval request {request.request_id} created for task {task_id}"
                )
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
                        logger.info(
                            f"Approval request {request_id} approved by {approver}"
                        )
            except Exception as e:
                logger.error(f"Failed to update approval request in database: {e}")

            return True
        return await self._decide_in_db(
            request_id, ApprovalStatus.APPROVED, approver=approver
        )

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
                        logger.info(
                            f"Approval request {request_id} rejected by {approver}"
                        )
            except Exception as e:
                logger.error(f"Failed to update approval request in database: {e}")

            return True
        return await self._decide_in_db(
            request_id, ApprovalStatus.REJECTED, approver=approver, reason=reason
        )

    async def _decide_in_db(
        self,
        request_id: str,
        status: ApprovalStatus,
        approver: str = "",
        reason: str = "",
    ) -> bool:
        """Apply an approve/reject decision for a request this process doesn't hold
        in memory (e.g. it was created by a different worker process). The worker
        that is actually waiting on the request polls the DB and picks this up."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ApprovalRequestModel).where(
                        ApprovalRequestModel.request_id == request_id
                    )
                )
                db_request = result.scalar_one_or_none()
                if (
                    db_request is None
                    or db_request.status != ApprovalStatus.PENDING.value
                ):
                    return False
                db_request.status = status.value
                db_request.approver = approver
                if reason:
                    db_request.rejection_reason = reason
                db_request.updated_at = datetime.now()
                await session.commit()
                logger.info(
                    f"Approval request {request_id} {status.value} by {approver} (cross-process)"
                )
                return True
        except Exception as e:
            logger.error(f"Failed to update approval request in database: {e}")
            return False

    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """Reads from the DB rather than the in-memory dict, since pending requests
        may have been created by a different worker process than the one serving
        this call."""
        try:
            async with AsyncSessionLocal() as session:
                result = await session.execute(
                    select(ApprovalRequestModel).where(
                        ApprovalRequestModel.status == ApprovalStatus.PENDING.value
                    )
                )
                return [
                    {
                        "request_id": r.request_id,
                        "task_id": r.task_id,
                        "tool_name": r.tool_name,
                        "tool_args": r.tool_args,
                        "agent_type": r.agent_type,
                        "query": r.query,
                        "status": r.status,
                        "created_at": r.created_at.isoformat(),
                        "expires_at": r.expires_at.isoformat(),
                    }
                    for r in result.scalars().all()
                ]
        except Exception as e:
            logger.error(f"Failed to list pending approval requests from database: {e}")
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
