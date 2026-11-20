from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from src.api.rate_limiter import RateLimitMiddleware


def _make_request(ip: str = "1.2.3.4"):
    return SimpleNamespace(client=SimpleNamespace(host=ip))


class TestRateLimitMiddleware:
    def setup_method(self) -> None:
        self.middleware = RateLimitMiddleware(
            app=AsyncMock(), max_requests=2, window_seconds=60
        )

    @pytest.mark.asyncio
    async def test_fails_open_when_redis_unreachable(self, monkeypatch) -> None:
        monkeypatch.setattr(self.middleware, "_get_redis", AsyncMock(return_value=None))
        call_next = AsyncMock(return_value="ok")

        response = await self.middleware.dispatch(_make_request(), call_next)

        assert response == "ok"
        call_next.assert_awaited_once()
        # No per-process fallback counter exists on the middleware at all.
        assert not hasattr(self.middleware, "_local")

    @pytest.mark.asyncio
    async def test_allows_requests_under_the_limit(self, monkeypatch) -> None:
        redis = AsyncMock()
        redis.zremrangebyscore.return_value = None
        redis.zcard.return_value = 0
        monkeypatch.setattr(
            self.middleware, "_get_redis", AsyncMock(return_value=redis)
        )
        call_next = AsyncMock(return_value="ok")

        response = await self.middleware.dispatch(_make_request(), call_next)

        assert response == "ok"
        redis.zadd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_blocks_requests_over_the_limit(self, monkeypatch) -> None:
        redis = AsyncMock()
        redis.zremrangebyscore.return_value = None
        redis.zcard.return_value = 2
        monkeypatch.setattr(
            self.middleware, "_get_redis", AsyncMock(return_value=redis)
        )
        call_next = AsyncMock(return_value="ok")

        response = await self.middleware.dispatch(_make_request(), call_next)

        assert response.status_code == 429
        call_next.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_fails_open_when_redis_errors_mid_request(self, monkeypatch) -> None:
        redis = AsyncMock()
        redis.zremrangebyscore.side_effect = Exception("connection reset")
        monkeypatch.setattr(
            self.middleware, "_get_redis", AsyncMock(return_value=redis)
        )
        call_next = AsyncMock(return_value="ok")

        response = await self.middleware.dispatch(_make_request(), call_next)

        assert response == "ok"
        call_next.assert_awaited_once()
