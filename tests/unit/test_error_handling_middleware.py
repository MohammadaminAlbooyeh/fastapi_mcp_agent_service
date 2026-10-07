from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.middleware import ErrorHandlingMiddleware
from src.config.settings import settings


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ErrorHandlingMiddleware)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("connection to postgresql://admin:s3cr3t@10.0.0.5/prod failed")

    return app


class TestErrorHandlingMiddleware:
    def test_hides_raw_exception_message_outside_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", False)
        client = TestClient(_build_app(), raise_server_exceptions=False)

        response = client.get("/boom")

        assert response.status_code == 500
        assert response.json() == {"detail": "Internal server error"}

    def test_shows_exception_message_in_debug(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(settings, "debug", True)
        client = TestClient(_build_app(), raise_server_exceptions=False)

        response = client.get("/boom")

        assert response.status_code == 500
        assert "s3cr3t" in response.json()["detail"]
