from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.auth import verify_token
from src.models.request import AgentExecuteRequest, TaskCancelRequest
from src.models.response import TaskResponse
from src.services.agent_service import agent_service
from src.utils.validators import validate_agent_type

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/execute", response_model=TaskResponse)
async def execute_agent(
    request: AgentExecuteRequest,
    _=Depends(verify_token),
) -> TaskResponse:
    if not validate_agent_type(request.agent_type):
        raise HTTPException(
            status_code=400, detail=f"Unknown agent_type: {request.agent_type!r}"
        )
    result = await agent_service.execute(
        query=request.query,
        agent_type=request.agent_type,
        tools=request.tools,
        max_iterations=request.max_iterations,
        timeout=request.timeout,
    )
    return TaskResponse(
        task_id=result.get("task_id", ""),
        status=result.get("status", "failed"),
        result=result.get("result"),
        execution_time=result.get("execution_time", 0.0),
        error=result.get("error"),
    )


@router.post("/stream")
async def stream_agent(
    request: AgentExecuteRequest,
    _=Depends(verify_token),
):
    if not validate_agent_type(request.agent_type):
        raise HTTPException(
            status_code=400, detail=f"Unknown agent_type: {request.agent_type!r}"
        )
    return StreamingResponse(
        agent_service.stream(
            query=request.query,
            agent_type=request.agent_type,
            tools=request.tools,
            timeout=request.timeout,
        ),
        media_type="text/event-stream",
    )


@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    _=Depends(verify_token),
) -> TaskResponse:
    from src.services.task_service import task_service

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


@router.get("/result/{task_id}", response_model=TaskResponse)
async def get_task_result(
    task_id: str,
    _=Depends(verify_token),
) -> TaskResponse:
    from src.services.task_service import task_service

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


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    request: TaskCancelRequest | None = None,
    _=Depends(verify_token),
) -> dict:
    reason = request.reason if request else ""
    cancelled = await agent_service.cancel(task_id, reason=reason)
    return {"task_id": task_id, "status": "cancelled" if cancelled else "not_found"}
