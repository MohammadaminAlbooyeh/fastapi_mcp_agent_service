from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text as sa_text

from src.database.connection import SessionLocal

router = APIRouter(prefix="/api/v1/health", tags=["health"])


@router.get("")
async def health_check() -> dict:
    return {"status": "healthy", "service": "fastapi-mcp-agent-service"}


@router.get("/detailed")
async def detailed_health() -> dict:
    db_status = "unknown"
    redis_status = "unknown"

    try:
        db = SessionLocal()
        db.execute(sa_text("SELECT 1"))
        db.close()
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"

    try:
        import redis.asyncio as aioredis
        from src.config.settings import settings
        client = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await client.ping()
        await client.aclose()
        redis_status = "healthy"
    except Exception:
        redis_status = "unavailable"

    return {
        "status": "healthy",
        "service": "fastapi-mcp-agent-service",
        "version": "0.1.0",
        "dependencies": {
            "database": db_status,
            "redis": redis_status,
        },
    }
