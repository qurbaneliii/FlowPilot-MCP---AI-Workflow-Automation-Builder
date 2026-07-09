import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar

from app.workflow.exceptions import RetryExhaustedError, TransientError


T = TypeVar("T")


async def with_retry(
    fn: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    multiplier: float = 2.0,
    retryable_exceptions: tuple[type[Exception], ...] = (TransientError,),
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> T:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return await fn()
        except retryable_exceptions as exc:
            last_error = exc
            if attempt == max_attempts:
                raise RetryExhaustedError(last_error) from last_error
            delay = base_delay * multiplier ** (attempt - 1)
            await sleep(delay)

    raise RetryExhaustedError(last_error or RuntimeError("retry failed"))
