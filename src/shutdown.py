from __future__ import annotations

import asyncio
import signal

from src.config.logger import logger

is_draining: bool = False


def register_sigterm_handler() -> None:
    """On ECS scale-in, the container receives SIGTERM before being killed.
    Uvicorn itself stops accepting new connections and waits for in-flight
    requests to finish, but nothing tells the ALB/ECS target group to stop
    routing new traffic during that window — that's what flipping
    `is_draining` (read by the /health/ready probe) is for."""
    loop = asyncio.get_event_loop()

    def _handle_sigterm() -> None:
        global is_draining
        is_draining = True
        logger.info("Received SIGTERM — draining in-flight requests")

    try:
        loop.add_signal_handler(signal.SIGTERM, _handle_sigterm)
    except NotImplementedError:
        # add_signal_handler isn't available on some platforms (e.g. Windows);
        # fall back to the standard signal module.
        signal.signal(signal.SIGTERM, lambda *_: _handle_sigterm())
