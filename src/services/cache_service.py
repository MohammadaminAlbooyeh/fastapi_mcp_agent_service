from __future__ import annotations

from typing import Any, Dict, Optional


class CacheService:
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    async def cache_result(
        self, key: str, value: Any, ttl: int = 300
    ) -> bool:
        self._cache[key] = value
        return True

    async def get_cached(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    async def invalidate_cache(self, pattern: str) -> bool:
        keys_to_delete = [k for k in self._cache if pattern in k]
        for k in keys_to_delete:
            del self._cache[k]
        return True


cache_service = CacheService()
