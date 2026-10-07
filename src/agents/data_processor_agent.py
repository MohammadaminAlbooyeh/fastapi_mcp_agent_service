from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.mcp_tools.tools_registry import tools_registry
from src.services.llm_service import llm_service

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)
_FILE_ACTIONS = {"read", "write", "list", "delete", "exists"}


class DataProcessorAgent(BaseAgent):
    name: str = "processor"
    description: str = "For data transformation and analysis"
    tools: list[str] = ["file_tool", "calculator_tool"]
    SYSTEM_PROMPT: str = "You are a data processing assistant. Explain calculations and file operations clearly."

    ROUTING_PROMPT: str = (
        "Classify the following request as either a math calculation or a file "
        "operation, and extract its parameters. Respond with only a single JSON "
        "object — no explanation, no markdown fences — matching one of these shapes:\n"
        '  {{"intent": "calculation", "expression": "<numeric expression using '
        'digits and + - * / // % ** ( ) operators>"}}\n'
        '  {{"intent": "file_operation", "file_action": "<one of read, write, list, '
        'delete, exists>", "path": "<file or directory path>", "content": "<content, '
        'only for write, else omitted>"}}\n\n'
        "Request: {query}"
    )

    def build_graph(self) -> StateGraph:
        async def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
            query = state.get("query", "")
            raw = await llm_service.generate(self.ROUTING_PROMPT.format(query=query))
            cleaned = _FENCE_RE.sub("", raw).strip()
            try:
                plan = json.loads(cleaned)
            except (json.JSONDecodeError, TypeError):
                plan = {}

            intent = plan.get("intent") if isinstance(plan, dict) else None
            if intent == "file_operation" and plan.get("file_action") in _FILE_ACTIONS:
                return {
                    "task": query,
                    "intent": "file_operation",
                    "file_action": plan.get("file_action"),
                    "file_path": plan.get("path", ""),
                    "file_content": plan.get("content", ""),
                }
            expression = plan.get("expression", "") if isinstance(plan, dict) else ""
            return {"task": query, "intent": "calculation", "expression": expression}

        async def execute_calculations(state: Dict[str, Any]) -> Dict[str, Any]:
            calc = tools_registry.get("calculator_tool")
            result = await calc.execute(expression=state.get("expression", ""))
            return {"intermediate_results": [result]}

        async def execute_file_operation(state: Dict[str, Any]) -> Dict[str, Any]:
            file_tool = tools_registry.get("file_tool")
            result = await file_tool.execute(
                action=state.get("file_action", ""),
                path=state.get("file_path", ""),
                directory=state.get("file_path", ""),
                content=state.get("file_content", ""),
            )
            return {"intermediate_results": [result]}

        async def respond(state: Dict[str, Any]) -> Dict[str, Any]:
            response = await self.llm_node(state)
            return {"result": response}

        def route(state: Dict[str, Any]) -> str:
            return "execute_file_operation" if state.get("intent") == "file_operation" else "execute_calculations"

        graph = StateGraph(Dict[str, Any])
        graph.add_node("analyze", analyze)
        graph.add_node("execute_calculations", execute_calculations)
        graph.add_node("execute_file_operation", execute_file_operation)
        graph.add_node("respond", respond)
        graph.add_edge(START, "analyze")
        graph.add_conditional_edges(
            "analyze",
            route,
            {"execute_calculations": "execute_calculations", "execute_file_operation": "execute_file_operation"},
        )
        graph.add_edge("execute_calculations", "respond")
        graph.add_edge("execute_file_operation", "respond")
        graph.add_edge("respond", END)
        return graph
