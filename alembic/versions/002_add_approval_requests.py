from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "approval_requests",
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("tool_name", sa.String(), nullable=False),
        sa.Column("tool_args", JSONB(), nullable=False),
        sa.Column("agent_type", sa.String(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=True, default="pending"),
        sa.Column("requester", sa.String(), nullable=True),
        sa.Column("approver", sa.String(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        "ix_approval_requests_status",
        "approval_requests",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_task_id",
        "approval_requests",
        ["task_id"],
        unique=False,
    )
    op.create_index(
        "ix_approval_requests_expires_at",
        "approval_requests",
        ["expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_approval_requests_expires_at", table_name="approval_requests")
    op.drop_index("ix_approval_requests_task_id", table_name="approval_requests")
    op.drop_index("ix_approval_requests_status", table_name="approval_requests")
    op.drop_table("approval_requests")
