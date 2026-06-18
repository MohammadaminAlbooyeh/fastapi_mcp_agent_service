from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.database.connection import SessionLocal
from src.database.crud import CRUD
from src.database.models import TaskRecord
from src.models.schemas import Task


class TaskService:
    async def create_task(
        self, query: str, agent_type: str, tools: Optional[List[str]] = None
    ) -> Task:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            record = crud.create_task(query, agent_type, tools)
            return Task(
                task_id=record.task_id,
                query=record.query,
                agent_type=record.agent_type,
                tools=record.tools or [],
                status=record.status,
                created_at=record.created_at or datetime.now(),
                updated_at=record.updated_at or datetime.now(),
            )
        finally:
            db.close()

    async def update_task_status(self, task_id: str, status: str) -> Optional[Task]:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            record = crud.update_task(task_id, {"status": status, "updated_at": datetime.now()})
            if not record:
                return None
            return self._record_to_task(record)
        finally:
            db.close()

    async def save_result(
        self, task_id: str, result: Dict[str, Any], execution_time: float = 0.0
    ) -> Optional[Task]:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            record = crud.update_task(task_id, {
                "result": result,
                "status": "completed",
                "execution_time": execution_time,
                "updated_at": datetime.now(),
            })
            if not record:
                return None
            return self._record_to_task(record)
        finally:
            db.close()

    async def save_error(self, task_id: str, error: str) -> Optional[Task]:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            record = crud.update_task(task_id, {
                "error": error,
                "status": "failed",
                "updated_at": datetime.now(),
            })
            if not record:
                return None
            return self._record_to_task(record)
        finally:
            db.close()

    async def get_task(self, task_id: str) -> Optional[Task]:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            record = crud.get_task(task_id)
            if not record:
                return None
            return self._record_to_task(record)
        finally:
            db.close()

    async def retrieve_task_history(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Task]:
        db = SessionLocal()
        try:
            crud = CRUD(db)
            records = crud.list_tasks(filters)
            return [self._record_to_task(r) for r in records]
        finally:
            db.close()

    def _record_to_task(self, record: TaskRecord) -> Task:
        return Task(
            task_id=record.task_id,
            query=record.query,
            agent_type=record.agent_type,
            tools=record.tools or [],
            status=record.status,
            result=record.result,
            error=record.error,
            execution_time=record.execution_time or 0.0,
            created_at=record.created_at or datetime.now(),
            updated_at=record.updated_at or datetime.now(),
        )


task_service = TaskService()
