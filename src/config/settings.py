from __future__ import annotations

from typing import List

from pydantic_settings import BaseSettings


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
    algorithm: str = "HS256"
    access_token_expiry: int = 3600

    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    sentry_dsn: str = ""

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    @property
    def cors_allowed_origins(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    model_config = {"env_file": ".env", "case_sensitive": False}


settings = Settings()
