from __future__ import annotations

import asyncio
import functools
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

from ..exceptions import (
    MailAPIError,
    MailAuthError,
    MailConflictError,
    MailNotFoundError,
    MailRateLimitError,
    MailValidationError,
)

logger = logging.getLogger(__name__)
F = TypeVar("F", bound=Callable[..., Any])
_NO_RETRY = (MailAuthError, MailNotFoundError, MailValidationError, MailConflictError)


def async_retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (MailAPIError,),
) -> Callable[[F], F]:
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except _NO_RETRY:
                    raise
                except exceptions as exc:
                    last_exc = exc
                    if attempt >= max_attempts:
                        break
                    if isinstance(exc, MailRateLimitError) and exc.retry_after:
                        delay = min(exc.retry_after, max_delay)
                    else:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                    if jitter:
                        delay *= 0.5 + random.random() * 0.5
                    logger.warning(
                        "%s attempt %d/%d failed (%s). Retrying in %.2fs",
                        func.__qualname__,
                        attempt,
                        max_attempts,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
            assert last_exc is not None
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator
