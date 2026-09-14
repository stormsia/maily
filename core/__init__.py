"""Core abstractions: MailProvider ABC, MailClient facade, AsyncHTTPSession."""
from .base_provider import MailProvider
from .client import MailClient
from .http import AsyncHTTPSession

__all__ = ["MailProvider", "MailClient", "AsyncHTTPSession"]
