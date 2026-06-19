from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.llm_service import LLMService


class TestLLMService:
    def setup_method(self) -> None:
        self.service = LLMService()

    def test_no_provider_configured(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "")
        assert self.service._provider is None

    @pytest.mark.asyncio
    async def test_generate_no_provider(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "")
        result = await self.service.generate("Hello")
        assert "LLM not configured" in result

    @pytest.mark.asyncio
    async def test_stream_generate_no_provider(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "")
        chunks = []
        async for chunk in self.service.stream_generate("Hello"):
            chunks.append(chunk)
        assert len(chunks) == 1
        assert "LLM not configured" in chunks[0]

    @pytest.mark.asyncio
    async def test_anthropic_generate(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "sk-test")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "")

        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="Hello from Claude")]
        mock_client = AsyncMock()
        mock_client.messages.create.return_value = mock_message

        monkeypatch.setattr(self.service, "_get_anthropic", AsyncMock(return_value=mock_client))

        result = await self.service.generate("Say hello")
        assert result == "Hello from Claude"

    @pytest.mark.asyncio
    async def test_openai_generate(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "sk-test")

        mock_choice = MagicMock()
        mock_choice.message.content = "Hello from GPT"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client = AsyncMock()
        mock_client.chat.completions.create.return_value = mock_response

        monkeypatch.setattr(self.service, "_get_openai", AsyncMock(return_value=mock_client))

        result = await self.service.generate("Say hello", system_prompt="Be nice")
        assert result == "Hello from GPT"

    @pytest.mark.asyncio
    async def test_anthropic_stream(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "sk-test")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "")

        mock_stream = AsyncMock()
        mock_stream.text_stream = AsyncMock()
        mock_stream.text_stream.__aiter__.return_value = AsyncMock()
        mock_stream.text_stream.__anext__ = AsyncMock(side_effect=["Hello", " ", "World"])

        mock_client = AsyncMock()
        mock_client.messages.stream.return_value.__aenter__.return_value = mock_stream

        monkeypatch.setattr(self.service, "_get_anthropic", AsyncMock(return_value=mock_client))

        chunks = []
        async for chunk in self.service.stream_generate("Say hello"):
            chunks.append(chunk)
        assert "".join(chunks) == "Hello World"
