from __future__ import annotations

import ast
import operator
from typing import Any, Dict

from src.mcp_tools.base import BaseTool


_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class CalculatorTool(BaseTool):
    name: str = "calculator_tool"
    description: str = "Math and calculation operations"

    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        expression = kwargs.get("expression", "")
        try:
            result = self._safe_eval(expression)
            return {"tool": self.name, "expression": expression, "result": result}
        except Exception as e:
            return {"tool": self.name, "expression": expression, "error": str(e)}

    def _safe_eval(self, expr: str) -> float:
        tree = ast.parse(expr.strip(), mode="eval")
        return self._eval_node(tree.body)

    def _eval_node(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant: {node.value}")
        if isinstance(node, ast.UnaryOp):
            op = _ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(self._eval_node(node.operand))
        if isinstance(node, ast.BinOp):
            op = _ALLOWED_OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            return op(self._eval_node(node.left), self._eval_node(node.right))
        raise ValueError(f"Unsupported expression: {type(node).__name__}")
