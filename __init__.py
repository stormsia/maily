"""
mailtmapi — async temporary email library with multi-provider support.

Quick start::

    from mailtmapi import MailClient

    async with MailClient() as client:
        account = await client.create_account()
        msg = await client.wait_for_confirmation_email(
            account.id, sender_domain="example.com", timeout=60
        )

Public API
----------
MailClient          — high-level facade (provider + DB)
MailProvider        — abstract base for custom providers
MailTMProvider      — mail.tm implementation


DatabaseManager     — peewee/SQLite manager (WAL mode)
db_manager          — module-level singleton

Schemas: Account, Token, Domain, Message, OneMessage, MessageSource
Exceptions: MailAPIError, MailAuthError, MailNotFoundError,
            MailRateLimitError, MailServerError, MailTimeoutError,
            MailConflictError, MailValidationError
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# High-level API
# ---------------------------------------------------------------------------
from .core.client import MailClient
from .core.base_provider import MailProvider

# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
from .providers.gmail import GmailProvider
from .providers.mailtm import MailTMProvider
from .providers.tempmail_plus import TempMailPlusProvider

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------
from .db.manager import DatabaseManager, db_manager
from .db.models import AccountRecord, MessageRecord, DomainRecord, ALL_MODELS

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
from .schemas.account import Account, Token
from .schemas.domains import Domain, Domains
from .schemas.message import Message, Messages, OneMessage, MessageSource, Attachment

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
from .utils.exceptions import (
    MailAPIError,
    MailAuthError,
    MailNotFoundError,
    MailRateLimitError,
    MailServerError,
    MailTimeoutError,
    MailConflictError,
    MailValidationError,
    MailTMInvalidResponse,  # back-compat alias
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
from .utils.misc import random_string, random_password

__all__ = [
    # High-level
    "MailClient",
    "MailProvider",
    # Providers
    "GmailProvider",
    "MailTMProvider",
    "TempMailPlusProvider",
    # DB
    "DatabaseManager",
    "db_manager",
    "AccountRecord",
    "MessageRecord",
    "DomainRecord",
    "ALL_MODELS",
    # Schemas
    "Account",
    "Token",
    "Domain",
    "Domains",
    "Message",
    "Messages",
    "OneMessage",
    "MessageSource",
    "Attachment",
    # Exceptions
    "MailAPIError",
    "MailAuthError",
    "MailNotFoundError",
    "MailRateLimitError",
    "MailServerError",
    "MailTimeoutError",
    "MailConflictError",
    "MailValidationError",
    "MailTMInvalidResponse",
    # Helpers
    "random_string",
    "random_password",
]
