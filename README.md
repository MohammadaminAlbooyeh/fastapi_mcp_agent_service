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

```
┌─────────────────────────────────────────────────┐
│        FastAPI Application                       │
├─────────────────────────────────────────────────┤
│  Routes (agent, tools, status, health)          │
├─────────────────────────────────────────────────┤
│  Services (AgentService, ToolService)           │
├─────────────────────────────────────────────────┤
│  Agents (Query, Processor, Research)            │
│  ↓ Uses LangGraph                               │
├─────────────────────────────────────────────────┤
│  MCP Tools (Database, Files, APIs)              │
├─────────────────────────────────────────────────┤
│  Database (PostgreSQL) | Cache (Redis)          │
│  Job Queue (Celery)                             │
└─────────────────────────────────────────────────┘
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
