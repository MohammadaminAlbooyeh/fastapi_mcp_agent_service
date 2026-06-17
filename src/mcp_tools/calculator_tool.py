from __future__ import annotations

from typing import Any, Dict

from src.mcp_tools.base import BaseTool


class CalculatorTool(BaseTool):
    name: str = "calculator_tool"
    description: str = "Math and calculation operations"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        expression = kwargs.get("expression", "")
        try:
            result = eval(expression)
        except Exception as e:
            result = {"error": str(e)}
        return {"tool": self.name, "expression": expression, "result": result}
