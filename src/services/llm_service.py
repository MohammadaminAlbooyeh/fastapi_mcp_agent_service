from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, Optional

from src.config.settings import settings


class LLMService:
    def __init__(self) -> None:
        self.model = settings.llm_model
        self._anthropic_client: Any = None
        self._openai_client: Any = None

    @property
    def _provider(self) -> Optional[str]:
        if settings.anthropic_api_key:
            return "anthropic"
        if settings.openai_api_key:
            return "openai"
        return None

    async def _get_anthropic(self) -> Any:
        if self._anthropic_client is None:
            from anthropic import AsyncAnthropic
            self._anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        return self._anthropic_client

    async def _get_openai(self) -> Any:
        if self._openai_client is None:
            from openai import AsyncOpenAI
            self._openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        return self._openai_client

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        provider = self._provider
        if provider == "anthropic":
            return await self._anthropic_generate(prompt, system_prompt)
        if provider == "openai":
            return await self._openai_generate(prompt, system_prompt)
        return f"[LLM not configured — set ANTHROPIC_API_KEY or OPENAI_API_KEY]\n\nPrompt: {prompt}"

    async def stream_generate(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        provider = self._provider
        if provider == "anthropic":
            async for chunk in self._anthropic_stream(prompt, system_prompt):
                yield chunk
        elif provider == "openai":
            async for chunk in self._openai_stream(prompt, system_prompt):
                yield chunk
        else:
            yield f"[LLM not configured — set ANTHROPIC_API_KEY or OPENAI_API_KEY]\n\nPrompt: {prompt}"

    async def _anthropic_generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = await self._get_anthropic()
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        response = await client.messages.create(**kwargs)
        return response.content[0].text

    async def _openai_generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        client = await self._get_openai()
        messages: list[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content or ""

    async def _anthropic_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        client = await self._get_anthropic()
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            kwargs["system"] = system_prompt
        async with client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def _openai_stream(self, prompt: str, system_prompt: Optional[str] = None) -> AsyncGenerator[str, None]:
        client = await self._get_openai()
        messages: list[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        response = await client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
            stream=True,
        )
        async for chunk in response:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content


llm_service = LLMService()
