from __future__ import annotations

import pytest

from src.utils.decorators import retry, timed


class TestDecorators:
    @pytest.mark.asyncio
    async def test_timed_async(self) -> None:
        @timed
        async def my_async_func():
            return 42

        result = await my_async_func()
        assert result == 42

    def test_timed_sync(self) -> None:
        @timed
        def my_sync_func():
            return "hello"

        result = my_sync_func()
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_retry_success_first_try(self) -> None:
        call_count = 0

        @retry(max_retries=3, delay=0.1)
        async def my_func():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await my_func()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_retry_success_after_retry(self) -> None:
        call_count = 0

        @retry(max_retries=3, delay=0.1)
        async def my_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary error")
            return "success"

        result = await my_func()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self) -> None:
        call_count = 0

        @retry(max_retries=2, delay=0.1)
        async def my_func():
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            await my_func()
        assert call_count == 2
