from __future__ import annotations

from typing import List

from pydantic import model_validator
from pydantic_settings import BaseSettings

_INSECURE_SECRET_KEY = "change-me-in-production"
_INSECURE_API_KEY = "dev-api-key"


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    database_url: str = "postgresql://user:password@localhost:5432/agent_service"
    database_pool_size: int = 20

    redis_url: str = "redis://localhost:6379/0"

    llm_model: str = "claude-3-sonnet-20240229"
    anthropic_api_key: str = ""

    openai_api_key: str = ""
    google_api_key: str = ""
    search_api_key: str = ""

    secret_key: str = "change-me-in-production"
    api_key: str = "dev-api-key"
    algorithm: str = "HS256"
    access_token_expiry: int = 3600

    webhook_url: str = ""

    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    sentry_dsn: str = ""

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @property
    def cors_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    @model_validator(mode="after")
    def _forbid_insecure_production_secrets(self) -> "Settings":
        if self.environment == "production":
            if self.secret_key == _INSECURE_SECRET_KEY:
                raise ValueError(
                    "SECRET_KEY must be overridden with a strong value when ENVIRONMENT=production"
                )
            if self.api_key == _INSECURE_API_KEY:
                raise ValueError(
                    "API_KEY must be overridden with a strong value when ENVIRONMENT=production"
                )
        return self

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
