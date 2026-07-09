from functools import lru_cache
from uuid import UUID

from pydantic import ConfigDict, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    debug_payload_logging: bool = False
    database_url: str = (
        "postgresql+asyncpg://flowpilot:flowpilot@localhost:5432/flowpilot"
    )
    default_user_id: UUID = Field(default=UUID("00000000-0000-0000-0000-000000000001"))
    openai_api_key: str | None = None
    openai_mcp_server_url: str | None = None
    github_mcp_mode: str = "mock"
    github_mcp_server_url: str | None = None
    github_token: str | None = None
    filesystem_mcp_mode: str = "mock"
    filesystem_mcp_root: str = "/workspace"


@lru_cache
def get_settings() -> Settings:
    return Settings()
