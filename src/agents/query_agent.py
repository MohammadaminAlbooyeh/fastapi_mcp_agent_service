from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.mcp_tools.tools_registry import tools_registry


class QueryAgent(BaseAgent):
    name: str = "query"
    description: str = "Specialized for executing database queries"
    tools: list[str] = ["database_tool"]
    SYSTEM_PROMPT: str = "You are a database query assistant. Interpret the user's request and explain the query results."

    def build_graph(self) -> StateGraph:
        def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"sql_query": state.get("query", "")}

        async def execute_tools(state: Dict[str, Any]) -> Dict[str, Any]:
            tool = tools_registry.get("database_tool")
            result = await tool.execute(action="query", sql=state.get("sql_query", ""))
            return {"intermediate_results": [result]}

        async def respond(state: Dict[str, Any]) -> Dict[str, Any]:
            response = await self.llm_node(state)
            return {"result": response}

        graph = StateGraph(Dict[str, Any])
        graph.add_node("analyze", analyze)
        graph.add_node("execute_tools", execute_tools)
        graph.add_node("respond", respond)
        graph.add_edge(START, "analyze")
        graph.add_edge("analyze", "execute_tools")
        graph.add_edge("execute_tools", "respond")
        graph.add_edge("respond", END)
        return graph
