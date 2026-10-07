from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict, Optional

from src.agents.orchestrator import orchestrator
from src.config.logger import logger
from src.config.settings import settings
from src.services.approval_service import approval_service
from src.services.memory_service import agent_memory_manager
from src.services.notification_service import notification_service
from src.services.task_service import task_service

DEFAULT_EXECUTION_TIMEOUT = 60


class AgentService:
    async def execute(
        self,
        query: str,
        agent_type: str,
        tools: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        require_approval: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        task = await task_service.create_task(query, agent_type, tools)
        task_id = task.task_id
        await task_service.update_task_status(task_id, "running")
        start = time.time()
        try:
            if require_approval:
                req = await approval_service.request_approval(
                    tool_name=agent_type,
                    tool_args={"query": query, "tools": tools},
                    agent_type=agent_type,
                    query=query,
                    task_id=task_id,
                    timeout=kwargs.get("approval_timeout", 300),
                )
                decision = await req.wait_for_decision()
                if decision.value != "approved":
                    elapsed = time.time() - start
                    await task_service.save_error(
                        task_id, f"Approval rejected: {decision.value}"
                    )
                    return {
                        "task_id": task_id,
                        "status": "rejected",
                        "error": f"Approval {decision.value}",
                        "execution_time": elapsed,
                    }

            # max_iterations has no effect: agents run as a single-pass LangGraph
            # pipeline rather than an iterative loop, so there is no iteration
            # count to bound. timeout IS enforced below — without it, a stuck
            # tool call (e.g. a slow external API) would hang the request forever.
            kwargs.pop("max_iterations", None)
            timeout = kwargs.pop("timeout", None) or DEFAULT_EXECUTION_TIMEOUT
            result = await asyncio.wait_for(
                orchestrator.execute(
                    query=query, agent_type=agent_type, tools=tools, **kwargs
                ),
                timeout=timeout,
            )
            elapsed = time.time() - start
            await task_service.save_result(task_id, result, elapsed)
            await notification_service.notify_task_completed(task_id, result)

            if session_id:
                await agent_memory_manager.store_agent_result(
                    session_id, agent_type, query, result
                )

            return {
                "task_id": task_id,
                "status": "completed",
                "result": result,
                "execution_time": elapsed,
            }
        except asyncio.TimeoutError:
            elapsed = time.time() - start
            error = f"Execution timed out after {timeout}s"
            await task_service.save_error(task_id, error)
            await notification_service.notify_task_failed(task_id, error)
            return {
                "task_id": task_id,
                "status": "timeout",
                "error": error,
                "execution_time": elapsed,
            }
        except Exception as e:
            elapsed = time.time() - start
            logger.exception(f"agent_service.execute failed for task {task_id}: {e}")
            await task_service.save_error(task_id, str(e))
            await notification_service.notify_task_failed(task_id, str(e))
            # Exception messages can carry internal details (DB connection
            # strings, file paths, stack traces); only surface them in debug.
            error = str(e) if settings.debug else "Agent execution failed"
            return {
                "task_id": task_id,
                "status": "failed",
                "error": error,
                "execution_time": elapsed,
            }

    async def stream(
        self,
        query: str,
        agent_type: str,
        session_id: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        task = await task_service.create_task(query, agent_type)
        task_id = task.task_id
        await task_service.update_task_status(task_id, "running")

        yield f"data: {json.dumps({'event': 'start', 'task_id': task_id, 'agent': agent_type})}\n\n"
        yield f"data: {json.dumps({'event': 'status', 'message': f'Processing query: {query}'})}\n\n"

        timeout = kwargs.pop("timeout", None) or DEFAULT_EXECUTION_TIMEOUT
        kwargs.pop("max_iterations", None)
        try:
            result = await asyncio.wait_for(
                orchestrator.execute(query=query, agent_type=agent_type, **kwargs),
                timeout=timeout,
            )
            llm_text = result.get("result", {}).get("llm_response", "")
            if llm_text:
                for chunk in llm_text.split(" "):
                    yield f"data: {json.dumps({'event': 'token', 'task_id': task_id, 'token': chunk + ' '})}\n\n"
            await task_service.save_result(task_id, result)

            if session_id:
                await agent_memory_manager.store_agent_result(
                    session_id, agent_type, query, result
                )

            yield f"data: {json.dumps({'event': 'result', 'task_id': task_id, 'result': str(result)})}\n\n"
            yield f"data: {json.dumps({'event': 'done', 'task_id': task_id, 'status': 'completed'})}\n\n"
            await notification_service.notify_task_completed(task_id, result)
        except Exception as e:
            logger.exception(f"agent_service.stream failed for task {task_id}: {e}")
            await task_service.save_error(task_id, str(e))
            await notification_service.notify_task_failed(task_id, str(e))
            error = str(e) if settings.debug else "Agent execution failed"
            yield f"data: {json.dumps({'event': 'error', 'task_id': task_id, 'error': error})}\n\n"

    async def cancel(self, task_id: str, reason: str = "") -> bool:
        task = await task_service.get_task(task_id)
        if task and task.status in ("pending", "running"):
            error = f"Cancelled: {reason}" if reason else None
            await task_service.update_task_status(task_id, "cancelled", error=error)
            logger.info(
                f"Task cancelled: {task_id}" + (f" ({reason})" if reason else "")
            )
            return True
        return False


agent_service = AgentService()
