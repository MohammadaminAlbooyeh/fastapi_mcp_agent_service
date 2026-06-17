from __future__ import annotations

from typing import Any, Dict, Optional

from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class ToolResponse(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any] = {}
    status: str = "active"
