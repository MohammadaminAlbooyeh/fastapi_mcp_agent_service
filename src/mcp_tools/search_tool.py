from __future__ import annotations

from typing import Any, Dict, List

import httpx

from src.config.settings import settings
from src.mcp_tools.base import BaseTool


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = "Web search and semantic search operations"

    async def web_search(self, query: str) -> List[Dict[str, Any]]:
        params = {"q": query, "format": "json"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get("https://duckduckgo.com/html/", params=params)
            response.raise_for_status()
            return [{"query": query, "status_code": response.status_code}]

    async def semantic_search(self, query: str, index: str) -> List[Dict[str, Any]]:
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(input=query, model="text-embedding-3-small")
            return [{"query": query, "index": index, "embedding_dim": len(response.data[0].embedding), "note": "Vector storage requires pgvector or similar"}]
        return [{"query": query, "index": index, "note": "Set OPENAI_API_KEY for embeddings"}]

    async def similarity_search(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if settings.openai_api_key:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.embeddings.create(input=text, model="text-embedding-3-small")
            return [{"text": text, "top_k": top_k, "embedding_dim": len(response.data[0].embedding), "note": "Vector storage requires pgvector or similar"}]
        return [{"text": text, "top_k": top_k, "note": "Set OPENAI_API_KEY for embeddings"}]

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        try:
            if action == "web_search":
                result = await self.web_search(kwargs.get("query", ""))
            elif action == "semantic_search":
                result = await self.semantic_search(kwargs.get("query", ""), kwargs.get("index", ""))
            elif action == "similarity_search":
                result = await self.similarity_search(kwargs.get("text", ""), kwargs.get("top_k", 5))
            else:
                return {"tool": self.name, "error": f"Unknown action: {action}"}
            return {"tool": self.name, "action": action, "result": result}
        except Exception as e:
            return {"tool": self.name, "action": action, "error": str(e)}
