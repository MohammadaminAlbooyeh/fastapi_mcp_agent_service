from __future__ import annotations

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AgentException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ToolNotFoundException(AgentException):
    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' not found", status_code=404)


class AgentExecutionException(AgentException):
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


async def agent_exception_handler(
    request: Request, exc: AgentException
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
