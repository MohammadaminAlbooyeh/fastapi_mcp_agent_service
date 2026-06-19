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

        class _AsyncTextStream:
            def __init__(self):
                self.tokens = ["Hello", " ", "World"]
                self.idx = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.idx >= len(self.tokens):
                    raise StopAsyncIteration
                val = self.tokens[self.idx]
                self.idx += 1
                return val

        class _AsyncStreamContext:
            def __init__(self):
                self.text_stream = _AsyncTextStream()

            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                pass

        mock_messages = MagicMock()
        mock_messages.stream = MagicMock(return_value=_AsyncStreamContext())

        mock_client = MagicMock()
        mock_client.messages = mock_messages

        monkeypatch.setattr(self.service, "_get_anthropic", AsyncMock(return_value=mock_client))

        chunks = []
        async for chunk in self.service.stream_generate("Say hello"):
            chunks.append(chunk)
        assert "".join(chunks) == "Hello World"

    @pytest.mark.asyncio
    async def test_openai_stream(self, monkeypatch) -> None:
        monkeypatch.setattr("src.services.llm_service.settings.anthropic_api_key", "")
        monkeypatch.setattr("src.services.llm_service.settings.openai_api_key", "sk-test")

        class _AsyncChunkStream:
            def __init__(self):
                self.chunks = []
                mock_delta = MagicMock()
                mock_delta.content = "Hello"
                mock_choice = MagicMock()
                mock_choice.delta = mock_delta
                c1 = MagicMock()
                c1.choices = [mock_choice]
                self.chunks.append(c1)
                self.idx = 0

            def __aiter__(self):
                return self

            async def __anext__(self):
                if self.idx >= len(self.chunks):
                    raise StopAsyncIteration
                val = self.chunks[self.idx]
                self.idx += 1
                return val

        mock_chat = MagicMock()
        mock_chat.completions = MagicMock()
        mock_chat.completions.create = AsyncMock(return_value=_AsyncChunkStream())

        mock_client = MagicMock()
        mock_client.chat = mock_chat

        monkeypatch.setattr(self.service, "_get_openai", AsyncMock(return_value=mock_client))

        chunks = []
        async for chunk in self.service.stream_generate("Say hello"):
            chunks.append(chunk)
        assert len(chunks) > 0
