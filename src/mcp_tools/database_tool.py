from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from src.database.connection import SessionLocal
from src.database.models import Base
from src.mcp_tools.base import BaseTool

# Only SELECT statements are allowed through the raw "query" action.
_SELECT_ONLY_RE = re.compile(r"^\s*SELECT\b", re.IGNORECASE)
_MULTI_STATEMENT_RE = re.compile(r";\s*\S")


def _allowed_tables() -> Dict[str, set]:
    return {name: set(table.columns.keys()) for name, table in Base.metadata.tables.items()}


def _validate_table(table: str) -> set:
    tables = _allowed_tables()
    if table not in tables:
        raise ValueError(f"Unknown or disallowed table: {table!r}")
    return tables[table]


def _validate_columns(table: str, columns: Any, allowed_columns: set) -> None:
    for column in columns:
        if column not in allowed_columns:
            raise ValueError(f"Unknown or disallowed column {column!r} for table {table!r}")


class DatabaseTool(BaseTool):
    name: str = "database_tool"
    description: str = "Execute database queries and CRUD operations"

    async def execute_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not _SELECT_ONLY_RE.match(sql) or _MULTI_STATEMENT_RE.search(sql):
            raise ValueError("Only single SELECT statements are allowed for the 'query' action")

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
        allowed_columns = _validate_table(table)
        _validate_columns(table, data.keys(), allowed_columns)

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
        allowed_columns = _validate_table(table)
        _validate_columns(table, data.keys(), allowed_columns)

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
        _validate_table(table)

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
        allowed_columns = _validate_table(table)
        if filters:
            _validate_columns(table, filters.keys(), allowed_columns)

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

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": "Execute database queries and CRUD operations. Use 'query' for custom SQL, 'list' for reading tables, 'insert', 'update', and 'delete' for modifications.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["query", "insert", "update", "delete", "list"],
                        "description": "The database operation to perform."
                    },
                    "sql": {
                        "type": "string",
                        "description": "SQL query to execute (used only with 'query' action)."
                    },
                    "table": {
                        "type": "string",
                        "description": "Table name (used with list, insert, update, delete)."
                    },
                    "data": {
                        "type": "object",
                        "description": "Record data for insert/update."
                    },
                    "id": {
                        "type": "integer",
                        "description": "Record ID for update/delete."
                    },
                    "filters": {
                        "type": "object",
                        "description": "Key-value filters for list action."
                    }
                },
                "required": ["action"]
            }
        }
