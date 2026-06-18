from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from src.mcp_tools.base import BaseTool


class APITool(BaseTool):
    name: str = "api_tool"
    description: str = "External API calls (REST, GraphQL)"

    async def http_request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, json=body)
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            }

    async def call_rest_api(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            return {
                "status_code": response.status_code,
                "body": response.text,
            }

    async def call_graphql(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post("", json=payload)
            return {
                "status_code": response.status_code,
                "body": response.text,
            }

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        try:
            if action == "http_request":
                result = await self.http_request(
                    kwargs.get("method", "GET"),
                    kwargs.get("url", ""),
                    kwargs.get("headers"),
                    kwargs.get("body"),
                )
            elif action == "rest_api":
                result = await self.call_rest_api(kwargs.get("endpoint", ""), kwargs.get("params"))
            elif action == "graphql":
                result = await self.call_graphql(kwargs.get("query", ""), kwargs.get("variables"))
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
