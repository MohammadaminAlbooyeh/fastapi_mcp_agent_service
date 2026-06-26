from __future__ import annotations

from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_tasks_task_id",
        "tasks",
        ["task_id"],
        unique=True,
    )
    op.create_index(
        "ix_tasks_status",
        "tasks",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_created_at",
        "tasks",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_agent_type",
        "tasks",
        ["agent_type"],
        unique=False,
    )
    op.create_index(
        "ix_tasks_status_created_at",
        "tasks",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_tasks_status_created_at", table_name="tasks")
    op.drop_index("ix_tasks_agent_type", table_name="tasks")
    op.drop_index("ix_tasks_created_at", table_name="tasks")
    op.drop_index("ix_tasks_status", table_name="tasks")
    op.drop_index("ix_tasks_task_id", table_name="tasks")
