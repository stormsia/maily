"""
Async retry decorator with exponential backoff and jitter.

Usage::

    from .retry import async_retry

    @async_retry(max_attempts=3, base_delay=0.5)
    async def flaky_api_call():
        ...
"""
from __future__ import annotations

import asyncio
import functools
import logging
import random
from collections.abc import Callable
from typing import Any, TypeVar

from .exceptions import MailAPIError, MailAuthError, MailNotFoundError, MailRateLimitError

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# These error types are NEVER retried — retrying auth/404 errors is pointless
_NO_RETRY: tuple[type[Exception], ...] = (MailAuthError, MailNotFoundError)


def async_retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 30.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (MailAPIError,),
) -> Callable[[F], F]:
    """
    Decorator that retries an async function on transient failures.

    Args:
        max_attempts:  Maximum total attempts (1 = no retry).
        base_delay:    Initial delay in seconds before second attempt.
        max_delay:     Upper cap on any single delay (seconds).
        jitter:        Multiply computed delay by random factor in [0.5, 1.0]
                       to prevent thundering herd when many coroutines retry.
        exceptions:    Exception types that trigger a retry.
                       ``MailAuthError`` and ``MailNotFoundError`` are always
                       re-raised immediately regardless of this setting.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)

                except _NO_RETRY:
                    raise  # auth/404 — re-raise immediately

                except exceptions as exc:
                    last_exc = exc

                    if attempt >= max_attempts:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__qualname__,
                            max_attempts,
                            exc,
                        )
                        break

                    # Honour Retry-After header when rate-limited
                    if isinstance(exc, MailRateLimitError) and exc.retry_after:
                        delay = min(exc.retry_after, max_delay)
                    else:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)

                    if jitter:
                        delay *= 0.5 + random.random() * 0.5  # noqa: S311

                    logger.warning(
                        "%s attempt %d/%d failed (%s). Retrying in %.2fs…",
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
