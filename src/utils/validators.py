from __future__ import annotations

from typing import Any, Dict, List


def validate_agent_type(agent_type: str) -> bool:
    return agent_type in {"query", "processor", "research"}


def validate_tools(tools: List[str], available: List[str]) -> bool:
    return all(tool in available for tool in tools)


def validate_query(query: str) -> bool:
    return bool(query and len(query.strip()) > 0)
