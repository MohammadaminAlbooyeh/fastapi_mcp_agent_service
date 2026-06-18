from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import verify_token
from src.models.response import TaskResponse
from src.services.task_service import task_service

router = APIRouter(prefix="/api/v1/status", tags=["status"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    _=Depends(verify_token),
) -> TaskResponse:
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return TaskResponse(
        task_id=task.task_id,
        status=task.status,
        result=task.result,
        execution_time=task.execution_time,
        error=task.error,
    )


@router.get("/{task_id}/result", response_model=TaskResponse)
async def get_task_result(
    task_id: str,
    _=Depends(verify_token),
) -> TaskResponse:
    task = await task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
    return TaskResponse(
        task_id=task.task_id,
        status=task.status,
        result=task.result,
        execution_time=task.execution_time,
        error=task.error,
    )
