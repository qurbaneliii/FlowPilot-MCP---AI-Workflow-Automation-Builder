import asyncio
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.api.deps import engine
from app.core.config import get_settings


router = APIRouter()


DependencyStatus = Literal["ok", "error", "not_configured"]
ServiceSeverity = Literal["success", "warning", "info", "error"]


class HealthDependencies(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database: DependencyStatus
    openai: DependencyStatus


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    version: str
    dependencies: HealthDependencies
    services: dict[str, "HealthServiceStatus"]
    ui: "HealthUiStatus"


class HealthServiceStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str
    label: str
    severity: ServiceSeverity
    blocking: bool = False


class HealthUiStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_mode_label: str
    storage_mode_label: str
    show_database_warning: bool
    database_warning_blocks_demo: bool


async def check_database(
    database_engine: AsyncEngine = engine, timeout_seconds: float = 2.0
) -> DependencyStatus:
    async def probe() -> None:
        async with database_engine.connect() as connection:
            await connection.execute(text("select 1"))

    try:
        await asyncio.wait_for(probe(), timeout=timeout_seconds)
    except Exception:
        return "error"
    return "ok"


async def check_openai() -> DependencyStatus:
    settings = get_settings()
    if not settings.openai_api_key:
        return "not_configured"
    return "ok"


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Check service health",
    description="Performs lightweight checks for the API process, database connectivity, and OpenAI configuration.",
)
async def health() -> HealthResponse:
    settings = get_settings()
    database_status = await check_database()
    openai_status = await check_openai()
    services = _services(
        database_status=database_status,
        openai_status=openai_status,
        mcp_mode=settings.github_mcp_mode,
        agent_mode=settings.openai_agent_mode,
    )
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        dependencies=HealthDependencies(
            database=database_status,
            openai=openai_status,
        ),
        services=services,
        ui=HealthUiStatus(
            primary_mode_label=services["mcp"].label,
            storage_mode_label=services["database"].label,
            show_database_warning=services["database"].status != "ok",
            database_warning_blocks_demo=services["database"].blocking,
        ),
    )


def _services(
    *,
    database_status: DependencyStatus,
    openai_status: DependencyStatus,
    mcp_mode: str,
    agent_mode: str,
) -> dict[str, HealthServiceStatus]:
    database = _database_service(database_status)
    return {
        "backend": HealthServiceStatus(
            status="ok",
            label="Backend connected",
            severity="success",
        ),
        "database": database,
        "mcp": HealthServiceStatus(
            status="real" if mcp_mode == "real" else "mock",
            label="Real MCP" if mcp_mode == "real" else "Mock MCP",
            severity="success" if mcp_mode == "real" else "info",
        ),
        "openai": HealthServiceStatus(
            status=agent_mode if openai_status == "ok" else "not_configured",
            label=_openai_label(openai_status, agent_mode),
            severity=(
                "success" if openai_status == "ok" and agent_mode == "real" else "info"
            ),
            blocking=False,
        ),
    }


def _database_service(status: DependencyStatus) -> HealthServiceStatus:
    if status == "ok":
        return HealthServiceStatus(
            status="ok",
            label="Database connected",
            severity="success",
            blocking=False,
        )
    if status == "not_configured":
        return HealthServiceStatus(
            status="not_configured",
            label="DB not configured",
            severity="warning",
            blocking=False,
        )
    return HealthServiceStatus(
        status="not_configured",
        label="Memory mode",
        severity="warning",
        blocking=False,
    )


def _openai_label(status: DependencyStatus, agent_mode: str) -> str:
    if agent_mode == "fake":
        return "Fake agent mode"
    if status == "not_configured":
        return "OpenAI not configured"
    return "OpenAI connected"
