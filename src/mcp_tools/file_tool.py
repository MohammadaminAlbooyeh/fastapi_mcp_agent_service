from __future__ import annotations

import posixpath
from typing import Any, Dict, List, Optional

from src.config.settings import settings
from src.mcp_tools.base import BaseTool
from src.utils.s3_client import get_s3_client


class FileTool(BaseTool):
    name: str = "file_tool"
    description: str = "File operations (read, write, list, delete) backed by S3"

    def _resolve_key(self, path: str, user_id: Optional[str]) -> str:
        """Namespaces every key under the requesting user, replacing the old
        local-path-traversal check with S3-key-based authorization: a key is
        only valid if it belongs to the caller's own `users/{user_id}/`
        prefix, regardless of what `path` looks like."""
        if not user_id:
            raise PermissionError("file_tool requires an authenticated user_id")

        prefix = f"users/{user_id}/"
        normalized = posixpath.normpath(path.lstrip("/"))
        if normalized in (".", ""):
            return prefix
        if normalized.startswith(".."):
            raise PermissionError(
                f"Access denied: {path!r} escapes the user's namespace"
            )

        key = prefix + normalized
        if not key.startswith(prefix):
            raise PermissionError(
                f"Access denied: {path!r} escapes the user's namespace"
            )
        return key

    async def read_file(self, path: str, user_id: Optional[str]) -> str:
        key = self._resolve_key(path, user_id)
        async with get_s3_client() as client:
            response = await client.get_object(Bucket=settings.s3_bucket_name, Key=key)
            body = await response["Body"].read()
            return body.decode("utf-8")

    async def write_file(self, path: str, content: str, user_id: Optional[str]) -> bool:
        key = self._resolve_key(path, user_id)
        async with get_s3_client() as client:
            await client.put_object(
                Bucket=settings.s3_bucket_name,
                Key=key,
                Body=content.encode("utf-8"),
            )
        return True

    async def list_files(self, directory: str, user_id: Optional[str]) -> List[str]:
        prefix = self._resolve_key(directory, user_id)
        if not prefix.endswith("/"):
            prefix += "/"
        owner_prefix = f"users/{user_id}/"

        entries: List[str] = []
        async with get_s3_client() as client:
            paginator = client.get_paginator("list_objects_v2")
            async for page in paginator.paginate(
                Bucket=settings.s3_bucket_name, Prefix=prefix
            ):
                for obj in page.get("Contents", []):
                    entries.append(obj["Key"][len(owner_prefix) :])
        return sorted(entries)

    async def delete_file(self, path: str, user_id: Optional[str]) -> bool:
        key = self._resolve_key(path, user_id)
        async with get_s3_client() as client:
            try:
                await client.head_object(Bucket=settings.s3_bucket_name, Key=key)
            except Exception:
                return False
            await client.delete_object(Bucket=settings.s3_bucket_name, Key=key)
        return True

    async def file_exists(self, path: str, user_id: Optional[str]) -> bool:
        key = self._resolve_key(path, user_id)
        async with get_s3_client() as client:
            try:
                await client.head_object(Bucket=settings.s3_bucket_name, Key=key)
                return True
            except Exception:
                return False

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        user_id = kwargs.get("user_id")
        try:
            if action == "read":
                result = await self.read_file(kwargs.get("path", ""), user_id)
            elif action == "write":
                result = await self.write_file(
                    kwargs.get("path", ""), kwargs.get("content", ""), user_id
                )
            elif action == "list":
                result = await self.list_files(kwargs.get("directory", ""), user_id)
            elif action == "delete":
                result = await self.delete_file(kwargs.get("path", ""), user_id)
            elif action == "exists":
                result = await self.file_exists(kwargs.get("path", ""), user_id)
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except PermissionError as e:
            return {"tool": self.name, "action": action, "error": str(e)}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
