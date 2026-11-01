"""Autonomous test email sending module for CI, integration tests, and automated testing.

Provides unified, resilient test email delivery with primary (WeSendTestMail)
and automatic fallback (XeraMail) providers. Completely decoupled from any
external codebase.
"""

from __future__ import annotations

from .exceptions import (
    AllProvidersFailedError,
    EmailSenderError,
    FallbackProviderError,
    InvalidEmailError,
    PrimaryProviderError,
    ProviderError,
)
from .fallback import XeraMailProvider
from .models import AttemptInfo, EmailSendResult
from .primary import WeSendTestMailProvider
from .sender import TestEmailSender, send_test_email

__all__ = [
    "AllProvidersFailedError",
    "AttemptInfo",
    "EmailSendResult",
    "EmailSenderError",
    "FallbackProviderError",
    "InvalidEmailError",
    "PrimaryProviderError",
    "ProviderError",
    "TestEmailSender",
    "WeSendTestMailProvider",
    "XeraMailProvider",
    "send_test_email",
]
