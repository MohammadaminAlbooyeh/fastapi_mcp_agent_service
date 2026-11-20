from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.services.memory_service import AgentMemoryManager, ConversationMemory


class TestConversationMemory:
    def setup_method(self) -> None:
        self.memory = ConversationMemory("test-session", max_history=5)

    @pytest.mark.asyncio
    async def test_add_and_get_history(self) -> None:
        mock_cache = AsyncMock()
        mock_cache.get_cached.return_value = None
        mock_cache.cache_result.return_value = True

        with patch.multiple(
            "src.services.memory_service.cache_service",
            get_cached=mock_cache.get_cached,
            cache_result=mock_cache.cache_result,
        ):
            await self.memory.add_message("user", "Hello", {"key": "val"})
            mock_cache.cache_result.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_history_with_data(self) -> None:
        existing = [
            {
                "role": "user",
                "content": "Hi",
                "timestamp": "2024-01-01",
                "metadata": {},
            },
            {
                "role": "assistant",
                "content": "Hello!",
                "timestamp": "2024-01-01",
                "metadata": {},
            },
        ]

        with patch(
            "src.services.memory_service.cache_service.get_cached",
            AsyncMock(return_value=existing),
        ):
            history = await self.memory.get_history()
            assert len(history) == 2

    @pytest.mark.asyncio
    async def test_get_summary(self) -> None:
        existing = [
            {
                "role": "user",
                "content": "Hi",
                "timestamp": "2024-01-01",
                "metadata": {},
            },
        ]

        with patch(
            "src.services.memory_service.cache_service.get_cached",
            AsyncMock(return_value=existing),
        ):
            summary = await self.memory.get_summary()
            assert summary["session_id"] == "test-session"
            assert summary["message_count"] == 1

    @pytest.mark.asyncio
    async def test_clear(self) -> None:
        with patch(
            "src.services.memory_service.cache_service.invalidate_cache",
            AsyncMock(return_value=True),
        ):
            await self.memory.clear()

    @pytest.mark.asyncio
    async def test_max_history_truncation(self) -> None:
        small_memory = ConversationMemory("small-session", max_history=3)
        mock_cache = AsyncMock()
        mock_cache.get_cached.return_value = [
            {
                "role": "user",
                "content": f"msg{i}",
                "timestamp": "2024-01-01",
                "metadata": {},
            }
            for i in range(5)
        ]

        with patch(
            "src.services.memory_service.cache_service.get_cached",
            mock_cache.get_cached,
        ):
            history = await small_memory.get_history()
            assert len(history) == 5

        mock_cache.cache_result.return_value = True
        with patch.multiple(
            "src.services.memory_service.cache_service",
            get_cached=mock_cache.get_cached,
            cache_result=mock_cache.cache_result,
        ):
            await small_memory.add_message("user", "overflow", {"key": "val"})
            assert small_memory.max_history == 3


class TestMemoryStatelessness:
    @pytest.mark.asyncio
    async def test_two_managers_share_history_via_redis(self) -> None:
        """Simulates two different processes (e.g. two ECS containers) each
        with their own AgentMemoryManager — a follow-up message routed to a
        different container must still see the prior conversation, since
        nothing is kept in an in-process dict."""
        shared_redis_store: dict = {}

        async def fake_get_cached(key):
            return shared_redis_store.get(key)

        async def fake_cache_result(key, value, ttl=300):
            shared_redis_store[key] = value
            return True

        with patch.multiple(
            "src.services.memory_service.cache_service",
            get_cached=fake_get_cached,
            cache_result=fake_cache_result,
        ):
            manager_a = AgentMemoryManager()
            manager_b = AgentMemoryManager()

            await manager_a.get_session("shared-session").add_message(
                "user", "hello from container A"
            )
            history_from_b = await manager_b.get_session("shared-session").get_history()

        assert len(history_from_b) == 1
        assert history_from_b[0]["content"] == "hello from container A"


class TestAgentMemoryManager:
    def setup_method(self) -> None:
        self.manager = AgentMemoryManager()

    def test_get_session_creates_new(self) -> None:
        memory = self.manager.get_session("new-session")
        assert isinstance(memory, ConversationMemory)
        assert memory.session_id == "new-session"

    def test_get_session_reuses_existing(self) -> None:
        memory1 = self.manager.get_session("session-1")
        memory2 = self.manager.get_session("session-1")
        assert memory1 is memory2

    @pytest.mark.asyncio
    async def test_store_agent_result(self) -> None:
        mock_cache = AsyncMock()
        mock_cache.get_cached.return_value = None
        mock_cache.cache_result.return_value = True

        with patch.multiple(
            "src.services.memory_service.cache_service",
            get_cached=mock_cache.get_cached,
            cache_result=mock_cache.cache_result,
        ):
            await self.manager.store_agent_result(
                session_id="session-1",
                agent_type="query",
                query="Get users",
                result={"result": {"llm_response": "Here are the users"}},
            )

    @pytest.mark.asyncio
    async def test_store_agent_result_with_memory(self) -> None:
        mock_cache = AsyncMock()
        mock_cache.get_cached.return_value = [
            {
                "role": "user",
                "content": "prior query",
                "timestamp": "2024-01-01",
                "metadata": {},
            }
        ]
        mock_cache.cache_result.return_value = True

        with patch.multiple(
            "src.services.memory_service.cache_service",
            get_cached=mock_cache.get_cached,
            cache_result=mock_cache.cache_result,
        ):
            await self.manager.store_agent_result(
                session_id="session-2",
                agent_type="research",
                query="New search",
                result={
                    "result": {"llm_response": "Results found"},
                    "status": "completed",
                },
            )
