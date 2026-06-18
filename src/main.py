from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.auth import create_access_token
from src.api.exceptions import AgentException, agent_exception_handler
from src.api.middleware import ErrorHandlingMiddleware
from src.api.routes.agent import router as agent_router
from src.api.routes.health import router as health_router
from src.api.routes.status import router as status_router
from src.api.routes.tools import router as tools_router
from src.config.logger import logger
from src.config.settings import settings
from src.services.cache_service import cache_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("Starting FastAPI MCP Agent Service...")
    yield
    logger.info("Shutting down FastAPI MCP Agent Service...")
    await cache_service.close()


app = FastAPI(
    title="FastAPI MCP Agent Service",
    description="Production-ready AI Agent service with FastAPI, LangGraph, and MCP tools",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(ErrorHandlingMiddleware)

app.add_exception_handler(AgentException, agent_exception_handler)

app.include_router(health_router)
app.include_router(agent_router)
app.include_router(status_router)
app.include_router(tools_router)


@app.post("/api/v1/auth/token")
async def get_token() -> dict:
    token = create_access_token({"sub": "api-user", "role": "user"})
    return {"access_token": token, "token_type": "bearer"}
