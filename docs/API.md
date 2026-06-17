# API Documentation

## Endpoints

### Health
- `GET /api/v1/health` - Service health check
- `GET /api/v1/health/detailed` - Detailed health info

### Agent
- `POST /api/v1/agent/execute` - Execute an agent task
- `POST /api/v1/agent/stream` - Stream agent response
- `GET /api/v1/agent/status/{task_id}` - Get task status
- `GET /api/v1/agent/result/{task_id}` - Get final result
- `POST /api/v1/agent/cancel/{task_id}` - Cancel running task

### Tools
- `GET /api/v1/tools` - List available MCP tools
- `GET /api/v1/tools/{tool_name}` - Get tool details
- `POST /api/v1/tools/test` - Test a tool
