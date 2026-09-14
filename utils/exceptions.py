"""
Exception hierarchy for mailtmapi.

All exceptions inherit from MailAPIError so callers can catch
either the base class or a specific subclass::

    try:
        await provider.get_messages(token)
    except MailRateLimitError as e:
        await asyncio.sleep(e.retry_after or 5)
    except MailAuthError:
        # refresh token …
        pass
    except MailAPIError as e:
        logger.error("API error %s: %s", e.status_code, e)
"""
from __future__ import annotations


class MailAPIError(Exception):
    """
    Base exception for all mailtmapi errors.

    Attributes:
        status_code: HTTP status code, if the error originated from an HTTP response.
        response_data: Raw response body as a dict (best-effort parse).
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data: dict = response_data or {}

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"{self.__class__.__name__}("
            f"status={self.status_code}, "
            f"message={self.args[0]!r})"
        )


class MailAuthError(MailAPIError):
    """Raised on HTTP 401 / 403 — invalid or expired token."""


class MailNotFoundError(MailAPIError):
    """Raised on HTTP 404 — account or message does not exist."""


class MailRateLimitError(MailAPIError):
    """
    Raised on HTTP 429 — provider rate limit exceeded.

    Attributes:
        retry_after: Seconds to wait before retrying (from Retry-After header),
                     or None if the header was absent.
    """

    def __init__(
        self,
        message: str,
        retry_after: float | None = None,
        **kwargs,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class MailServerError(MailAPIError):
    """Raised on HTTP 5xx — transient server-side error."""


class MailTimeoutError(MailAPIError):
    """Raised when an HTTP request exceeds the configured timeout."""


class MailConflictError(MailAPIError):
    """Raised on HTTP 409 / 422 — e.g. duplicate account registration."""


class MailValidationError(MailAPIError):
    """Raised on local validation failures before any network call."""


# ---------------------------------------------------------------------------
# Back-compat alias (old code used MailTMInvalidResponse)
# ---------------------------------------------------------------------------
MailTMInvalidResponse = MailAPIError