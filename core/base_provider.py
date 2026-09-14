"""
Abstract base class for temporary email providers.

To add a new provider:
  1. Subclass ``MailProvider``
  2. Implement every abstract method
  3. Register your provider in ``providers/__init__.py``

Example::

    from mailtmapi.core.base_provider import MailProvider

    class MyProvider(MailProvider):
        @property
        def provider_name(self) -> str:
            return "myprovider"

        async def get_domains(self) -> list[Domain]:
            ...
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..schemas.account import Account, Token
from ..schemas.domains import Domain
from ..schemas.message import Messages, OneMessage, MessageSource


class MailProvider(ABC):
    """
    Common interface for any temporary email backend.

    ``MailClient`` depends only on this interface, making providers
    hot-swappable without changing any consumer code.
    """

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Short, human-readable slug (e.g. ``'mail.tm'``, ``'guerrillamail'``)."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    @abstractmethod
    async def close(self) -> None:
        """Release all resources (HTTP sessions, background tasks, etc.)."""

    async def __aenter__(self) -> "MailProvider":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_domains(self) -> list[Domain]:
        """Return a list of available domains for account creation."""

    async def get_first_domain(self) -> str:
        """Convenience: return the hostname of the first active domain."""
        domains = await self.get_domains()
        if not domains:
            from ..utils.exceptions import MailAPIError
            raise MailAPIError("Provider returned zero available domains")
        return domains[0].domain

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_account_token(self, address: str, password: str) -> Token:
        """Authenticate and return a bearer token for the given account."""

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------

    @abstractmethod
    async def create_account(self, address: str, password: str) -> Account:
        """Register a new account and return it (includes the token)."""

    @abstractmethod
    async def get_account_by_id(self, account_id: str, token: str) -> Account:
        """Fetch account details by its provider-assigned ID."""

    @abstractmethod
    async def delete_account(self, account_id: str, token: str) -> bool:
        """Permanently delete an account. Returns True on success."""

    @abstractmethod
    async def get_me(self, token: str) -> Account:
        """Return the account that owns the given token."""

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_messages(self, token: str, page: int = 1) -> Messages:
        """Return a paginated list of messages."""

    @abstractmethod
    async def get_message_by_id(self, message_id: str, token: str) -> OneMessage:
        """Fetch full message details including body and attachments."""

    @abstractmethod
    async def delete_message(self, message_id: str, token: str) -> bool:
        """Delete a single message. Returns True on success."""

    @abstractmethod
    async def mark_message_read(self, message_id: str, token: str) -> bool:
        """Mark a message as read. Returns True when confirmed."""

    @abstractmethod
    async def get_message_source(self, message_id: str, token: str) -> MessageSource:
        """Fetch the raw MIME source of a message."""
