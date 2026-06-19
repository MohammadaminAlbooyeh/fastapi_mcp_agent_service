from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client import CONTENT_TYPE_LATEST
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ACTIVE_REQUESTS = Gauge(
    "http_active_requests",
    "Number of active HTTP requests",
)

TASKS_CREATED = Counter(
    "tasks_created_total",
    "Total tasks created",
    ["agent_type"],
)

TASKS_COMPLETED = Counter(
    "tasks_completed_total",
    "Total tasks completed",
    ["agent_type", "status"],
)

TOOL_EXECUTIONS = Counter(
    "tool_executions_total",
    "Total tool executions",
    ["tool_name", "status"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path == "/metrics":
            return await call_next(request)

        ACTIVE_REQUESTS.inc()
        start = time.time()
        try:
            response = await call_next(request)
            status_group = f"{response.status_code // 100}xx"
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status=status_group,
            ).inc()
            return response
        except Exception:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=request.url.path,
                status="5xx",
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=request.url.path,
            ).observe(time.time() - start)
            ACTIVE_REQUESTS.dec()


def metrics_endpoint(request: Request) -> Response:
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
