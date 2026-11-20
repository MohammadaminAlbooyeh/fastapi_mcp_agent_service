from __future__ import annotations

from datetime import datetime

from src.config.celery_app import celery_app
from src.config.logger import logger
from src.database.connection import SessionLocal
from src.database.models import ApprovalRequest as ApprovalRequestModel


@celery_app.task(name="expire_pending_approvals")
def expire_pending_approvals() -> int:
    """Celery Beat task (runs every minute): sweeps approval requests whose
    `expires_at` has passed but are still 'pending' and marks them expired.

    Replaces any in-process timer/asyncio.sleep-based expiry — a timer like
    that is lost whenever its container is scaled down or restarted, so
    expiry needs to live in a scheduled job that checks the database
    instead. Idempotent: re-running against an already-expired row is a
    no-op, so duplicate Beat schedulers firing this concurrently is safe.
    """
    db = SessionLocal()
    try:
        now = datetime.now()
        expired = (
            db.query(ApprovalRequestModel)
            .filter(
                ApprovalRequestModel.status == "pending",
                ApprovalRequestModel.expires_at < now,
            )
            .all()
        )
        for request in expired:
            request.status = "expired"
            request.updated_at = now
        db.commit()
        if expired:
            logger.info(f"Expired {len(expired)} pending approval request(s)")
        return len(expired)
    finally:
        db.close()
