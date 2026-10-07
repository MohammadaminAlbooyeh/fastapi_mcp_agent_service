from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from src.config.settings import settings

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "agent_service.log")


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

    # Relies on the "logs" directory existing relative to the process's CWD
    # (previously only guaranteed by a tracked .gitkeep file) — that breaks
    # whenever the CWD assumption doesn't hold, e.g. inside a container image
    # built with a .dockerignore that excludes "logs". Creating it here makes
    # module import robust regardless of deployment method.
    os.makedirs(LOG_DIR, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE,
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
