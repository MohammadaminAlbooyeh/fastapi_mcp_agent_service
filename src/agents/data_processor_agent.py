from __future__ import annotations

from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.mcp_tools.tools_registry import tools_registry


class DataProcessorAgent(BaseAgent):
    name: str = "processor"
    description: str = "For data transformation and analysis"
    tools: list[str] = ["file_tool", "calculator_tool"]

    def build_graph(self) -> StateGraph:
        def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"task": state.get("query", "")}

        async def execute_calculations(state: Dict[str, Any]) -> Dict[str, Any]:
            calc = tools_registry.get("calculator_tool")
            result = await calc.execute(expression=state.get("query", ""))
            return {"calculation_result": result}

        def respond(state: Dict[str, Any]) -> Dict[str, Any]:
            return {"result": {"calculation": state.get("calculation_result", {}), "status": "processed"}}

        graph = StateGraph(Dict[str, Any])
        graph.add_node("analyze", analyze)
        graph.add_node("execute_calculations", execute_calculations)
        graph.add_node("respond", respond)
        graph.add_edge(START, "analyze")
        graph.add_edge("analyze", "execute_calculations")
        graph.add_edge("execute_calculations", "respond")
        graph.add_edge("respond", END)
        return graph
