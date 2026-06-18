from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.mcp_tools.tools_registry import tools_registry


class ResearchAgent(BaseAgent):
    name: str = "research"
    description: str = "For information gathering and research"
    tools: list[str] = ["search_tool", "api_tool"]

    def build_graph(self) -> StateGraph:
        def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"research_topic": state.get("query", "")}

        async def execute_tools(state: Dict[str, Any]) -> Dict[str, Any]:
            results: List[Dict[str, Any]] = []
            search = tools_registry.get("search_tool")
            sr = await search.execute(action="web_search", query=state.get("research_topic", ""))
            results.append(sr)
            return {"intermediate_results": results}

        def respond(state: Dict[str, Any]) -> Dict[str, Any]:
            results = state.get("intermediate_results", [])
            return {"result": {"findings": results, "sources_count": len(results)}}

        graph = StateGraph(Dict[str, Any])
        graph.add_node("analyze", analyze)
        graph.add_node("execute_tools", execute_tools)
        graph.add_node("respond", respond)
        graph.add_edge(START, "analyze")
        graph.add_edge("analyze", "execute_tools")
        graph.add_edge("execute_tools", "respond")
        graph.add_edge("respond", END)
        return graph
