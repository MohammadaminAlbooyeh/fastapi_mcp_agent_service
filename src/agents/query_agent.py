from __future__ import annotations

import re
from typing import Any, Dict, List

from langgraph.graph import END, START, StateGraph

from src.agents.base_agent import BaseAgent
from src.mcp_tools.tools_registry import tools_registry
from src.services.llm_service import llm_service

_SQL_FENCE_RE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


class QueryAgent(BaseAgent):
    name: str = "query"
    description: str = "Specialized for executing database queries"
    tools: list[str] = ["database_tool"]
    SYSTEM_PROMPT: str = "You are a database query assistant. Interpret the user's request and explain the query results."

    SQL_GENERATION_PROMPT: str = (
        "Convert the following request into a single, read-only SQL SELECT statement. "
        "Respond with only the SQL statement and nothing else — no explanation, no markdown fences.\n\n"
        "Request: {query}"
    )

    def build_graph(self) -> StateGraph:
        async def analyze(state: Dict[str, Any]) -> Dict[str, Any]:
            query = state.get("query", "")
            raw_sql = await llm_service.generate(self.SQL_GENERATION_PROMPT.format(query=query))
            sql = _SQL_FENCE_RE.sub("", raw_sql).strip()
            return {"sql_query": sql}

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
