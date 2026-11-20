from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

import aioboto3

from src.config.settings import settings

_session = aioboto3.Session()


@asynccontextmanager
async def get_s3_client() -> AsyncIterator[Any]:
    async with _session.client("s3", region_name=settings.aws_region) as client:
        yield client
