#!/usr/bin/env python3
from __future__ import annotations

from src.config.logger import logger
from src.database.connection import engine
from src.database.models import Base


def init_database() -> None:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully.")


if __name__ == "__main__":
    init_database()
