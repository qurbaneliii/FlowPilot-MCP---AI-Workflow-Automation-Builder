import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.workflow.exceptions import NodeTimeoutError


T = TypeVar("T")


async def with_timeout(fn: Callable[[], Awaitable[T]], *, timeout_seconds: float) -> T:
    try:
        return await asyncio.wait_for(fn(), timeout=timeout_seconds)
    except TimeoutError as exc:
        raise NodeTimeoutError(timeout_seconds=timeout_seconds) from exc
