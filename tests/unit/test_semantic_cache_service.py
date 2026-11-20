from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.config.settings import settings
from src.services.semantic_cache_service import SemanticCacheService, _cosine_similarity


class TestCosineSimilarity:
    def test_identical_vectors_score_one(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)

    def test_orthogonal_vectors_score_zero(self) -> None:
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_zero_vector_is_handled(self) -> None:
        assert _cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


class TestSemanticCacheService:
    def setup_method(self) -> None:
        self.service = SemanticCacheService()

    @pytest.mark.asyncio
    async def test_disabled_without_openai_key(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "")
        result = await self.service.get_similar("query", "hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_hit_above_threshold(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "sk-test")
        monkeypatch.setattr(settings, "semantic_cache_threshold", 0.99)
        monkeypatch.setattr(self.service, "embed", AsyncMock(return_value=[1.0, 0.0]))
        monkeypatch.setattr(
            "src.services.semantic_cache_service.cache_service.get_cached",
            AsyncMock(
                return_value=[{"embedding": [1.0, 0.0], "response": "cached answer"}]
            ),
        )
        result = await self.service.get_similar("query", "hello")
        assert result == "cached answer"

    @pytest.mark.asyncio
    async def test_miss_below_threshold(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "sk-test")
        monkeypatch.setattr(settings, "semantic_cache_threshold", 0.99)
        monkeypatch.setattr(self.service, "embed", AsyncMock(return_value=[1.0, 0.0]))
        monkeypatch.setattr(
            "src.services.semantic_cache_service.cache_service.get_cached",
            AsyncMock(
                return_value=[{"embedding": [0.0, 1.0], "response": "unrelated answer"}]
            ),
        )
        result = await self.service.get_similar("query", "hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_store_appends_and_caps_size(self, monkeypatch) -> None:
        monkeypatch.setattr(settings, "openai_api_key", "sk-test")
        monkeypatch.setattr(settings, "semantic_cache_size", 2)
        monkeypatch.setattr(self.service, "embed", AsyncMock(return_value=[1.0, 0.0]))
        monkeypatch.setattr(
            "src.services.semantic_cache_service.cache_service.get_cached",
            AsyncMock(
                return_value=[
                    {"embedding": [0.1, 0.1], "response": "old-1"},
                    {"embedding": [0.2, 0.2], "response": "old-2"},
                ]
            ),
        )
        mock_cache_result = AsyncMock(return_value=True)
        monkeypatch.setattr(
            "src.services.semantic_cache_service.cache_service.cache_result",
            mock_cache_result,
        )

        await self.service.store("query", "hello", "new answer")

        stored_entries = mock_cache_result.call_args.args[1]
        assert len(stored_entries) == 2
        assert stored_entries[-1]["response"] == "new answer"
