from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class AgentExecuteRequest(BaseModel):
    query: str
    agent_type: str
    tools: Optional[List[str]] = None
    max_iterations: int = 5
    timeout: int = 30


class TaskCancelRequest(BaseModel):
    reason: str
