from __future__ import annotations

import json
import time
from typing import Any, AsyncGenerator, Dict, Optional

from src.agents.orchestrator import orchestrator
from src.config.logger import logger
from src.services.llm_service import llm_service
from src.services.notification_service import notification_service
from src.services.task_service import task_service


class AgentService:
    async def execute(
        self,
        query: str,
        agent_type: str,
        tools: Optional[list[str]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        task = await task_service.create_task(query, agent_type, tools)
        task_id = task.task_id
        await task_service.update_task_status(task_id, "running")
        start = time.time()
        try:
            result = await orchestrator.execute(query=query, agent_type=agent_type, tools=tools, **kwargs)
            elapsed = time.time() - start
            await task_service.save_result(task_id, result, elapsed)
            await notification_service.notify_task_completed(task_id, result)
            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "execution_time": elapsed,
            }
        except Exception as e:
            elapsed = time.time() - start
            await task_service.save_error(task_id, str(e))
            await notification_service.notify_task_failed(task_id, str(e))
            return {
                "task_id": task_id,
                "status": "failed",
                "error": str(e),
                "execution_time": elapsed,
            }

    async def stream(
        self,
        query: str,
        agent_type: str,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        task = await task_service.create_task(query, agent_type)
        task_id = task.task_id
        await task_service.update_task_status(task_id, "running")

        yield f"data: {json.dumps({'event': 'start', 'task_id': task_id, 'agent': agent_type})}\n\n"
        yield f"data: {json.dumps({'event': 'status', 'message': f'Processing query: {query}'})}\n\n"

        try:
            result = await orchestrator.execute(query=query, agent_type=agent_type, **kwargs)
            llm_text = result.get("result", {}).get("llm_response", "")
            if llm_text:
                for chunk in llm_text.split(" "):
                    yield f"data: {json.dumps({'event': 'token', 'task_id': task_id, 'token': chunk + ' '})}\n\n"
            await task_service.save_result(task_id, result)
            yield f"data: {json.dumps({'event': 'result', 'task_id': task_id, 'result': str(result)})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'task_id': task_id, 'status': 'completed'})}\n\n"
            await notification_service.notify_task_completed(task_id, result)
        except Exception as e:
            await task_service.save_error(task_id, str(e))
            await notification_service.notify_task_failed(task_id, str(e))
            yield f"data: {json.dumps({'event': 'error', 'task_id': task_id, 'error': str(e)})}\n\n"

    async def cancel(self, task_id: str) -> bool:
        task = await task_service.get_task(task_id)
        if task and task.status in ("pending", "running"):
            await task_service.update_task_status(task_id, "cancelled")
            logger.info(f"Task cancelled: {task_id}")
            return True
        return False


agent_service = AgentService()
