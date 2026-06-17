from __future__ import annotations

from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


class Queries:
    def __init__(self, db: Session) -> None:
        self.db = db

    def execute_raw_sql(
        self, sql: str, params: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        result = self.db.execute(text(sql), params or {})
        if result.returns_rows:
            return [dict(row._mapping) for row in result]
        return []

    def count_tasks_by_status(self) -> List[Dict[str, Any]]:
        sql = """
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
        """
        return self.execute_raw_sql(sql)

    def get_recent_tasks(self, limit: int = 10) -> List[Dict[str, Any]]:
        sql = """
            SELECT task_id, query, agent_type, status, created_at
            FROM tasks
            ORDER BY created_at DESC
            LIMIT :limit
        """
        return self.execute_raw_sql(sql, {"limit": limit})
