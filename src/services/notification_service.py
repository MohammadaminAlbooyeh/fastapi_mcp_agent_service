from __future__ import annotations

from typing import Any, Dict


class NotificationService:
    async def send_event(
        self, event_type: str, data: Dict[str, Any]
    ) -> bool:
        return True

    async def notify_task_completed(self, task_id: str) -> bool:
        return await self.send_event(
            "task.completed", {"task_id": task_id}
        )

    async def notify_task_failed(self, task_id: str, error: str) -> bool:
        return await self.send_event(
            "task.failed", {"task_id": task_id, "error": error}
        )


notification_service = NotificationService()
