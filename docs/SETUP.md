# Setup & Installation Guide

## Prerequisites
- Python 3.11+
- PostgreSQL
- Redis (optional)

## Installation

```bash
git clone <repo-url>
cd fastapi_mcp_agent_service

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your configuration

python scripts/init_db.py
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

```bash
docker-compose -f docker/docker-compose.yml up -d
```
