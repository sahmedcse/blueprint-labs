"""Typed settings, read from the environment once at startup."""

from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_SCHEMES = {"postgres", "postgresql", "postgresql+asyncpg"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    log_level: str = "info"

    @field_validator("database_url")
    @classmethod
    def use_asyncpg_driver(cls, value: str) -> str:
        """Accept the plain postgres:// URLs that CI and Go services use.

        asyncpg wants the +asyncpg scheme and calls libpq's sslmode "ssl".
        """
        parts = urlsplit(value)
        if parts.scheme not in _SCHEMES:
            raise ValueError("DATABASE_URL must be a postgres:// or postgresql:// URL")
        query = [("ssl" if k == "sslmode" else k, v) for k, v in parse_qsl(parts.query)]
        return urlunsplit(parts._replace(scheme="postgresql+asyncpg", query=urlencode(query)))


@lru_cache
def get_settings() -> Settings:
    """Load and validate settings. Fails fast when DATABASE_URL is missing."""
    return Settings()
