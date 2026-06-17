from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.mcp_tools.tools_registry import tools_registry
from src.models.response import ToolResponse

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.get("", response_model=list[ToolResponse])
async def list_tools() -> list[ToolResponse]:
    tools = tools_registry.list_tools()
    return [ToolResponse(**t, status="active") for t in tools]


@router.get("/{tool_name}", response_model=ToolResponse)
async def get_tool_details(tool_name: str) -> ToolResponse:
    try:
        tool = tools_registry.get(tool_name)
        return ToolResponse(
            name=tool.name,
            description=tool.description,
            status="active",
        )
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")


@router.post("/test")
async def test_tool() -> dict:
    return {"message": "Tool test endpoint"}
