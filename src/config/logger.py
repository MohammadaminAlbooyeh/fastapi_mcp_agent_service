from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler

from src.config.settings import settings


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("agent_service")
    logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(log_level)
    stdout_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        "logs/agent_service.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(stdout_handler)
        logger.addHandler(file_handler)

    return logger


logger = setup_logging()
