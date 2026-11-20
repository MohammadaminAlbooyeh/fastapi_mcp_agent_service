from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

from src.config.logger import logger
from src.config.settings import settings
from src.services.cache_service import cache_service

EMBEDDING_MODEL = "text-embedding-3-small"


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCacheService:
    """Avoids redundant LLM calls for queries that are near-duplicates of
    one answered recently. Backed by a bounded, per-agent-type list of
    (embedding, response) pairs in Redis — a recent-queries cache, not a
    general-purpose vector index, so no new vector-DB infra is needed."""

    def __init__(self) -> None:
        self._openai_client: Any = None
        self._warned_disabled = False

    def _cache_key(self, agent_type: str) -> str:
        return f"semcache:{agent_type}"

    async def embed(self, text: str) -> Optional[List[float]]:
        if not settings.openai_api_key:
            if not self._warned_disabled:
                logger.warning("Semantic cache disabled: OPENAI_API_KEY is not set")
                self._warned_disabled = True
            return None
        try:
            if self._openai_client is None:
                from openai import AsyncOpenAI

                self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
            response = await self._openai_client.embeddings.create(
                model=EMBEDDING_MODEL, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Semantic cache embedding failed: {e}")
            return None

    async def get_similar(self, agent_type: str, query: str) -> Optional[str]:
        embedding = await self.embed(query)
        if embedding is None:
            return None

        entries: List[Dict[str, Any]] = (
            await cache_service.get_cached(self._cache_key(agent_type)) or []
        )
        best_score = 0.0
        best_response: Optional[str] = None
        for entry in entries:
            score = _cosine_similarity(embedding, entry["embedding"])
            if score > best_score:
                best_score = score
                best_response = entry["response"]

        if (
            best_response is not None
            and best_score >= settings.semantic_cache_threshold
        ):
            return best_response
        return None

    async def store(self, agent_type: str, query: str, response: str) -> None:
        embedding = await self.embed(query)
        if embedding is None:
            return

        key = self._cache_key(agent_type)
        entries: List[Dict[str, Any]] = await cache_service.get_cached(key) or []
        entries.append({"embedding": embedding, "response": response})
        entries = entries[-settings.semantic_cache_size :]
        await cache_service.cache_result(key, entries, ttl=3600)


semantic_cache_service = SemanticCacheService()
