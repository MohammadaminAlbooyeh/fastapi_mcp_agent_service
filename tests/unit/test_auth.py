from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from src.api.auth import authenticate_with_api_key, create_access_token, verify_token


class TestAuth:
    def test_create_access_token(self) -> None:
        token = create_access_token({"sub": "test-user", "role": "admin"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self) -> None:
        from datetime import timedelta
        token = create_access_token({"sub": "test"}, expires_delta=timedelta(hours=1))
        assert isinstance(token, str)

    def test_verify_token_dev_no_credentials(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.environment", "development")
        result = verify_token(None)
        assert result["sub"] == "dev-user"
        assert result["role"] == "admin"

    def test_verify_token_production_no_credentials(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.environment", "production")
        with pytest.raises(HTTPException) as exc:
            verify_token(None)
        assert exc.value.status_code == 403

    def test_verify_token_valid(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.environment", "production")
        mock_credentials = MagicMock()
        mock_credentials.credentials = "valid-token"

        with patch("src.api.auth.jwt.decode", return_value={"sub": "user", "role": "user"}):
            result = verify_token(mock_credentials)
            assert result["sub"] == "user"

    def test_verify_token_invalid(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.environment", "production")
        mock_credentials = MagicMock()
        mock_credentials.credentials = "invalid-token"

        with patch("src.api.auth.jwt.decode", side_effect=JWTError("Invalid")):
            with pytest.raises(HTTPException) as exc:
                verify_token(mock_credentials)
            assert exc.value.status_code == 401

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key_valid(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.api_key", "valid-key")
        result = await authenticate_with_api_key("valid-key")
        assert result["sub"] == "api-user"

    @pytest.mark.asyncio
    async def test_authenticate_with_api_key_invalid(self, monkeypatch) -> None:
        monkeypatch.setattr("src.api.auth.settings.api_key", "valid-key")
        with pytest.raises(HTTPException) as exc:
            await authenticate_with_api_key("wrong-key")
        assert exc.value.status_code == 401
