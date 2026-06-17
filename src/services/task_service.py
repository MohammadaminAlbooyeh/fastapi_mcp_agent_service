from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.models.schemas import Task


class TaskService:
    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    async def create_task(
        self, query: str, agent_type: str, tools: Optional[List[str]] = None
    ) -> Task:
        task = Task(
            task_id=str(uuid4()),
            query=query,
            agent_type=agent_type,
            tools=tools or [],
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        self._tasks[task.task_id] = task
        return task

    async def update_task_status(
        self, task_id: str, status: str
    ) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
        return task

    async def save_result(
        self, task_id: str, result: Dict[str, Any]
    ) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task:
            task.result = result
            task.status = "completed"
            task.updated_at = datetime.now()
        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    async def retrieve_task_history(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        tasks = list(self._tasks.values())
        if filters:
            for key, value in filters.items():
                tasks = [
                    t for t in tasks if getattr(t, key, None) == value
                ]
        return sorted(tasks, key=lambda t: t.created_at, reverse=True)


task_service = TaskService()
