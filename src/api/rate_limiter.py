from __future__ import annotations

import time
from typing import TYPE_CHECKING, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.logger import logger
from src.config.settings import settings

if TYPE_CHECKING:
    from redis.asyncio import Redis


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window rate limiter backed solely by Redis, keyed by client IP.

    Redis is the only counter — there is no per-process fallback, since each
    container enforcing its own independent limit would effectively multiply
    the allowed request rate once the service runs as more than one
    instance. If Redis is unreachable, requests are allowed through (fail
    open) rather than rate-limited locally, since failing closed would take
    the whole API down on a transient Redis blip.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._redis: Optional["Redis"] = None

    async def _get_redis(self) -> Optional["Redis"]:
        if self._redis is not None:
            return self._redis
        try:
            import redis.asyncio as aioredis

            client = aioredis.from_url(
                settings.redis_url, decode_responses=True, socket_connect_timeout=1
            )
            await client.ping()
            self._redis = client
        except Exception as e:
            logger.warning(
                "Rate limiter could not connect to Redis (%s); failing open "
                "(requests will not be rate-limited) until Redis is reachable "
                "again.",
                e,
            )
            return None
        return self._redis

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = int(now - self.window_seconds)

        redis = await self._get_redis()
        if redis is None:
            return await call_next(request)

        try:
            key = f"ratelimit:{client_ip}"
            await redis.zremrangebyscore(key, 0, window_start)
            count = await redis.zcard(key)
            if count is not None and count >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": "Too many requests",
                        "retry_after": self.window_seconds,
                    },
                )
            await redis.zadd(key, {str(now): now})
            await redis.expire(key, self.window_seconds * 2)
        except Exception as e:
            self._redis = None
            logger.warning(
                "Rate limiter lost its Redis connection mid-request (%s); "
                "failing open for this request.",
                e,
            )
            return await call_next(request)

        return await call_next(request)
