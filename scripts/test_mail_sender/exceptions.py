"""Exceptions for autonomous test mail sender."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import AttemptInfo


class EmailSenderError(Exception):
    """Base exception for all email sending failures."""


class InvalidEmailError(EmailSenderError):
    """Raised when the specified recipient address has an invalid format."""

    def __init__(self, email: str, reason: str = "Invalid email format") -> None:
        self.email = email
        self.reason = reason
        super().__init__(f"{reason}: '{email}'")


class ProviderError(EmailSenderError):
    """Raised when an individual email provider fails."""

    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        self.provider = provider
        self.status_code = status_code
        self.response_text = response_text
        prefix = f"[{provider}]"
        if status_code is not None:
            prefix = f"[{provider} HTTP {status_code}]"
        super().__init__(f"{prefix} {message}")


class PrimaryProviderError(ProviderError):
    """Raised when primary provider (wesendtestmail.com) fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(
            "wesendtestmail",
            message,
            status_code=status_code,
            response_text=response_text,
        )


class FallbackProviderError(ProviderError):
    """Raised when fallback provider (xeramail.com) fails."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_text: str | None = None,
    ) -> None:
        super().__init__(
            "xeramail",
            message,
            status_code=status_code,
            response_text=response_text,
        )


class AllProvidersFailedError(EmailSenderError):
    """Raised when all configured providers (primary + fallback) failed to deliver."""

    def __init__(self, email: str, attempts: list[AttemptInfo]) -> None:
        self.email = email
        self.attempts = attempts
        summary = "; ".join(
            f"{a.provider} failed: {a.error or f'HTTP {a.status_code}'}" for a in attempts
        )
        super().__init__(f"All email send providers failed for '{email}': {summary}")
