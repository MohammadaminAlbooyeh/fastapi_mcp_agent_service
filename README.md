# FastAPI MCP Agent Service

A production-ready AI Agent service combining FastAPI, LangGraph, and MCP (Model Context Protocol) tools for intelligent task execution with database, file system, and external API access.

## Features

- **Multi-Agent System** — Query, Processor, Research agents
- **MCP Tools Integration** — Database, Files, APIs, Search
- **Async/Await Support** — Non-blocking operations
- **Task Persistence** — Store & retrieve execution history
- **Caching Layer** — Redis for performance
- **Error Handling** — Graceful failure management
- **Streaming Responses** — Real-time agent output
- **Production Ready** — Logging, monitoring, security

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Initialize database
python scripts/init_db.py

# Run server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker-compose -f docker/docker-compose.yml up -d
```

## Testing

```bash
pytest tests/unit -v
pytest tests/integration -v
pytest --cov=src tests/
```

## License

MIT License
