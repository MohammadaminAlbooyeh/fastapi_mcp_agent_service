# API Documentation

## Base URL

All endpoints are prefixed with `/api/v1`.

## Authentication

### `POST /api/v1/auth/token`

Get a JWT access token using HTTP Basic Auth.

**Request:**
- HTTP Basic Auth header: `username=<any>`, `password=<API_KEY from env>`

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Authentication Header for protected endpoints:**
```
Authorization: Bearer <access_token>
```

---

## Health

### `GET /api/v1/health`

Basic service health check.

**Response (200):**
```json
{
  "status": "healthy",
  "service": "fastapi_mcp_agent_service",
  "version": "0.1.0"
}
```

### `GET /api/v1/health/detailed`

Detailed health information including dependency status.

**Response (200):**
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "uptime_seconds": 3600
}
```

---

## Agent

### `POST /api/v1/agent/execute`

Execute an agent task synchronously.

**Request:**
```json
{
  "agent_type": "query",
  "query": "SELECT * FROM users WHERE age > 25",
  "tools": ["database_tool"],
  "max_iterations": 5,
  "timeout": 30
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `agent_type` | string | yes | - | One of: `query`, `processor`, `research` |
| `query` | string | yes | - | The task description or query |
| `tools` | array[string] | no | `[]` | Allowed MCP tool names |
| `max_iterations` | integer | no | `5` | Max agent loop iterations |
| `timeout` | integer | no | `30` | Execution timeout in seconds |

**Response (200):**
```json
{
  "task_id": "uuid-string",
  "status": "completed",
  "result": {
    "output": "Query returned 15 users older than 25."
  },
  "execution_time": 2.35,
  "error": null
}
```

**Error (422):**
```json
{
  "detail": [
    { "loc": ["body", "agent_type"], "msg": "field required", "type": "value_error.missing" }
  ]
}
```

### `POST /api/v1/agent/stream`

Execute an agent task with streaming Server-Sent Events (SSE).

**Request:** Same body as `/agent/execute`.

**Response:** SSE stream (`text/event-stream`):
```
data: {"type": "token", "content": "Processing"}
data: {"type": "token", "content": " query..."}
data: {"type": "result", "content": {"output": "..."}}
data: {"type": "done", "content": {}}
```

### `GET /api/v1/agent/status/{task_id}`

Get the current status of a task.

**Response (200):**
```json
{
  "task_id": "uuid-string",
  "status": "running",
  "result": null,
  "execution_time": null,
  "error": null
}
```

**Response (404):**
```json
{
  "detail": "Task 'invalid-id' not found"
}
```

### `GET /api/v1/agent/result/{task_id}`

Get the final result of a completed task.

**Response (200):** Same shape as `/agent/execute` response.

### `POST /api/v1/agent/cancel/{task_id}`

Cancel a running task.

**Response (200):**
```json
{
  "task_id": "uuid-string",
  "status": "cancelled"
}
```

---

## Tools (MCP)

### `GET /api/v1/tools`

List all registered MCP tools.

**Response (200):**
```json
[
  {
    "name": "database_tool",
    "description": "SQL CRUD operations",
    "status": "active"
  },
  {
    "name": "file_tool",
    "description": "File system operations",
    "status": "active"
  },
  {
    "name": "search_tool",
    "description": "Web search and semantic search operations",
    "status": "active"
  },
  {
    "name": "api_tool",
    "description": "REST/GraphQL API calls",
    "status": "active"
  },
  {
    "name": "calculator_tool",
    "description": "Safe math evaluation",
    "status": "active"
  }
]
```

### `GET /api/v1/tools/{tool_name}`

Get details for a specific tool.

**Response (200):**
```json
{
  "name": "database_tool",
  "description": "SQL CRUD operations",
  "status": "active"
}
```

**Response (404):**
```json
{
  "detail": "Tool 'unknown_tool' not found"
}
```

### `POST /api/v1/tools/test`

Execute a test invocation of any registered tool.

**Request:**
```json
{
  "tool_name": "calculator_tool",
  "action": "calculate",
  "params": {
    "expression": "2 + 2"
  }
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_name` | string | yes | Name of the tool to test |
| `action` | string | yes | Action to execute |
| `params` | object | no | Parameters passed to the tool |

**Response (200):**
```json
{
  "tool": "calculator_tool",
  "action": "calculate",
  "result": {
    "tool": "calculator_tool",
    "action": "calculate",
    "result": 4
  }
}
```

**Response (404):**
```json
{
  "detail": "Tool 'unknown' not found"
}
```

---

## Approval (Human-in-the-Loop)

### `GET /api/v1/approval/requests`

List all pending approval requests.

**Response (200):**
```json
[
  {
    "request_id": "uuid-string",
    "task_id": "uuid-string",
    "tool_name": "database_tool",
    "tool_args": { "action": "delete", "table": "users" },
    "agent_type": "query",
    "query": "Remove inactive users",
    "status": "pending",
    "created_at": "2026-06-20T10:00:00",
    "expires_at": "2026-06-20T10:05:00"
  }
]
```

### `POST /api/v1/approval/requests/{request_id}/approve`

Approve a pending request.

**Request (optional body):**
```json
{
  "approver": "admin@example.com"
}
```

**Response (200):**
```json
{
  "request_id": "uuid-string",
  "status": "approved"
}
```

### `POST /api/v1/approval/requests/{request_id}/reject`

Reject a pending request.

**Request (optional body):**
```json
{
  "approver": "admin@example.com",
  "reason": "This operation is not authorized"
}
```

**Response (200):**
```json
{
  "request_id": "uuid-string",
  "status": "rejected"
}
```

---

## Metrics

### `GET /metrics`

Prometheus metrics endpoint (no `/api/v1` prefix).

**Response (200):** `text/plain; charset=utf-8` with Prometheus-formatted metrics:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/api/v1/health",status="2xx"} 42.0
```

---

## Error Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 401 | Missing or invalid authentication token |
| 404 | Resource not found |
| 422 | Request validation error |
| 429 | Rate limit exceeded (100 req/min) |
| 500 | Internal server error |

## Rate Limiting

- **Limit:** 100 requests per IP per 60-second window
- **Backend:** Redis (falls back to in-memory)
- **Error response:** 429 with `retry_after` in seconds
