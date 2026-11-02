"""Deprecated alias module.

The flat SDK client and the section-based client were merged into
``maily.client``. Importing names from ``maily.sdk`` still works via
the re-exports below, but emits a ``DeprecationWarning`` — prefer
``from maily.client import Maily``.
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
    Maily,
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
    "maily.sdk is deprecated; use maily.client instead",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "Maily",
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
