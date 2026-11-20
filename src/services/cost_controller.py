from __future__ import annotations

from src.api.exceptions import TokenBudgetExceededError
from src.config.logger import logger
from src.config.settings import settings

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("cl100k_base")
except Exception:  # pragma: no cover - exercised only if tiktoken is absent
    _ENCODING = None


class CostController:
    def count_tokens(self, text: str) -> int:
        if _ENCODING is not None:
            return len(_ENCODING.encode(text))
        # Rough fallback (~4 chars/token for English text) if tiktoken isn't
        # importable — good enough to stop a runaway request, not meant to
        # be billing-accurate.
        return len(text) // 4

    def check_budget(self, prompt: str, max_tokens: int) -> None:
        prompt_tokens = self.count_tokens(prompt)
        total = prompt_tokens + max_tokens
        if total > settings.max_tokens_per_request:
            logger.warning(
                f"Blocking LLM call: estimated {total} tokens "
                f"(prompt={prompt_tokens}, max_tokens={max_tokens}) exceeds "
                f"the per-request ceiling of {settings.max_tokens_per_request}"
            )
            raise TokenBudgetExceededError(
                f"Request would use ~{total} tokens, exceeding the "
                f"per-request limit of {settings.max_tokens_per_request}"
            )


cost_controller = CostController()
