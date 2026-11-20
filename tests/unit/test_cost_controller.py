from __future__ import annotations

import pytest

from src.api.exceptions import TokenBudgetExceededError
from src.config.settings import settings
from src.services.cost_controller import CostController


class TestCostController:
    def setup_method(self) -> None:
        self.controller = CostController()

    def test_allows_small_prompt_within_budget(self) -> None:
        self.controller.check_budget("hello world", max_tokens=100)

    def test_blocks_prompt_exceeding_budget(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(settings, "max_tokens_per_request", 10)
        with pytest.raises(TokenBudgetExceededError):
            self.controller.check_budget(
                "this prompt is long enough to exceed it", max_tokens=10
            )

    def test_counts_tokens_without_tiktoken(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr("src.services.cost_controller._ENCODING", None)
        count = self.controller.count_tokens("abcd" * 10)
        assert count == len("abcd" * 10) // 4
