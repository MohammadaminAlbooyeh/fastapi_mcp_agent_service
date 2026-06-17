# Usage Examples

## Execute a Query Agent

```bash
curl -X POST http://localhost:8000/api/v1/agent/execute \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Get all users from database where age > 25",
    "agent_type": "query",
    "tools": ["database_tool"],
    "max_iterations": 5,
    "timeout": 30
  }'
```

## Check Health

```bash
curl http://localhost:8000/api/v1/health
```

## List Tools

```bash
curl http://localhost:8000/api/v1/tools
```
