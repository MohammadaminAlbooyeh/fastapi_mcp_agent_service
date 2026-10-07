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


def _endpoint_label(request: Request) -> str:
    """Uses the matched route's path template (e.g. "/api/v1/agent/status/{task_id}")
    rather than the raw request path. Labeling by raw path would create a new,
    permanent Prometheus time series for every distinct task_id/request_id ever
    seen — unbounded cardinality growth that leaks those IDs through the
    unauthenticated /metrics endpoint and leads to steadily growing memory use."""
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    return request.url.path


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable):
        if request.url.path == "/metrics":
            return await call_next(request)

        ACTIVE_REQUESTS.inc()
        start = time.time()
        try:
            response = await call_next(request)
            endpoint = _endpoint_label(request)
            status_group = f"{response.status_code // 100}xx"
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_group,
            ).inc()
            return response
        except Exception:
            REQUEST_COUNT.labels(
                method=request.method,
                endpoint=_endpoint_label(request),
                status="5xx",
            ).inc()
            raise
        finally:
            REQUEST_DURATION.labels(
                method=request.method,
                endpoint=_endpoint_label(request),
            ).observe(time.time() - start)
            ACTIVE_REQUESTS.dec()


def metrics_endpoint(request: Request | None = None) -> Response:
    return StarletteResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
