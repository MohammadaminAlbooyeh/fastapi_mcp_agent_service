from __future__ import annotations

from celery import Celery

from src.config.settings import settings

celery_app = Celery(
    "agent_service",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks.agent_tasks"],
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
)
