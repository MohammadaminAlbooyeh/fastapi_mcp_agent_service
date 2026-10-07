from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Task(BaseModel):
    task_id: str
    query: str
    agent_type: str
    tools: List[str] = []
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    # default_factory, not a bare `datetime.now()` call: a plain default
    # expression is evaluated once at class-definition time, so every Task
    # created without an explicit timestamp would share the exact moment this
    # module was first imported instead of getting its own creation time.
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    execution_time: float = 0.0
