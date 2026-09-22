"""In-package alias for the canonical standalone client.

Реализация живёт в одном месте — :mod:`mailtmapi.standalone_client`
(самодостаточный однофайловый клиент). Этот модуль просто пробрасывает её,
сохраняя совместимость с ``from mailtmapi.client import MailTMAPI``
(используется дашбордом, тестами и ``mailtmapi.sdk``).
"""

from __future__ import annotations

from .standalone_client import (
    AdminAPI,
    ApiError,
    ClientError,
    ConfigAPI,
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
    __version__,
    check_update,
    self_update,
)

# Тот же публичный контракт, что и у канонического standalone-клиента,
# плюс ресурсные API-секции (AdminAPI и др.) — для обратной совместимости с
# `from mailtmapi.sdk import ...` / старыми плоскими методами.
# Импорты выше намеренно перечислены явно и продублированы в __all__ как строки,
# чтобы Ruff не удалял их как «unused».
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
    "check_update",
    "self_update",
    "__version__",
    "AdminAPI",
    "ConfigAPI",
    "GmailAPI",
    "HealthAPI",
    "MailboxesAPI",
    "MessagesAPI",
    "ProvidersAPI",
]
