from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import StateGraph


class BaseAgent:
    name: str = ""
    description: str = ""
    tools: List[str] = []

    def build_graph(self) -> StateGraph:
        raise NotImplementedError

    async def execute(self, query: str, **kwargs: Any) -> Dict[str, Any]:
        graph = self.build_graph()
        app = graph.compile()
        state: Dict[str, Any] = {
            "query": query,
            "tools": kwargs.get("tools", self.tools),
            "intermediate_results": [],
            "result": {},
            "error": None,
        }
        try:
            final = await app.ainvoke(state)
            return {
                "agent": self.name,
                "query": query,
                "status": "completed",
                "result": final.get("result", {}),
            }
        except Exception as e:
            return {
                "agent": self.name,
                "query": query,
                "status": "failed",
                "error": str(e),
            }
