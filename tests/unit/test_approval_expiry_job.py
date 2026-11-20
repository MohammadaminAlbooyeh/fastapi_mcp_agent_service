from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.services.approval_expiry_job import expire_pending_approvals


class TestApprovalExpiryJob:
    def test_expires_only_pending_rows_past_their_deadline(self) -> None:
        expired_row = MagicMock(status="pending")
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = [expired_row]

        with patch(
            "src.services.approval_expiry_job.SessionLocal", return_value=mock_db
        ):
            count = expire_pending_approvals.run()

        assert count == 1
        assert expired_row.status == "expired"
        mock_db.commit.assert_called_once()
        mock_db.close.assert_called_once()

    def test_no_op_when_nothing_is_expired(self) -> None:
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.all.return_value = []

        with patch(
            "src.services.approval_expiry_job.SessionLocal", return_value=mock_db
        ):
            count = expire_pending_approvals.run()

        assert count == 0
        mock_db.commit.assert_called_once()
