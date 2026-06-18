from __future__ import annotations

import json
from datetime import timedelta
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from src.config.settings import settings


class CacheService:
    def __init__(self) -> None:
        self._client: Optional[aioredis.Redis] = None
        self._local: Dict[str, Any] = {}

    async def _get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_url,
                decode_responses=True,
            )
        return self._client

    async def cache_result(self, key: str, value: Any, ttl: int = 300) -> bool:
        try:
            client = await self._get_client()
            serialized = json.dumps(value, default=str)
            await client.setex(key, timedelta(seconds=ttl), serialized)
            return True
        except Exception:
            self._local[key] = value
            return True

    async def get_cached(self, key: str) -> Optional[Any]:
        try:
            client = await self._get_client()
            data = await client.get(key)
            if data is not None:
                return json.loads(data)
            return None
        except Exception:
            return self._local.get(key)

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
        except Exception:
            keys_to_delete = [k for k in self._local if pattern in k]
            for k in keys_to_delete:
                del self._local[k]
            return True

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None


cache_service = CacheService()
