from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException

from src.agents.orchestrator import orchestrator
from src.models.request import AgentExecuteRequest
from src.models.response import TaskResponse

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/execute", response_model=TaskResponse)
async def execute_agent(request: AgentExecuteRequest) -> TaskResponse:
    try:
        result = await orchestrator.execute(
            query=request.query,
            agent_type=request.agent_type,
            tools=request.tools,
            max_iterations=request.max_iterations,
            timeout=request.timeout,
        )
        return TaskResponse(
            task_id="",
            status="completed",
            result=result,
            execution_time=0.0,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def stream_agent(request: AgentExecuteRequest) -> dict:
    return {"message": "Stream endpoint not yet implemented"}


@router.get("/status/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str) -> TaskResponse:
    return TaskResponse(task_id=task_id, status="pending")


@router.get("/result/{task_id}", response_model=TaskResponse)
async def get_task_result(task_id: str) -> TaskResponse:
    return TaskResponse(task_id=task_id, status="pending")


@router.post("/cancel/{task_id}")
async def cancel_task(task_id: str) -> dict:
    return {"task_id": task_id, "status": "cancelled"}
