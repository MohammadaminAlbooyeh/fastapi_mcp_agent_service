from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.services.cache_service import cache_service


class ConversationMemory:
    def __init__(self, session_id: str, max_history: int = 20):
        self.session_id = session_id
        self.max_history = max_history

    def _memory_key(self) -> str:
        return f"memory:{self.session_id}"

    async def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        messages = await self.get_history()
        messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {},
        })
        if len(messages) > self.max_history:
            messages = messages[-self.max_history:]
        await cache_service.cache_result(self._memory_key(), messages, ttl=86400)

    async def get_history(self) -> List[Dict[str, Any]]:
        cached = await cache_service.get_cached(self._memory_key())
        return cached if cached else []

    async def clear(self) -> None:
        await cache_service.invalidate_cache(self._memory_key())

    async def get_summary(self) -> Dict[str, Any]:
        history = await self.get_history()
        return {
            "session_id": self.session_id,
            "message_count": len(history),
            "last_interaction": history[-1]["timestamp"] if history else None,
        }


class AgentMemoryManager:
    def __init__(self):
        self._sessions: Dict[str, ConversationMemory] = {}

    def get_session(self, session_id: str) -> ConversationMemory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ConversationMemory(session_id)
        return self._sessions[session_id]

    async def store_agent_result(
        self, session_id: str, agent_type: str, query: str, result: Dict[str, Any]
    ) -> None:
        memory = self.get_session(session_id)
        await memory.add_message(
            role="user",
            content=query,
            metadata={"agent_type": agent_type},
        )
        await memory.add_message(
            role="assistant",
            content=str(result.get("result", result.get("llm_response", ""))),
            metadata={"agent_type": agent_type, "status": result.get("status", "completed")},
        )


agent_memory_manager = AgentMemoryManager()
