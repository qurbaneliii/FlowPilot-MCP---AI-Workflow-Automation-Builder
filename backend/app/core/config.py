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
    storage_mode: str | None = None
    database_url: str | None = None
    default_user_id: UUID = Field(default=UUID("00000000-0000-0000-0000-000000000001"))
    openai_api_key: str | None = None
    openai_agent_mode: str = "fake"
    openai_agent_model: str = "gpt-4.1"
    openai_mcp_server_url: str | None = None
    github_mcp_mode: str = "mock"
    github_mcp_server_url: str | None = None
    github_token: str | None = None
    filesystem_mcp_mode: str = "mock"
    filesystem_mcp_root: str = "/workspace"

    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def effective_storage_mode(self) -> str:
        """Select durable storage whenever a database URL is configured.

        STORAGE_MODE can explicitly force the safe local memory fallback.
        """
        if self.storage_mode:
            return self.storage_mode.lower()
        return "postgres" if self.database_url else "memory"

    @property
    def allowed_cors_origins(self) -> list[str]:
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
