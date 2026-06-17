from __future__ import annotations

from typing import Any, Dict

SAMPLE_TASK: Dict[str, Any] = {
    "task_id": "test-task-001",
    "query": "Get all users from database where age > 25",
    "agent_type": "query",
    "tools": ["database_tool"],
    "status": "completed",
}

SAMPLE_QUERIES: list[str] = [
    "Get all users from database where age > 25",
    "Calculate the average order value",
    "Research the latest AI trends",
]
