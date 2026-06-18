from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from src.config.celery_app import celery_app
from src.config.logger import logger
from src.services.task_service import task_service


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def execute_agent_task(
    self,
    task_id: str,
    query: str,
    agent_type: str,
    tools: Optional[List[str]] = None,
) -> Dict[str, Any]:
    from src.agents.orchestrator import orchestrator

    logger.info(f"Celery task started: {task_id} ({agent_type})")
    start = time.time()

    _run_async(task_service.update_task_status(task_id, "running"))

    try:
        result = _run_async(orchestrator.execute(query=query, agent_type=agent_type, tools=tools))
        elapsed = time.time() - start
        _run_async(task_service.save_result(task_id, result, elapsed))
        logger.info(f"Celery task completed: {task_id} in {elapsed:.2f}s")
        return {"task_id": task_id, "status": "completed", "result": result}
    except Exception as e:
        elapsed = time.time() - start
        _run_async(task_service.save_error(task_id, str(e)))
        logger.error(f"Celery task failed: {task_id} - {e}")
        raise self.retry(exc=e, countdown=5)
