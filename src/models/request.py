from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class AgentExecuteRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    agent_type: str
    tools: Optional[List[str]] = None
    max_iterations: int = Field(default=5, ge=1, le=20)
    timeout: int = Field(default=30, ge=1, le=300)


class TaskCancelRequest(BaseModel):
    reason: str
