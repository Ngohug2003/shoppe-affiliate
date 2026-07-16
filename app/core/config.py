from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=True
    )

    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_NAME: str = "shopee-affiliate-bot"
    APP_BASE_URL: AnyHttpUrl = AnyHttpUrl("http://localhost:8000")
    SECRET_KEY: str = Field(default="change-me", min_length=8)
    JWT_SECRET: str = Field(default="change-me", min_length=8)
    JWT_ALGORITHM: Literal["HS256"] = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, ge=1, le=10080)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:change-me@postgres:5432/shopee_bot"
    TIMEZONE: str = "Asia/Ho_Chi_Minh"
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    TRUSTED_HOSTS: list[str] = ["localhost", "127.0.0.1"]
    ENABLE_DEBUGPY: bool = False
    DEBUGPY_PORT: int = 5678
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: str = Field(default="change-me", min_length=8)
    AFFILIATE_PROVIDER: Literal["mock", "official", "shopee_redirect"] = "mock"
    AFFILIATE_API_BASE_URL: str = ""
    AFFILIATE_API_KEY: str = ""
    AFFILIATE_PUBLISHER_ID: str = ""
    AFFILIATE_TIMEOUT_SECONDS: float = Field(default=10.0, gt=0, le=60)
    CATALOG_API_BASE_URL: AnyHttpUrl = AnyHttpUrl("http://api:8000")
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_POLLING_TIMEOUT_SECONDS: int = Field(default=30, ge=1, le=50)
    TELEGRAM_WEBHOOK_ENABLED: bool = False
    TELEGRAM_WEBHOOK_SECRET: str = Field(default="", max_length=256)


@lru_cache
def get_settings() -> Settings:
    return Settings()
