from __future__ import annotations

from fastapi import APIRouter

from src.models.request import ApprovalDecisionRequest
from src.services.approval_service import approval_service

router = APIRouter(prefix="/api/v1/approval", tags=["approval"])


@router.get("/requests")
async def list_pending_requests():
    return {"requests": await approval_service.get_pending_requests()}


@router.post("/requests/{request_id}/approve")
async def approve_request(request_id: str, body: ApprovalDecisionRequest | None = None):
    approver = body.approver if body else ""
    success = await approval_service.approve_request(request_id, approver=approver)
    return {"request_id": request_id, "status": "approved" if success else "not_found"}


@router.post("/requests/{request_id}/reject")
async def reject_request(request_id: str, body: ApprovalDecisionRequest | None = None):
    approver = body.approver if body else ""
    reason = body.reason if body else ""
    success = await approval_service.reject_request(
        request_id, approver=approver, reason=reason
    )
    return {"request_id": request_id, "status": "rejected" if success else "not_found"}
