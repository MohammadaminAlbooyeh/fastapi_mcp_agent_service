from __future__ import annotations

import asyncio
import ipaddress
import socket
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import httpx

from src.mcp_tools.base import BaseTool

_ALLOWED_SCHEMES = {"http", "https"}


async def _ensure_safe_url(url: str) -> None:
    """Blocks SSRF: rejects non-http(s) schemes and any hostname that resolves
    to a private, loopback, link-local, or otherwise reserved address (this
    also covers cloud metadata endpoints such as 169.254.169.254)."""
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme must be http or https, got: {parsed.scheme!r}")
    if not parsed.hostname:
        raise ValueError(f"URL has no hostname: {url!r}")

    def _resolve() -> list:
        return socket.getaddrinfo(parsed.hostname, None)

    try:
        addr_info = await asyncio.to_thread(_resolve)
    except socket.gaierror as e:
        raise ValueError(f"Could not resolve host {parsed.hostname!r}: {e}")

    for family, _, _, _, sockaddr in addr_info:
        ip = ipaddress.ip_address(sockaddr[0])
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            raise ValueError(f"Access to internal/private address is not allowed: {ip}")


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
        await _ensure_safe_url(url)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, json=body)
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": response.text,
            }

    async def call_rest_api(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await _ensure_safe_url(endpoint)
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(endpoint, params=params)
            return {
                "status_code": response.status_code,
                "body": response.text,
            }

    async def call_graphql(
        self, endpoint: str, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        await _ensure_safe_url(endpoint)
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(endpoint, json=payload)
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
                result = await self.call_rest_api(
                    kwargs.get("endpoint", ""), kwargs.get("params")
                )
            elif action == "graphql":
                result = await self.call_graphql(
                    kwargs.get("endpoint", ""),
                    kwargs.get("query", ""),
                    kwargs.get("variables"),
                )
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
