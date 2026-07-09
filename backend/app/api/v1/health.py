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


class HealthDependencies(BaseModel):
    model_config = ConfigDict(extra="forbid")

    database: DependencyStatus
    openai: DependencyStatus


class HealthResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ok"]
    version: str
    dependencies: HealthDependencies


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
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        dependencies=HealthDependencies(
            database=await check_database(),
            openai=await check_openai(),
        ),
    )
