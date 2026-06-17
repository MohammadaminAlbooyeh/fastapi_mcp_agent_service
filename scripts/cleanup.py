#!/usr/bin/env python3
from __future__ import annotations

from src.config.logger import logger
from src.database.connection import SessionLocal


def cleanup() -> None:
    logger.info("Cleaning up...")
    db = SessionLocal()
    try:
        db.execute("DELETE FROM tasks WHERE status = 'failed'")
        db.commit()
        logger.info("Cleanup complete.")
    finally:
        db.close()


if __name__ == "__main__":
    cleanup()
