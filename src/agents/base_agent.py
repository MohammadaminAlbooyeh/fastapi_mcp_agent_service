from __future__ import annotations

from typing import Any, Dict, List, Optional


class BaseAgent:
    name: str = ""
    description: str = ""
    tools: List[str] = []

    async def execute(
        self, query: str, **kwargs: Any
    ) -> Dict[str, Any]:
        ...
