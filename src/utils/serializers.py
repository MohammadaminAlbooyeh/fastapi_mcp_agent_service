from __future__ import annotations

import json
from datetime import datetime
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def serialize(data: Any) -> str:
    return json.dumps(data, cls=CustomJSONEncoder)


def deserialize(data: str) -> Any:
    return json.loads(data)
