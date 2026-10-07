from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from src.config.logger import logger
from src.config.settings import settings


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.exception(f"Unhandled exception while processing {request.method} {request.url.path}: {e}")
            # Exception messages can carry internal details (DB connection
            # strings, file paths, stack traces) — only ever return the raw
            # message in debug mode; production clients get a generic message.
            detail = str(e) if settings.debug else "Internal server error"
            return JSONResponse(
                status_code=500,
                content={"detail": detail},
            )
