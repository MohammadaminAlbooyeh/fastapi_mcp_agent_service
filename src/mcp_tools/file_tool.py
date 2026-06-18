from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List

from src.mcp_tools.base import BaseTool


class FileTool(BaseTool):
    name: str = "file_tool"
    description: str = "File system operations (read, write, list, delete)"

    ALLOWED_BASE = Path.cwd()

    async def read_file(self, path: str) -> str:
        full_path = self._resolve(path)
        return await asyncio.to_thread(full_path.read_text, encoding="utf-8")

    async def write_file(self, path: str, content: str) -> bool:
        full_path = self._resolve(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(full_path.write_text, content, encoding="utf-8")
        return True

    async def list_files(self, directory: str) -> List[str]:
        full_path = self._resolve(directory)
        if not full_path.is_dir():
            return []
        entries: List[str] = await asyncio.to_thread(
            lambda: [str(p.relative_to(self.ALLOWED_BASE)) for p in sorted(full_path.iterdir())]
        )
        return entries

    async def delete_file(self, path: str) -> bool:
        full_path = self._resolve(path)
        if not full_path.exists():
            return False
        await asyncio.to_thread(full_path.unlink)
        return True

    async def file_exists(self, path: str) -> bool:
        full_path = self._resolve(path)
        exists: bool = await asyncio.to_thread(full_path.exists)
        return exists

    def _resolve(self, path: str) -> Path:
        full = (self.ALLOWED_BASE / path).resolve()
        if not str(full).startswith(str(self.ALLOWED_BASE.resolve())):
            raise PermissionError(f"Access denied: {path} is outside allowed directory")
        return full

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        try:
            if action == "read":
                result = await self.read_file(kwargs.get("path", ""))
            elif action == "write":
                result = await self.write_file(kwargs.get("path", ""), kwargs.get("content", ""))
            elif action == "list":
                result = await self.list_files(kwargs.get("directory", ""))
            elif action == "delete":
                result = await self.delete_file(kwargs.get("path", ""))
            elif action == "exists":
                result = await self.file_exists(kwargs.get("path", ""))
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except PermissionError as e:
            return {"tool": self.name, "action": action, "error": str(e)}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
