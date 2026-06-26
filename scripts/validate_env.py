#!/usr/bin/env python3
"""
Environment Validation Script

Validates all required environment variables and connectivity to external services.
Run this before starting the service in production.
"""

from __future__ import annotations

import asyncio
import os
import sys
from typing import Dict, List, Tuple

import asyncpg
import httpx
import redis


class EnvironmentValidator:
    REQUIRED_VARS = {
        "DATABASE_URL": "PostgreSQL connection string",
        "REDIS_URL": "Redis connection URL",
        "ANTHROPIC_API_KEY": "Anthropic API key for Claude",
        "SECRET_KEY": "Secret key for JWT signing",
        "API_KEY": "API key for service authentication",
    }

    OPTIONAL_VARS = {
        "ENVIRONMENT": "Deployment environment (development/production)",
        "DEBUG": "Debug mode (true/false)",
        "LOG_LEVEL": "Logging level (DEBUG/INFO/WARNING/ERROR)",
        "ALLOWED_ORIGINS": "CORS allowed origins",
        "WEBHOOK_URL": "Webhook URL for notifications",
        "OPENAI_API_KEY": "OpenAI API key (optional)",
        "GOOGLE_API_KEY": "Google API key (optional)",
        "SEARCH_API_KEY": "Search API key (optional)",
        "SENTRY_DSN": "Sentry DSN for error tracking (optional)",
    }

    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []

    def validate_required_env_vars(self) -> bool:
        print("Validating required environment variables...")
        missing = []
        for var, description in self.REQUIRED_VARS.items():
            value = os.getenv(var)
            if not value:
                missing.append(f"  ✗ {var}: {description}")
                self.errors.append(f"Missing required variable: {var}")
            else:
                masked_value = (
                    value[:10] + "***" if len(value) > 10 else "***"
                )
                print(f"  ✓ {var}: {masked_value}")
                self.info.append(f"Found {var}")

        if missing:
            print("\nMissing required variables:")
            for msg in missing:
                print(msg)
            return False
        return True

    def validate_optional_env_vars(self) -> bool:
        print("\nValidating optional environment variables...")
        for var, description in self.OPTIONAL_VARS.items():
            value = os.getenv(var)
            if value:
                masked_value = (
                    value[:10] + "***" if len(value) > 10 else "***"
                )
                print(f"  ✓ {var}: {masked_value}")
                self.info.append(f"Found {var}")
            else:
                print(f"  ⊘ {var}: Not set (optional)")
                self.warnings.append(f"Optional variable not set: {var}")

        return True

    async def validate_database_connection(self) -> bool:
        print("\nValidating database connection...")
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            self.errors.append("DATABASE_URL not set, skipping database validation")
            return False

        try:
            conn = await asyncpg.connect(db_url)
            version = await conn.fetchval("SELECT version()")
            print(f"  ✓ PostgreSQL connected: {version.split(',')[0]}")
            self.info.append("Database connection successful")
            await conn.close()
            return True
        except Exception as e:
            self.errors.append(f"Database connection failed: {str(e)}")
            print(f"  ✗ Database connection failed: {e}")
            return False

    def validate_redis_connection(self) -> bool:
        print("\nValidating Redis connection...")
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            self.warnings.append("REDIS_URL not set, Redis will be unavailable")
            print("  ⊘ Redis not configured (optional for development)")
            return True

        try:
            r = redis.from_url(redis_url)
            info = r.info()
            print(f"  ✓ Redis connected: v{info.get('redis_version')}")
            self.info.append("Redis connection successful")
            r.close()
            return True
        except Exception as e:
            self.warnings.append(f"Redis connection failed: {str(e)}")
            print(f"  ⊘ Redis connection failed (will use in-memory cache): {e}")
            return False

    async def validate_api_connectivity(self) -> bool:
        print("\nValidating external API connectivity...")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            self.warnings.append("ANTHROPIC_API_KEY not set, skipping API validation")
            return True

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.anthropic.com/",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5,
                )
                if response.status_code in [200, 401, 403]:
                    print("  ✓ Anthropic API accessible")
                    self.info.append("Anthropic API connectivity verified")
                    return True
                else:
                    self.warnings.append(
                        f"Anthropic API returned {response.status_code}"
                    )
                    print(f"  ⚠ Anthropic API status: {response.status_code}")
                    return False
        except Exception as e:
            self.warnings.append(f"Anthropic API check failed: {str(e)}")
            print(f"  ⚠ Anthropic API check failed: {e}")
            return False

    def validate_jwt_secret(self) -> bool:
        print("\nValidating JWT configuration...")
        secret = os.getenv("SECRET_KEY")
        if not secret:
            self.errors.append("SECRET_KEY not set")
            return False

        if len(secret) < 32:
            self.warnings.append(
                f"SECRET_KEY is short ({len(secret)} chars), minimum 32 recommended"
            )
            print(f"  ⚠ SECRET_KEY length: {len(secret)} (min 32 recommended)")
            return False

        print(f"  ✓ SECRET_KEY length: {len(secret)} chars")
        self.info.append("JWT secret key has adequate length")
        return True

    def validate_logging_config(self) -> bool:
        print("\nValidating logging configuration...")
        log_level = os.getenv("LOG_LEVEL", "INFO")
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if log_level not in valid_levels:
            self.warnings.append(f"Invalid LOG_LEVEL: {log_level}")
            print(f"  ⚠ Invalid LOG_LEVEL: {log_level}")
            return False

        print(f"  ✓ LOG_LEVEL: {log_level}")
        self.info.append(f"Logging level set to {log_level}")
        return True

    def validate_cors_config(self) -> bool:
        print("\nValidating CORS configuration...")
        origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
        origins_list = [o.strip() for o in origins.split(",")]
        print(f"  ✓ CORS origins configured: {len(origins_list)} origin(s)")
        self.info.append(f"CORS configured for {len(origins_list)} origin(s)")
        return True

    async def run_all_validations(self) -> bool:
        print("=" * 60)
        print("FastAPI MCP Agent Service - Environment Validator")
        print("=" * 60)
        print()

        all_valid = True

        all_valid &= self.validate_required_env_vars()
        all_valid &= self.validate_optional_env_vars()
        all_valid &= await self.validate_database_connection()
        all_valid &= self.validate_redis_connection()
        all_valid &= await self.validate_api_connectivity()
        all_valid &= self.validate_jwt_secret()
        all_valid &= self.validate_logging_config()
        all_valid &= self.validate_cors_config()

        self.print_summary()
        return all_valid

    def print_summary(self) -> None:
        print()
        print("=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        if self.info:
            print(f"\n✓ Info ({len(self.info)}):")
            for msg in self.info[:5]:
                print(f"  • {msg}")
            if len(self.info) > 5:
                print(f"  ... and {len(self.info) - 5} more")

        if self.warnings:
            print(f"\n⚠ Warnings ({len(self.warnings)}):")
            for msg in self.warnings:
                print(f"  • {msg}")

        if self.errors:
            print(f"\n✗ Errors ({len(self.errors)}):")
            for msg in self.errors:
                print(f"  • {msg}")
            print(
                "\nFix the above errors before running the service in production."
            )
        else:
            print("\n✓ All validations passed!")

        print()


async def main() -> int:
    validator = EnvironmentValidator()
    valid = await validator.run_all_validations()
    return 0 if valid else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
