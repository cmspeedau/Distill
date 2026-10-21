"""Application settings. The only place that reads environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DISTILL_", env_file=".env", extra="ignore")

    database_url: str = Field(default="sqlite:///distill.db")
    storage_dir: str = Field(default="./data")
    timeout: float = Field(default=15.0, gt=0)
    max_response_bytes: int = Field(default=10 * 1024 * 1024, gt=0)
    respect_robots: bool = Field(default=True)
    user_agent: str = Field(default="Distill/1.0")


@lru_cache
def get_settings() -> Settings:
    return Settings()
