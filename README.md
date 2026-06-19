# FastAPI MCP Agent Service

A production-ready AI Agent orchestration service combining **FastAPI**, **LangGraph**, and **MCP (Model Context Protocol)** tools for intelligent task execution with structured access to databases, file systems, and external APIs.

## Overview

This service provides a scalable, async-first platform for deploying multi-agent systems. It enables AI agents to safely execute tasks with access to tools via the Model Context Protocol, including database operations, file management, and third-party integrations.

## Features

- **Multi-Agent Orchestration** — Query, Processor, and Research agents using LangGraph
- **MCP Tools Framework** — Standardized interface for agent tool access
- **Database Integration** — PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **Async/Await Throughout** — Non-blocking operations with ASGI server
- **Task Persistence** — Store, retrieve, and monitor agent execution history
- **Caching Layer** — Redis for performance optimization
- **Job Queue** — Celery-based background task processing
- **Streaming Responses** — Real-time agent output via Server-Sent Events
- **Authentication** — JWT-based security with python-jose
- **Error Handling** — Comprehensive exception handling and graceful degradation
- **Production Ready** — Structured logging, CORS middleware, health checks

## Prerequisites

- Python 3.11+
- PostgreSQL 12+
- Redis (optional, for caching and Celery)

## Quick Start

### 1. Clone and Setup

```bash
git clone <repo-url>
cd fastapi_mcp_agent_service

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your database and service credentials
```

### 4. Initialize Database

```bash
python scripts/init_db.py
```

### 5. Run Server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with OpenAPI docs at `/docs`.

## Docker

### Development

```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Production

Update `docker/docker-compose.yml` with production credentials and deploy:

```bash
docker-compose -f docker/docker-compose.yml up -d --build
```

## API Endpoints

The service exposes the following endpoint groups:

- **`GET /api/v1/health`** — Service health check
- **`GET /api/v1/health/detailed`** — Detailed dependency health
- **`POST /api/v1/agent/execute`** — Execute an agent task
- **`POST /api/v1/agent/stream`** — Stream agent output
- **`GET /api/v1/agent/status/{task_id}`** — Get task status
- **`GET /api/v1/agent/result/{task_id}`** — Get task result
- **`POST /api/v1/agent/cancel/{task_id}`** — Cancel a running task
- **`GET /api/v1/tools`** — List available MCP tools
- **`GET /api/v1/tools/{tool_name}`** — Get tool details
- **`POST /api/v1/tools/test`** — Test a tool
- **`GET /api/v1/approval/requests`** — List pending approval requests
- **`POST /api/v1/approval/requests/{request_id}/approve`** — Approve a request
- **`POST /api/v1/approval/requests/{request_id}/reject`** — Reject a request
- **`POST /api/v1/auth/token`** — Get JWT/bearer access token

For the full contract, see [API Documentation](docs/API.md).

## Architecture

### High-Level Component Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Application                             │
├─────────────────────────────────────────────────────────────────────┤
│  API Routes                                                          │
│  ├─ /agent/execute (Sync execution)                                 │
│  ├─ /agent/stream (Streaming responses)                             │
│  ├─ /agent/status, /agent/result, /agent/cancel                    │
│  ├─ /tools (List & test MCP tools)                                  │
│  ├─ /approval (Approval workflow)                                   │
│  └─ /health (Health checks)                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Middleware Layer                                                    │
│  ├─ CORS Middleware                                                 │
│  ├─ Error Handling Middleware                                       │
│  ├─ Rate Limiting (100 req/min)                                     │
│  └─ Metrics Collection (Prometheus)                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Service Layer                                                       │
│  ├─ AgentService (Orchestration)                                    │
│  ├─ TaskService (Persistence)                                       │
│  ├─ LLMService (Claude API)                                         │
│  ├─ CacheService (Redis)                                            │
│  ├─ NotificationService (Webhooks)                                  │
│  ├─ ApprovalService (Human-in-the-loop)                            │
│  └─ MemoryService (Agent conversations)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Agent Layer (LangGraph)                                             │
│  ├─ Query Agent (Database ops)                                      │
│  ├─ Processor Agent (Data transformation)                           │
│  └─ Research Agent (Web search & APIs)                              │
├─────────────────────────────────────────────────────────────────────┤
│  MCP Tools Layer                                                     │
│  ├─ DatabaseTool (SQL execution)                                    │
│  ├─ FileTool (File operations)                                      │
│  ├─ CalculatorTool (Math operations)                                │
│  ├─ SearchTool (Semantic & similarity search)                       │
│  └─ APITool (REST & GraphQL requests)                               │
├─────────────────────────────────────────────────────────────────────┤
│  Persistence & Cache                                                │
│  ├─ PostgreSQL (Tasks, audit logs)                                  │
│  ├─ Redis (Caching, sessions, queues)                               │
│  └─ Celery (Background jobs)                                        │
└─────────────────────────────────────────────────────────────────────┘
```

## Complete Workflows

### 1. Synchronous Agent Execution Workflow

```
Client Request (POST /api/v1/agent/execute)
    │
    ├─→ Authentication Check (JWT)
    │       │
    │       └─→ Validation (agent_type, tools, query)
    │
    ├─→ TaskService.create_task()
    │       │
    │       └─→ Store in PostgreSQL (status: "pending")
    │
    ├─→ Check Cache (TaskService.get_cached_result)
    │       │
    │       ├─→ Cache HIT → Return cached result
    │       │
    │       └─→ Cache MISS → Continue
    │
    ├─→ AgentService.execute()
    │       │
    │       ├─→ AgentOrchestrator.route_to_agent()
    │       │       │
    │       │       ├─ Query Agent (database_tool)
    │       │       ├─ Processor Agent (file_tool, calculator_tool)
    │       │       └─ Research Agent (search_tool, api_tool)
    │       │
    │       ├─→ Agent builds LangGraph workflow
    │       │       │
    │       │       ├─→ LLM Node (Claude generates plan)
    │       │       ├─→ Tool Execution Node (runs MCP tools)
    │       │       ├─→ Result Processing Node (formats output)
    │       │       └─→ LLM Summary Node (final response)
    │       │
    │       ├─→ Check if approval required
    │       │       │
    │       │       ├─ YES → ApprovalService.create_approval_request()
    │       │       │          (Return pending approval, timeout: 5 min)
    │       │       │
    │       │       └─ NO → Continue execution
    │       │
    │       └─→ Execute with timeout protection
    │
    ├─→ TaskService.save_result()
    │       │
    │       ├─→ Update PostgreSQL (status: "completed")
    │       ├─→ Cache result in Redis (TTL: 1 hour)
    │       └─→ Calculate execution_time
    │
    ├─→ NotificationService.notify_task_completed()
    │       │
    │       └─→ Send webhook if configured
    │
    └─→ Return TaskResponse to client
        {
            "task_id": "uuid",
            "status": "completed",
            "result": {...},
            "execution_time": 2.5,
            "error": null
        }
```

### 2. Streaming Agent Execution Workflow

```
Client Request (POST /api/v1/agent/stream)
    │
    ├─→ Authentication Check (JWT)
    │
    ├─→ Establish SSE (Server-Sent Events) connection
    │
    ├─→ TaskService.create_task() [async]
    │       │
    │       └─→ Store in PostgreSQL (status: "pending")
    │
    ├─→ AgentService.stream()
    │       │
    │       ├─→ LLMService.stream_generate()
    │       │       │
    │       │       ├─→ Connect to Claude API
    │       │       │
    │       │       └─→ Stream tokens in real-time:
    │       │           "data: token1\n\n"
    │       │           "data: token2\n\n"
    │       │           "data: token3\n\n"
    │       │
    │       └─→ As tokens arrive:
    │               ├─→ Yield to client
    │               ├─→ Accumulate in buffer
    │               └─→ Update in-memory state
    │
    ├─→ After stream completes
    │       │
    │       ├─→ Execute any pending tools (parallel)
    │       ├─→ Append tool results to stream
    │       └─→ Send final result
    │
    ├─→ TaskService.save_result() [async]
    │       │
    │       └─→ Store final state in PostgreSQL
    │
    └─→ Close SSE connection
        Client receives continuous updates:
        "data: Processing query...\n\n"
        "data: Running database_tool...\n\n"
        "data: [RESULT] {...}\n\n"
```

### 3. MCP Tool Execution Flow (Inside Agent)

```
Agent Node receives query: "Get users over 25"
    │
    ├─→ LLM Node: Claude generates plan
    │       │
    │       └─→ "I need to execute a SQL query on the database"
    │               Plan: { tool: "database_tool", action: "execute_query", params: {...} }
    │
    ├─→ Tool Selection Node
    │       │
    │       ├─→ Validate tool is in agent's allowed tools
    │       ├─→ Validate tool parameters
    │       └─→ Check if approval needed (for sensitive ops)
    │
    ├─→ Tool Execution Node
    │       │
    │       └─→ ToolsRegistry.get_tool(tool_name)
    │               │
    │               ├─→ Initialize tool instance
    │               │
    │               └─→ Execute tool.execute(action, params)
    │                       │
    │                       ├─ DatabaseTool
    │                       │   ├─ Validate SQL (no DROP, DELETE, etc.)
    │                       │   ├─ Execute with asyncpg connection pool
    │                       │   └─ Return: {status: "ok", data: [...]}
    │                       │
    │                       ├─ FileTool
    │                       │   ├─ Check file path (prevent traversal)
    │                       │   ├─ Execute (read/write/list)
    │                       │   └─ Return: {status: "ok", content: "..."}
    │                       │
    │                       ├─ SearchTool
    │                       │   ├─ Call external API (with rate limiting)
    │                       │   └─ Return: {results: [...]}
    │                       │
    │                       ├─ APITool
    │                       │   ├─ Parse URL and method
    │                       │   ├─ Send HTTP/GraphQL request
    │                       │   ├─ Handle retries on 429, 500
    │                       │   └─ Return: {status_code: 200, data: {...}}
    │                       │
    │                       └─ CalculatorTool
    │                           ├─ Parse expression
    │                           ├─ Evaluate safely
    │                           └─ Return: {result: 42}
    │
    ├─→ Result Processing
    │       │
    │       ├─→ Store in state["intermediate_results"]
    │       └─→ Continue to next node
    │
    └─→ LLM Synthesis Node
            │
            └─→ Claude generates final response based on:
                    - Original query
                    - Tool results
                    - Context from MemoryService
```

### 4. Approval Workflow (Human-in-the-Loop)

```
Sensitive Operation Detected (DELETE, DROP, etc.)
    │
    ├─→ ApprovalService.create_approval_request()
    │       │
    │       ├─→ Generate approval ID
    │       ├─→ Store request (task_id, operation, expiry: +5 min)
    │       ├─→ Emit notification webhook (if configured)
    │       └─→ Return to client with status: "pending_approval"
    │
    ├─→ Client polls: GET /api/v1/approval/requests
    │       │
    │       └─→ Returns pending approval requests with:
    │           {
    │             "request_id": "xxx",
    │             "task_id": "yyy",
    │             "operation": "DELETE from users",
    │             "status": "pending",
    │             "expires_at": "2026-06-19T10:30:00Z"
    │           }
    │
    ├─→ Human approves or rejects
    │       │
    │       ├─→ POST /api/v1/approval/requests/{id}/approve
    │       │       │
    │       │       ├─→ Validate request still valid (not expired)
    │       │       ├─→ Resume agent execution from checkpoint
    │       │       ├─→ Execute sensitive operation
    │       │       ├─→ Update task status: "completed"
    │       │       └─→ Cache result
    │       │
    │       └─→ POST /api/v1/approval/requests/{id}/reject
    │               │
    │               ├─→ Mark request as rejected
    │               ├─→ Fail associated task
    │               ├─→ Return error: "Operation rejected by approver"
    │               └─→ Notify via webhook
    │
    └─→ Expiry Handler (background)
            │
            └─→ If no response after 5 minutes:
                    ├─→ Auto-reject approval
                    ├─→ Fail associated task
                    └─→ Log for audit trail
```

### 5. Caching & Performance Optimization Flow

```
Task Execution Request
    │
    ├─→ CacheService.get_cached_result(cache_key)
    │       │
    │       ├─→ Generate cache key: hash(agent_type + query + tools)
    │       │
    │       ├─→ Try Redis
    │       │       ├─ HIT → Increment metrics, return result [5ms]
    │       │       └─ MISS → Fall through
    │       │
    │       ├─→ Fall back to in-memory cache (if Redis unavailable)
    │       │       ├─ HIT → Return result [1ms]
    │       │       └─ MISS → Continue
    │       │
    │       └─→ Result: CACHE_MISS (proceed with execution)
    │
    ├─→ Execute Task (normal flow)
    │       │
    │       ├─→ Run agent workflow
    │       ├─→ Execute MCP tools
    │       ├─→ Collect results
    │       └─→ Return final result
    │
    ├─→ CacheService.cache_result(cache_key, result)
    │       │
    │       ├─→ Store in Redis with TTL: 3600 seconds
    │       ├─→ Store in in-memory cache with TTL: 300 seconds
    │       ├─→ Increment cache_writes metric
    │       └─→ Update memory usage tracking
    │
    └─→ Return result to client [normal execution time]

Cache Invalidation:
    ├─→ When agent memory is updated
    ├─→ When database is modified (DELETE, UPDATE)
    ├─→ When approval is processed
    └─→ When task is cancelled
```

### 6. Agent Memory Management Workflow

```
Client Session starts
    │
    ├─→ MemoryService.get_session(session_id)
    │       │
    │       └─→ Load or create ConversationMemory
    │               {
    │                 "session_id": "user-123",
    │                 "history": [],
    │                 "metadata": {...}
    │               }
    │
    ├─→ Agent executes query
    │       │
    │       ├─→ Retrieve conversation history
    │       ├─→ Include in LLM context (system prompt)
    │       └─→ LLM generates response with context awareness
    │
    ├─→ Store result in memory
    │       │
    │       ├─→ MemoryService.add_to_history()
    │       │       │
    │       │       ├─→ Append message to history list
    │       │       ├─→ Maintain max history: 100 messages
    │       │       ├─→ Truncate oldest if over limit
    │       │       └─→ Store in Redis per session
    │       │
    │       └─→ Store in PostgreSQL for persistence
    │               └─→ Can recover after service restart
    │
    └─→ Future requests in same session
            │
            └─→ Use agent memory for context
                    ├─→ "Remember when we discussed X?"
                    ├─→ "Refer back to previous result"
                    └─→ Consistent multi-turn conversations
```

### 7. End-to-End Request Lifecycle with Metrics

```
Client                  API Server                 Database            External
   │                        │                          │                 │
   │  POST /agent/execute   │                          │                 │
   ├───────────────────────>│  [t=0ms]                 │                 │
   │                        │                          │                 │
   │                        ├─ Validate JWT            │                 │
   │                        ├─ Check rate limit        │                 │
   │                        ├─ Record metrics          │                 │
   │                        │  [t=5ms]                 │                 │
   │                        │                          │                 │
   │                        ├─ Check cache             │                 │
   │                        │  [t=10ms]                │                 │
   │                        │  MISS → Continue         │                 │
   │                        │                          │                 │
   │                        ├─ Create task             │                 │
   │                        ├──────────────────────────>│ INSERT tasks    │
   │                        │  [t=20ms]                │ [t=22ms]        │
   │                        │                          │                 │
   │                        ├─ Route to agent          │                 │
   │                        ├─ Build LangGraph         │                 │
   │                        │  [t=30ms]                │                 │
   │                        │                          │                 │
   │                        ├─ Call LLM (Claude)       │                 │
   │                        ├─────────────────────────────────────────────>│
   │                        │  [t=50ms]                │                 │
   │                        │                          │                 │ (LLM Processing)
   │                        │<─────────────────────────────────────────────┤
   │                        │  [t=800ms]               │                 │
   │                        │                          │                 │
   │                        ├─ Execute tools           │                 │
   │                        │  [t=810ms]               │                 │
   │                        ├─ DatabaseTool            │                 │
   │                        ├──────────────────────────>│ SELECT users    │
   │                        │  [t=850ms]               │ [t=860ms]       │
   │                        │<──────────────────────────┤ Result: [...]   │
   │                        │  [t=870ms]               │                 │
   │                        │                          │                 │
   │                        ├─ APITool call            │                 │
   │                        ├─────────────────────────────────────────────>│
   │                        │  [t=880ms]               │                 │
   │                        │<─────────────────────────────────────────────┤
   │                        │  [t=1200ms]              │                 │
   │                        │                          │                 │
   │                        ├─ Store result in cache   │                 │
   │                        ├─ Cache in Redis          │                 │
   │                        │  [t=1210ms]              │                 │
   │                        │                          │                 │
   │                        ├─ Update task status      │                 │
   │                        ├──────────────────────────>│ UPDATE tasks    │
   │                        │  [t=1220ms]              │ [t=1225ms]      │
   │                        │                          │                 │
   │                        ├─ Send notification       │                 │
   │                        ├─────────────────────────────────────────────>│
   │                        │  [t=1230ms]              │                 │ (Webhook)
   │                        │                          │                 │
   │  200 OK + result       │                          │                 │
   │<───────────────────────┤  [t=1235ms]              │                 │
   │  execution_time: 1235ms│                          │                 │
   │  status: "completed"   │                          │                 │
```

## Configuration

Configuration is managed through environment variables. See `.env.example` for available options:

- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection URL (optional)
- `CORS_ALLOWED_ORIGINS` — Comma-separated CORS origins
- `LOG_LEVEL` — Logging level (DEBUG, INFO, WARNING, ERROR)
- `JWT_SECRET` — Secret key for JWT authentication

## Development

### Running Tests

```bash
# Unit tests
pytest tests/unit -v

# Integration tests
pytest tests/integration -v

# Coverage report
pytest --cov=src tests/ --cov-report=html
```

### Code Quality

```bash
# Format
black src/ tests/

# Lint
flake8 src/ tests/

# Type checking
mypy src/
```

### Project Structure

```
src/
├── agents/          # Multi-agent implementations
├── api/
│   ├── routes/      # API endpoints
│   ├── middleware/  # Request/response middleware
│   └── schemas/     # Pydantic models
├── config/          # Settings and logging
├── database/        # SQLAlchemy models and migrations
├── mcp_tools/       # MCP tool implementations
├── models/          # Domain models
├── services/        # Business logic layer
└── utils/           # Utilities and helpers
```

## Documentation

- [Setup & Installation](docs/SETUP.md) — Detailed installation instructions
- [Agent Guide](docs/AGENTS.md) — Agent architecture and customization
- [MCP Tools](docs/MCP_TOOLS.md) — Available tools and tool development
- [API Reference](docs/API.md) — Complete endpoint documentation
- [Examples](docs/EXAMPLES.md) — Usage examples and workflows

## Deployment

See Docker files in `docker/` directory for containerized deployment. For production:

1. Update environment variables for your infrastructure
2. Configure database backups and monitoring
3. Set up Redis replication if using caching
4. Configure Celery workers for background jobs
5. Enable TLS/SSL for all connections
6. Set up structured logging aggregation

## License

MIT License
