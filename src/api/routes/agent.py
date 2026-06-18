from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.auth import verify_token
from src.models.request import AgentExecuteRequest
from src.models.response import TaskResponse
from src.services.agent_service import agent_service

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/execute", response_model=TaskResponse)
async def execute_agent(
    request: AgentExecuteRequest,
    _=Depends(verify_token),
) -> TaskResponse:
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
    return StreamingResponse(
        agent_service.stream(
            query=request.query,
            agent_type=request.agent_type,
            tools=request.tools,
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
    _=Depends(verify_token),
) -> dict:
    cancelled = await agent_service.cancel(task_id)
    return {"task_id": task_id, "status": "cancelled" if cancelled else "not_found"}
