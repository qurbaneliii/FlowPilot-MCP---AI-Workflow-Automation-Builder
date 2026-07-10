from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


class ApiError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        severity: str | None = None,
        retryable: bool | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details or {}
        self.severity = severity or _default_severity(status_code)
        self.retryable = retryable if retryable is not None else status_code >= 500
        super().__init__(message)


async def api_error_handler(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "severity": exc.severity,
                "retryable": exc.retryable,
            }
        },
    )


async def validation_error_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": {"errors": exc.errors()},
                "severity": "warning",
                "retryable": False,
            }
        },
    )


def _default_severity(status_code: int) -> str:
    if status_code >= 500:
        return "error"
    if status_code in {401, 403, 404, 409, 422}:
        return "warning"
    return "info"
