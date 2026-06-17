from __future__ import annotations

from typing import Any, Dict, List

from src.mcp_tools.base import BaseTool


class FileTool(BaseTool):
    name: str = "file_tool"
    description: str = "File system operations (read, write, list, delete)"

    async def read_file(self, path: str) -> str:
        ...

    async def write_file(self, path: str, content: str) -> bool:
        ...

    async def list_files(self, directory: str) -> List[str]:
        ...

    async def delete_file(self, path: str) -> bool:
        ...

    async def file_exists(self, path: str) -> bool:
        ...

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        if action == "read":
            result = await self.read_file(kwargs.get("path", ""))
        elif action == "write":
            result = await self.write_file(
                kwargs.get("path", ""), kwargs.get("content", "")
            )
        elif action == "list":
            result = await self.list_files(kwargs.get("directory", ""))
        elif action == "delete":
            result = await self.delete_file(kwargs.get("path", ""))
        elif action == "exists":
            result = await self.file_exists(kwargs.get("path", ""))
        else:
            result = {"error": f"Unknown action: {action}"}
        return {"tool": self.name, "action": action, "result": result}
