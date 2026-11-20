from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Optional

import redis.asyncio as aioredis

from src.config.logger import logger
from src.config.settings import settings


class CacheService:
    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._client

    async def cache_result(self, key: str, value: Any, ttl: int = 300) -> bool:
        # Redis is the only cache backend. A per-container fallback would let
        # horizontally scaled instances return inconsistent cached results,
        # so on a Redis error we skip caching entirely rather than caching
        # locally.
        try:
            client = await self._get_client()
            serialized = json.dumps(value, default=str)
            await client.setex(key, timedelta(seconds=ttl), serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache write skipped (Redis unavailable): {e}")
            return False

    async def get_cached(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            data = await client.get(key)
            if data is not None:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache read skipped (Redis unavailable): {e}")
            return None

    async def invalidate_cache(self, pattern: str) -> bool:
        try:
            client = await self._get_client()
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor=cursor, match=pattern)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.warning(f"Cache invalidation skipped (Redis unavailable): {e}")
            return False

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


cache_service = CacheService()
