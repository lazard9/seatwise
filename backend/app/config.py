from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

MIN_SECRET_BYTES = 32
PLACEHOLDER_MARKER = "change-me"


class Settings(BaseSettings):
    """Application settings, read from the environment and `backend/.env`.

    Construction fails on a missing or weak secret, so the app refuses to start.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    mongodb_url: str = "mongodb://localhost:27017/?replicaSet=rs0"
    database_name: str = "seatwise"
    mongodb_timeout_ms: int = Field(default=5000, ge=100)
    jwt_secret: str
    access_token_expire_minutes: int = Field(default=15, ge=1, le=60)
    # NoDecode: the env value is a comma-separated string, not JSON.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173"]

    @field_validator("jwt_secret")
    @classmethod
    def secret_must_be_strong(cls, value: str) -> str:
        if PLACEHOLDER_MARKER in value:
            raise ValueError("JWT_SECRET still has the placeholder value from .env.example")
        if len(value.encode()) < MIN_SECRET_BYTES:
            raise ValueError(f"JWT_SECRET must be at least {MIN_SECRET_BYTES} bytes")
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    # Required values come from the environment, not from arguments.
    return Settings()  # type: ignore[call-arg]
