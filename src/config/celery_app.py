from __future__ import annotations

from celery import Celery

from src.config.settings import settings

celery_app = Celery(
    "agent_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks.agent_tasks", "src.services.approval_expiry_job"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # SQS has no concept of exchanges/routing keys beyond the queue name
    # itself; this maps Celery's default "celery" queue onto an SQS queue
    # name prefix so multiple environments can share one AWS account.
    broker_transport_options={
        "region": settings.aws_region,
        "queue_name_prefix": f"{settings.environment}-agent-service-",
    },
    beat_schedule={
        "expire-pending-approvals": {
            "task": "expire_pending_approvals",
            "schedule": 60.0,
        },
    },
)
