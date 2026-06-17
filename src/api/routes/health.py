from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    return {"status": "healthy", "service": "fastapi-mcp-agent-service"}


@router.get("/detailed")
async def detailed_health() -> dict:
    return {
        "status": "healthy",
        "service": "fastapi-mcp-agent-service",
        "version": "0.1.0",
        "dependencies": {
            "database": "unknown",
            "redis": "unknown",
        },
    }
