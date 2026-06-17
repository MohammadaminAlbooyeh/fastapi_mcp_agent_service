from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.orm import Session

from src.database.connection import SessionLocal


async def get_db() -> AsyncGenerator[Session, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
