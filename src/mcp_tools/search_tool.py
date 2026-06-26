from __future__ import annotations

import math
import re
from typing import Any, Dict, List

import httpx

from src.config.settings import settings
from src.mcp_tools.base import BaseTool


class SearchTool(BaseTool):
    name: str = "search_tool"
    description: str = "Web search and semantic search operations"

    _vector_index: Dict[str, List[float]] = {}

    async def web_search(self, query: str) -> List[Dict[str, Any]]:
        results = []
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            response.raise_for_status()
            data = response.json()

            if data.get("AbstractText"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data.get("AbstractText", ""),
                    "source": data.get("AbstractSource", ""),
                    "url": data.get("AbstractURL", ""),
                })

            for topic in data.get("RelatedTopics", []):
                if "Topics" in topic:
                    for sub in topic["Topics"]:
                        results.append({
                            "title": sub.get("Text", "").split(" - ")[0],
                            "snippet": sub.get("Text", ""),
                            "url": sub.get("FirstURL", ""),
                        })
                else:
                    results.append({
                        "title": topic.get("Text", "").split(" - ")[0],
                        "snippet": topic.get("Text", ""),
                        "url": topic.get("FirstURL", ""),
                    })

        if not results:
            async with httpx.AsyncClient(timeout=15.0) as client:
                html_response = await client.get(
                    "https://lite.duckduckgo.com/lite/",
                    params={"q": query},
                )
                html_response.raise_for_status()
                snippets = re.findall(
                    r'<a[^>]*href="(https?://[^"]+)"[^>]*>(.*?)</a>',
                    html_response.text,
                )
                for url, title in snippets[:5]:
                    results.append({"title": title.strip(), "snippet": "", "url": url})

        return results if results else [{"query": query, "note": "No results found"}]

    async def semantic_search(self, query: str, index: str) -> List[Dict[str, Any]]:
        if not settings.openai_api_key:
            return [{"query": query, "index": index, "note": "Set OPENAI_API_KEY for embeddings"}]

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(input=query, model="text-embedding-3-small")
        embedding = response.data[0].embedding

        self._vector_index[f"{index}:{query}"] = embedding
        return [{
            "query": query,
            "index": index,
            "embedding_dim": len(embedding),
            "index_size": len(self._vector_index),
            "note": "Stored in in-memory vector index. Use similarity_search to query.",
        }]

    async def similarity_search(self, text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not settings.openai_api_key:
            return [{"text": text, "top_k": top_k, "note": "Set OPENAI_API_KEY for embeddings"}]

        if not self._vector_index:
            return [{"text": text, "top_k": top_k, "note": "No vectors in index. Add documents via semantic_search first."}]

        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.openai_api_key)
        response = await client.embeddings.create(input=text, model="text-embedding-3-small")
        query_embedding = response.data[0].embedding

        def cosine_similarity(a: List[float], b: List[float]) -> float:
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(y * y for y in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0

        scored = [
            (key, cosine_similarity(query_embedding, vec))
            for key, vec in self._vector_index.items()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        top = [{"key": k, "similarity": round(s, 4)} for k, s in scored[:top_k]]

        return [{"text": text, "top_k": top_k, "results": top}]

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
