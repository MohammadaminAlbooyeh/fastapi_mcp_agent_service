from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from src.database.connection import SessionLocal
from src.mcp_tools.base import BaseTool


class DatabaseTool(BaseTool):
    name: str = "database_tool"
    description: str = "Execute database queries and CRUD operations"

    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        def _run() -> list[dict[str, Any]]:
            db = SessionLocal()
            try:
                result = db.execute(text(sql), params or {})
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
            finally:
                db.close()
        return await asyncio.to_thread(_run)

    async def insert_record(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        def _run() -> Optional[int]:
            db = SessionLocal()
            try:
                columns = ", ".join(data.keys())
                placeholders = ", ".join(f":{k}" for k in data)
                sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
                result = db.execute(text(sql), data)
                db.commit()
                row = result.fetchone()
                return row[0] if row else None
            finally:
                db.close()
        return await asyncio.to_thread(_run)

    async def update_record(self, table: str, record_id: int, data: Dict[str, Any]) -> bool:
        def _run() -> bool:
            db = SessionLocal()
            try:
                sets = ", ".join(f"{k} = :{k}" for k in data)
                data["record_id"] = record_id
                sql = f"UPDATE {table} SET {sets} WHERE id = :record_id"
                result = db.execute(text(sql), data)
                db.commit()
                return result.rowcount > 0
            finally:
                db.close()
        return await asyncio.to_thread(_run)

    async def delete_record(self, table: str, record_id: int) -> bool:
        def _run() -> bool:
            db = SessionLocal()
            try:
                sql = f"DELETE FROM {table} WHERE id = :record_id"
                result = db.execute(text(sql), {"record_id": record_id})
                db.commit()
                return result.rowcount > 0
            finally:
                db.close()
        return await asyncio.to_thread(_run)

    async def list_records(self, table: str, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        def _run() -> List[Dict[str, Any]]:
            db = SessionLocal()
            try:
                if filters:
                    conditions = " AND ".join(f"{k} = :{k}" for k in filters)
                    sql = f"SELECT * FROM {table} WHERE {conditions}"
                    result = db.execute(text(sql), filters)
                else:
                    sql = f"SELECT * FROM {table}"
                    result = db.execute(text(sql))
                if result.returns_rows:
                    return [dict(row._mapping) for row in result]
                return []
            finally:
                db.close()
        return await asyncio.to_thread(_run)

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        try:
            if action == "query":
                result = await self.execute_query(kwargs.get("sql", ""), kwargs.get("params"))
            elif action == "insert":
                result = await self.insert_record(kwargs.get("table", ""), kwargs.get("data", {}))
            elif action == "update":
                result = await self.update_record(kwargs.get("table", ""), kwargs.get("id", 0), kwargs.get("data", {}))
            elif action == "delete":
                result = await self.delete_record(kwargs.get("table", ""), kwargs.get("id", 0))
            elif action == "list":
                result = await self.list_records(kwargs.get("table", ""), kwargs.get("filters"))
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
