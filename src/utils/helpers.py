from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any


def generate_task_id() -> str:
    return str(uuid.uuid4())


def compute_hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def timestamp() -> str:
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 100) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."
