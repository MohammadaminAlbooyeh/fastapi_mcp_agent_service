from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.logger import logger
from src.config.settings import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._local: Dict[str, List[float]] = defaultdict(list)
        self._redis: Optional["Redis"] = None
        self._redis_available: Optional[bool] = None

    async def _check_redis(self) -> bool:
        if self._redis_available is not None:
            return self._redis_available
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(
                settings.redis_url, decode_responses=True, socket_connect_timeout=1
            )
            await client.ping()
            self._redis = client
            self._redis_available = True
        except Exception as e:
            self._redis = None
            self._redis_available = False
            logger.warning(
                "Rate limiter could not connect to Redis (%s); falling back to "
                "in-memory, per-process rate limiting. This is NOT safe across "
                "multiple workers/instances — each process will enforce its own "
                "independent limit, effectively multiplying the allowed request rate.",
                e,
            )
        return self._redis_available

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = int(now - self.window_seconds)

        if await self._check_redis():
            try:
                key = f"ratelimit:{client_ip}"
                await self._redis.zremrangebyscore(key, 0, window_start)
                count = await self._redis.zcard(key)
                if count is not None and count >= self.max_requests:
                    return JSONResponse(
                        status_code=429,
                        content={
                            "detail": "Too many requests",
                            "retry_after": self.window_seconds,
                        },
                    )
                await self._redis.zadd(key, {str(now): now})
                await self._redis.expire(key, self.window_seconds * 2)
            except Exception as e:
                self._redis_available = False
                logger.warning(
                    "Rate limiter lost its Redis connection mid-request (%s); "
                    "falling back to in-memory, per-process rate limiting, which "
                    "is not consistent across multiple workers/instances.",
                    e,
                )
                return await call_next(request)
            return await call_next(request)

        timestamps = self._local[client_ip]
        self._local[client_ip] = [t for t in timestamps if t > window_start]
        if len(self._local[client_ip]) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests",
                    "retry_after": self.window_seconds,
                },
            )
        self._local[client_ip].append(now)
        return await call_next(request)
