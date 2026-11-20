# Deployment Guide (ECS)

Notes for running this service as more than one container behind a load
balancer. See `docker/docker-compose.yml` for the equivalent local topology
(`api`, `worker`, `beat`, `db`, `redis`).

## Configuration

Production reads configuration strictly from process environment variables
(`src/config/settings.py` disables loading a local `.env` file whenever
`ENVIRONMENT=production`). Wire each ECS task definition's `secrets` to pull
values from AWS Secrets Manager / SSM Parameter Store at deploy time, e.g.:

```json
"secrets": [
  {"name": "SECRET_KEY", "valueFrom": "arn:aws:secretsmanager:...:secret:agent-service/secret-key"},
  {"name": "DATABASE_URL", "valueFrom": "arn:aws:secretsmanager:...:secret:agent-service/database-url"},
  {"name": "ANTHROPIC_API_KEY", "valueFrom": "arn:aws:ssm:...:parameter/agent-service/anthropic-api-key"}
]
```

Never bake `.env` into the image — `.dockerignore` already excludes it.

## Logging

Logs are JSON on stdout only (no file handler, no local `logs/` volume) so
CloudWatch Logs can ingest the container's stdout/stderr directly via the
`awslogs` log driver.

## Graceful shutdown

On scale-in, ECS sends SIGTERM and waits `stopTimeout` seconds before
SIGKILL. Set the task definition's `stopTimeout` to match
`GRACEFUL_SHUTDOWN_SECONDS` (default 30s, passed to uvicorn's
`--timeout-graceful-shutdown`). Point the ALB target group's health check at
`GET /api/v1/health/ready` (not `/api/v1/health`) so it stops routing new
traffic as soon as the container starts draining, rather than only once
uvicorn actually stops accepting connections.

## Celery / SQS

`CELERY_BROKER_URL` should be an SQS URL in production (e.g. `sqs://`,
relying on the task's IAM role for auth — grant `sqs:*` on the service's
queue ARNs). The `worker` service can run with `desiredCount` > 1 and scale
independently of the API.

The `beat` service (scheduled jobs, currently just approval expiry) should
run with **`desiredCount: 1`** — the job itself is idempotent, but there's
no benefit to more than one scheduler.

## S3 (file_tool)

Set `S3_BUCKET_NAME`/`AWS_REGION` and grant the task role
`s3:GetObject`/`PutObject`/`DeleteObject`/`ListBucket` scoped to
`arn:aws:s3:::<bucket>/users/*`. Objects are namespaced by the authenticated
user id (`users/{user_id}/...`), not by container, so this is safe across
any number of API instances.
