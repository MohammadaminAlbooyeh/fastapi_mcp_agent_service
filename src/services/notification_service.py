from __future__ import annotations

from typing import Any, Dict

import httpx

from src.config.logger import logger
from src.config.settings import settings


class NotificationService:
    async def send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        if not settings.webhook_url:
            return True
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    settings.webhook_url,
                    json={"event": event_type, "data": data},
                )
                response.raise_for_status()
                logger.info(f"Webhook sent: {event_type} -> {settings.webhook_url}")
                return True
        except Exception as e:
            logger.warning(f"Webhook failed ({event_type}): {e}")
            return False

    async def notify_task_completed(self, task_id: str, result: Any = None) -> bool:
        return await self.send_event("task.completed", {"task_id": task_id, "result": result})

    async def notify_task_failed(self, task_id: str, error: str) -> bool:
        return await self.send_event("task.failed", {"task_id": task_id, "error": error})


notification_service = NotificationService()
