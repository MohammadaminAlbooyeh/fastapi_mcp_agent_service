from __future__ import annotations

from fastapi import APIRouter

from src.services.approval_service import approval_service

router = APIRouter(prefix="/api/v1/approval", tags=["approval"])


@router.get("/requests")
async def list_pending_requests():
    return {"requests": approval_service.get_pending_requests()}


@router.post("/requests/{request_id}/approve")
async def approve_request(request_id: str):
    success = await approval_service.approve_request(request_id)
    return {"request_id": request_id, "status": "approved" if success else "not_found"}


@router.post("/requests/{request_id}/reject")
async def reject_request(request_id: str, reason: str = ""):
    success = await approval_service.reject_request(request_id, reason)
    return {"request_id": request_id, "status": "rejected" if success else "not_found"}
