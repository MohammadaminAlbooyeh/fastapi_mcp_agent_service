from __future__ import annotations

import json
import logging
import sys

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("agent_service")
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # CloudWatch Logs ingests stdout/stderr from the container; writing to a
    # local file would be lost whenever the container is replaced.
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(JSONFormatter())

    if not logger.handlers:
        logger.addHandler(stdout_handler)

    return logger


logger = setup_logging()
