#!/usr/bin/env python3
from __future__ import annotations

from src.config.logger import logger
from src.database.connection import SessionLocal
from src.database.models import TaskRecord


def seed_data() -> None:
    logger.info("Seeding test data...")
    db = SessionLocal()
    try:
        sample_tasks = [
            TaskRecord(
                query="Get all users where age > 25",
                agent_type="query",
                tools=["database_tool"],
                status="completed",
            ),
            TaskRecord(
                query="Calculate average order value",
                agent_type="processor",
                tools=["calculator_tool"],
                status="completed",
            ),
        ]
        db.add_all(sample_tasks)
        db.commit()
        logger.info(f"Seeded {len(sample_tasks)} tasks.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
