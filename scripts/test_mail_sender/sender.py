"""Autonomous high-reliability test email dispatcher with primary and fallback providers."""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Literal

from .exceptions import (
    AllProvidersFailedError,
    EmailSenderError,
    FallbackProviderError,
    InvalidEmailError,
    PrimaryProviderError,
)
from .fallback import XeraMailProvider
from .models import AttemptInfo, EmailSendResult
from .primary import WeSendTestMailProvider

logger = logging.getLogger("test_mail_sender")

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SendMode = Literal["auto", "primary", "fallback", "primary_only", "fallback_only"]


class TestEmailSender:
    """Autonomous email sender designed for autotests and CI environments.

    Orchestrates sending test emails using:
    - Primary: WeSendTestMail (https://www.wesendtestmail.com)
    - Fallback: XeraMail (https://xeramail.com)

    Features:
    - Zero dependencies on the main project codebase (100% autonomous).
    - Automatic token and session management for WeSendTestMail.
    - Seamless fallback if the primary service is down, rate-limited, or errors out.
    - Full diagnostic tracking on every attempt (provider, status, duration, error).
    - Asynchronous batch sending with concurrency control.
    """

    __test__ = False

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        proxy: str | None = None,
        cf_clearance: str | None = None,
        primary_provider: WeSendTestMailProvider | None = None,
        fallback_provider: XeraMailProvider | None = None,
    ) -> None:
        self.primary = primary_provider or WeSendTestMailProvider(
            timeout=timeout,
            proxy=proxy,
        )
        self.fallback = fallback_provider or XeraMailProvider(
            timeout=timeout,
            proxy=proxy,
            cf_clearance=cf_clearance,
        )

    async def __aenter__(self) -> TestEmailSender:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close HTTP clients for both providers."""
        await asyncio.gather(
            self.primary.close(),
            self.fallback.close(),
            return_exceptions=True,
        )

    @staticmethod
    def validate_email(email: str) -> None:
        """Validate recipient email address format."""
        if not email or not isinstance(email, str) or not EMAIL_REGEX.match(email.strip()):
            raise InvalidEmailError(email)

    async def send(
        self,
        email: str,
        *,
        mode: SendMode = "auto",
    ) -> EmailSendResult:
        """Send a test email to the target address.

        Args:
            email: Target email address.
            mode: Sending mode:
                - "auto": Try primary first; seamlessly fail over to fallback on error.
                - "primary" / "primary_only": Only attempt primary provider.
                - "fallback" / "fallback_only": Only attempt fallback provider.

        Returns:
            EmailSendResult with delivery information and diagnostic attempt logs.

        Raises:
            InvalidEmailError: When email format is invalid.
            AllProvidersFailedError: When all attempted providers fail.
            PrimaryProviderError: When primary mode is selected and primary fails.
            FallbackProviderError: When fallback mode is selected and fallback fails.
        """
        email = email.strip()
        self.validate_email(email)

        attempts: list[AttemptInfo] = []

        # Mode: Fallback only
        if mode in ("fallback", "fallback_only"):
            logger.info(f"Sending test email to {email} via fallback (xeramail)...")
            return await self.fallback.send(email)

        # Mode: Primary only
        if mode in ("primary", "primary_only"):
            logger.info(f"Sending test email to {email} via primary (wesendtestmail)...")
            return await self.primary.send(email)

        # Mode: Auto (Primary with Fallback)
        logger.info(f"Sending test email to {email} (attempting primary: wesendtestmail)...")
        try:
            res = await self.primary.send(email)
            return res
        except PrimaryProviderError as exc:
            logger.warning(
                f"Primary provider (wesendtestmail) failed for {email}: {exc}. Switching to fallback..."
            )
            # Record failed primary attempt
            attempts.append(
                AttemptInfo(
                    provider=self.primary.provider_name,
                    success=False,
                    status_code=exc.status_code,
                    error=str(exc),
                )
            )

        # Execute fallback
        logger.info(f"Executing fallback provider (xeramail) for {email}...")
        try:
            res = await self.fallback.send(email)
            # Combine primary attempt history with fallback result
            combined_attempts = attempts + res.attempts
            return EmailSendResult(
                email=res.email,
                success=res.success,
                provider=res.provider,
                fallback_used=True,
                message_id=res.message_id,
                detail=res.detail,
                duration_ms=res.duration_ms,
                attempts=combined_attempts,
            )
        except FallbackProviderError as exc:
            logger.error(f"Fallback provider (xeramail) also failed for {email}: {exc}")
            attempts.append(
                AttemptInfo(
                    provider=self.fallback.provider_name,
                    success=False,
                    status_code=exc.status_code,
                    error=str(exc),
                )
            )

        raise AllProvidersFailedError(email, attempts)

    async def send_all(
        self,
        emails: list[str],
        *,
        mode: SendMode = "auto",
        concurrency: int = 5,
    ) -> list[EmailSendResult | Exception]:
        """Send test emails to multiple addresses with concurrency control.

        Returns a list of EmailSendResult objects or caught Exceptions for each email.
        """
        semaphore = asyncio.Semaphore(concurrency)

        async def _worker(target: str) -> EmailSendResult | Exception:
            async with semaphore:
                try:
                    return await self.send(target, mode=mode)
                except EmailSenderError as exc:
                    return exc

        return await asyncio.gather(*[_worker(e) for e in emails])


async def send_test_email(
    email: str,
    *,
    mode: SendMode = "auto",
    timeout: float = 20.0,
    proxy: str | None = None,
    cf_clearance: str | None = None,
) -> EmailSendResult:
    """Convenience helper to send a single test email without manually managing sender lifecycle.

    Usage:
        result = await send_test_email("my_inbox@example.com")
        print(result.provider, result.success)
    """
    async with TestEmailSender(timeout=timeout, proxy=proxy, cf_clearance=cf_clearance) as sender:
        return await sender.send(email, mode=mode)
