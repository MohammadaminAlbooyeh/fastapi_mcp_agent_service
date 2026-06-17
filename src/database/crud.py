from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.database.models import TaskRecord


class CRUD:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_task(
        self, query: str, agent_type: str, tools: Optional[List[str]] = None
    ) -> TaskRecord:
        task = TaskRecord(
            query=query,
            agent_type=agent_type,
            tools=tools or [],
        )
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return (
            self.db.query(TaskRecord)
            .filter(TaskRecord.task_id == task_id)
            .first()
        )

    def update_task(
        self, task_id: str, updates: Dict[str, Any]
    ) -> Optional[TaskRecord]:
        task = self.get_task(task_id)
        if task:
            for key, value in updates.items():
                setattr(task, key, value)
            self.db.commit()
            self.db.refresh(task)
        return task

    def list_tasks(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[TaskRecord]:
        query = self.db.query(TaskRecord)
        if filters:
            for key, value in filters.items():
                query = query.filter(
                    getattr(TaskRecord, key) == value
                )
        return query.order_by(TaskRecord.created_at.desc()).all()
