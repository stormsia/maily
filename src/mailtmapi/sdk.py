"""Deprecated alias module.

The flat SDK client and the section-based client were merged into
``mailtmapi.client``. Importing names from ``mailtmapi.sdk`` still works via
the re-exports below, but emits a ``DeprecationWarning`` — prefer
``from mailtmapi.client import MailTMAPI``.
"""
from __future__ import annotations

import warnings

from .client import (
    AdminAPI,
    ApiError,
    ClientError,
    DomainCache,
    DomainCacheProvider,
    DomainCacheRun,
    GmailAccount,
    GmailAPI,
    GmailCreds,
    HealthAPI,
    HealthOut,
    Mailbox,
    MailboxesAPI,
    MailTMAPI,
    MessageDetail,
    MessagesAPI,
    MessageSource,
    MessageSummary,
    OAuthStart,
    Provider,
    ProvidersAPI,
    Retention,
    SweepResult,
    Target,
)

warnings.warn(
    "mailtmapi.sdk is deprecated; use mailtmapi.client instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "MailTMAPI",
    "ClientError",
    "ApiError",
    "HealthOut",
    "Provider",
    "Target",
    "Mailbox",
    "MessageSummary",
    "MessageDetail",
    "MessageSource",
    "GmailAccount",
    "OAuthStart",
    "GmailCreds",
    "Retention",
    "SweepResult",
    "DomainCacheProvider",
    "DomainCache",
    "DomainCacheRun",
    "HealthAPI",
    "ProvidersAPI",
    "MailboxesAPI",
    "MessagesAPI",
    "GmailAPI",
    "AdminAPI",
]
