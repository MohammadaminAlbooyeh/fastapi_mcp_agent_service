from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.mcp_tools.base import BaseTool


class DatabaseTool(BaseTool):
    name: str = "database_tool"
    description: str = "Execute database queries and CRUD operations"

    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        ...

    async def insert_record(
        self, table: str, data: Dict[str, Any]
    ) -> Optional[int]:
        ...

    async def update_record(
        self, table: str, record_id: int, data: Dict[str, Any]
    ) -> bool:
        ...

    async def delete_record(self, table: str, record_id: int) -> bool:
        ...

    async def list_records(
        self, table: str, filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        ...

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        if action == "query":
            result = await self.execute_query(kwargs.get("sql", ""))
        elif action == "insert":
            result = await self.insert_record(
                kwargs.get("table", ""), kwargs.get("data", {})
            )
        elif action == "update":
            result = await self.update_record(
                kwargs.get("table", ""),
                kwargs.get("id", 0),
                kwargs.get("data", {}),
            )
        elif action == "delete":
            result = await self.delete_record(
                kwargs.get("table", ""), kwargs.get("id", 0)
            )
        elif action == "list":
            result = await self.list_records(
                kwargs.get("table", ""), kwargs.get("filters")
            )
        else:
            result = {"error": f"Unknown action: {action}"}
        return {"tool": self.name, "action": action, "result": result}
