from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/status", tags=["status"])


@router.get("/{task_id}")
async def get_task_status(task_id: str) -> dict:
    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}/result")
async def get_task_result(task_id: str) -> dict:
    return {"task_id": task_id, "status": "pending", "result": None}
