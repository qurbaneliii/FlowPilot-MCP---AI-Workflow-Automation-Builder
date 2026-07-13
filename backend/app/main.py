from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

import app.workflow.nodes  # noqa: F401
from app.api.v1.approvals import router as approvals_router
from app.api.v1.health import router as health_router
from app.api.v1.runs import router as runs_router
from app.api.v1.workflows import router as workflows_router
from app.core.api_errors import ApiError, api_error_handler, validation_error_handler
from app.core.config import get_settings
from app.core.logging import configure_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="FlowPilot MCP API",
        version=settings.app_version,
        description="Backend API for the FlowPilot MCP AI Workflow Automation Builder.",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_exception_handler(ApiError, api_error_handler)
    application.add_exception_handler(RequestValidationError, validation_error_handler)
    application.include_router(health_router, prefix="/api/v1", tags=["health"])
    application.include_router(workflows_router, prefix="/api/v1", tags=["workflows"])
    application.include_router(runs_router, prefix="/api/v1", tags=["runs"])
    application.include_router(approvals_router, prefix="/api/v1", tags=["approvals"])
    return application


app = create_app()
