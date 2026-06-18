from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List, Optional

from langgraph.graph import StateGraph

from src.services.llm_service import llm_service


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
        prompt = f"Query: {query}\n\nTool results: {results}\n\nProvide a clear response based on the above."
        response = await llm_service.generate(prompt, system_prompt=self.SYSTEM_PROMPT)
        return {"llm_response": response}

    async def stream_llm(self, state: Dict[str, Any]) -> AsyncGenerator[str, None]:
        query = state.get("query", "")
        results = state.get("intermediate_results", [])
        prompt = f"Query: {query}\n\nTool results: {results}\n\nProvide a clear response."
        async for chunk in llm_service.stream_generate(prompt, system_prompt=self.SYSTEM_PROMPT):
            yield chunk

    async def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        graph = self.build_graph()
        app = graph.compile()
        state: Dict[str, Any] = {
            "query": query,
            "tools": kwargs.get("tools", self.tools),
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
        except Exception as e:
            return {
                "agent": self.name,
                "query": query,
                "status": "failed",
                "error": str(e),
            }
