from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class TaskRecord(Base):
    __tablename__ = "tasks"

    task_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    query = Column(Text, nullable=False)
    agent_type = Column(String, nullable=False)
    tools = Column(JSONB, default=[])
    status = Column(String, default="pending")
    result = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    execution_time = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    request_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    tool_args = Column(JSONB, nullable=False)
    agent_type = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    status = Column(String, default="pending")
    requester = Column(String, nullable=True)
    approver = Column(String, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
