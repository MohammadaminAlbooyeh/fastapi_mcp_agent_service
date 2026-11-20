from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List

from langgraph.graph import StateGraph

from src.api.exceptions import TokenBudgetExceededError
from src.config.logger import logger
from src.config.settings import settings
from src.services.llm_service import llm_service
from src.services.semantic_cache_service import semantic_cache_service


class BaseAgent:
    name: str = ""
    description: str = ""
    tools: List[str] = []

    SYSTEM_PROMPT: str = ""

    def build_graph(self) -> StateGraph:
        raise NotImplementedError

    async def llm_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        query = state.get("query", "")
        results = state.get("intermediate_results", [])
        prompt = (
            "Query: {query}\n\n"
            "Tool results: {results}\n\n"
            "Provide a clear response based on the above."
        ).format(query=query, results=results)

        # Avoids a redundant LLM call for a prompt that's near-identical to
        # one answered recently (bounded recent-query cache, not a general
        # semantic index).
        cached = await semantic_cache_service.get_similar(self.name, prompt)
        if cached is not None:
            return {"llm_response": cached}

        response = await llm_service.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
        await semantic_cache_service.store(self.name, prompt, response)
        return {"llm_response": response}

    async def stream_llm(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        query = state.get("query", "")
        results = state.get("intermediate_results", [])
        prompt = (
            "Query: {query}\n\n"
            "Tool results: {results}\n\n"
            "Provide a clear response."
        ).format(query=query, results=results)
        async for chunk in llm_service.stream_generate(
            prompt, system_prompt=self.SYSTEM_PROMPT
        ):
            yield chunk

    async def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        graph = self.build_graph()
        app = graph.compile()
        state: Dict[str, Any] = {
            "query": query,
            "tools": kwargs.get("tools", self.tools),
            "user_id": kwargs.get("user_id"),
            "intermediate_results": [],
            "llm_response": None,
            "result": {},
            "error": None,
        }
        try:
            final = await app.ainvoke(state)
            return {
                "agent": self.name,
                "query": query,
                "status": "completed",
                "result": final.get("result", final.get("llm_response", {})),
            }
        except TokenBudgetExceededError:
            # Let agent_service's dedicated handler report this distinctly
            # (413, not a generic failure) instead of folding it into the
            # catch-all below.
            raise
        except Exception as e:
            logger.exception(f"Agent {self.name!r} failed for query {query!r}: {e}")
            # Exception messages can carry internal details (DB connection
            # strings, file paths, stack traces); only surface them in debug.
            error = str(e) if settings.debug else "Agent execution failed"
            return {
                "agent": self.name,
                "query": query,
                "status": "failed",
                "error": error,
            }
