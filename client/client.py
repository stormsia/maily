# -=- THIS FILE IS GENERATED from src/mailtmapi/standalone_client.py -=-
# Do not edit by hand; edit the canonical file and run:
#   python scripts/build_client.py
"""mailtmapi standalone client — CANONICAL single-file implementation.

Это единственный источник истины клиента. Два способа использовать этот код:

    1. Внутри серверного пакета — через тонкий прокси `mailtmapi.client`
       (этот модуль импортируется оттуда).
    2. Снаружи — файл `client/client.py` в корне репозитория, который
       генерируется из этого модуля скриптом `scripts/build_client.py`
       (добавляет only шапку «generated»). Не редактируй `client/client.py`
       руками — правь здесь и перегенерируй; parity проверяет тест
       `tests/test_client_standalone.py::test_standalone_mirror_is_current`.

Файл самодостаточный: не тянет серверную часть (FastAPI, SQLAlchemy,
uvicorn и т.п.), нужны только httpx, loguru и pydantic.

    pip install "mailtmapi-client @ git+https://github.com/stormsia/mailtmapi.git#subdirectory=client"
    # или просто скопируй файл в свой проект:
    #   curl -O https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py

Автообновление: клиент умеет проверять версию на git и обновлять себя из
    client/client.py репозитория:

        mailtmapi-client check           # есть ли новая версия на git?
        mailtmapi-client update          # скачать и установить новую версию

    (или `python client.py check/update`, если файл лежит локально).

    Из кода:

        import client
        from client import MailTMAPI, self_update, check_update

        self_update()          # async-free, обновляет файл клиента на диске
        up = check_update()    # (current, remote) если есть новая версия, иначе None
"""

from __future__ import annotations

import asyncio
import builtins
import os
import re
import sys
import time
from collections.abc import AsyncIterator, Callable
from contextlib import suppress
from typing import Any
from urllib.parse import quote

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

__version__ = "0.3.0"

# Откуда клиент берёт себя для автообновления (переопределяется env-переменной).
CLIENT_SOURCE = os.environ.get(
    "MAILTMAPI_CLIENT_SOURCE",
    "https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py",
)

__all__ = [
    # Клиент и секции
    "MailTMAPI",
    "HealthAPI",
    "ConfigAPI",
    "ProvidersAPI",
    "MailboxesAPI",
    "MessagesAPI",
    "GmailAPI",
    "AdminAPI",
    "KeysAPI",
    # Ошибки
    "ClientError",
    "WaitTimeoutError",
    "ApiError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "UpstreamProviderError",
    # Модели данных
    "HealthOut",
    "Provider",
    "ProviderOut",
    "ProviderCapabilities",
    "Target",
    "TargetOut",
    "Mailbox",
    "MailboxOut",
    "MessageSummary",
    "MessageOut",
    "MessageDetail",
    "MessageDetailOut",
    "MessageSource",
    "SourceOut",
    "GmailAccount",
    "GmailAccountOut",
    "OAuthStart",
    "OAuthStartOut",
    "GmailCreds",
    "GmailCredsOut",
    "Retention",
    "RetentionOut",
    "SweepResult",
    "DomainCacheProvider",
    "DomainCacheProviderOut",
    "DomainCache",
    "DomainCacheOut",
    "DomainCacheRun",
    "ApiKeyOut",
    "ApiKeyCreatedOut",
    "ApiKeyMeOut",
    "KeyScopeOut",
    "KeyRetentionOut",
    "ExtractedConfirmation",
    # Утилиты обновления
    "check_update",
    "self_update",
]


# --------------------------------------------------------------------------- #
# Модели ответов (самодостаточны — не зависят от mailtmapi.schemas)
# --------------------------------------------------------------------------- #
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class HealthOut(_Base):
    status: str = ""


class ProviderCapabilities(_Base):
    can_choose_username: bool = True
    can_choose_domain: bool = True
    can_set_password: bool = False
    supports_delete_mailbox: bool = True
    supports_delete_message: bool = True
    supports_mark_read: bool = False
    supports_source: bool = True
    supports_attachments: bool = True


class ProviderOut(_Base):
    slug: str
    kind: str
    capabilities: ProviderCapabilities | None = None


class TargetOut(_Base):
    id: str
    kind: str
    provider: str
    label: str


class MailboxOut(_Base):
    id: int
    provider: str
    address: str
    parent_id: int | None = None
    is_active: bool
    created_at: Any = None
    parent_status: str | None = None


class MessageOut(_Base):
    id: int
    message_api_id: str
    subject: str = ""
    from_address: str = ""
    from_name: str = ""
    seen: bool = False
    has_attachments: bool = False
    size: int = 0
    received_at: Any = None


class MessageDetailOut(MessageOut):
    text: str = ""
    html: list[str] = []


class SourceOut(_Base):
    id: str
    data: str
    download_url: str = ""


class GmailAccountOut(_Base):
    id: int
    email: str
    status: str
    send_as: list[str] = []


class OAuthStartOut(_Base):
    auth_url: str
    state: str


class GmailCredsOut(_Base):
    configured: bool
    source: str
    client_id: str | None = None
    redirect_uri: str = ""


class RetentionOut(_Base):
    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class SweepResult(_Base):
    mailboxes_deleted: int = 0
    messages_deleted: int = 0


class DomainCacheProviderOut(_Base):
    provider: str
    kind: str = "domain"
    domains_count: int = 0
    updated_at: Any = None
    error: str | None = None


class DomainCacheOut(_Base):
    enabled: bool = True
    interval_seconds: int = 1800
    providers: list[DomainCacheProviderOut] = []


class DomainCacheRun(_Base):
    refreshed: list[str] = []
    failed: list[str] = []


class KeyScopeOut(_Base):
    providers: list[str] = Field(default_factory=list)
    parent_ids: list[int] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class KeyRetentionOut(_Base):
    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class ApiKeyOut(_Base):
    id: int
    name: str
    prefix: str
    scope: KeyScopeOut = Field(default_factory=KeyScopeOut)
    expires_at: Any = None
    created_at: Any = None
    updated_at: Any = None
    key_retention: list[KeyRetentionOut] = Field(default_factory=list)


class ApiKeyCreatedOut(ApiKeyOut):
    secret: str


class ApiKeyMeOut(_Base):
    is_root: bool = False
    name: str = ""
    expires_at: Any = None
    scope: KeyScopeOut | None = None
    key_retention: list[KeyRetentionOut] = Field(default_factory=list)


class ExtractedConfirmation(_Base):
    message_id: str
    from_address: str
    subject: str
    confirmation_link: str | None = None
    confirmation_code: str | None = None


Provider = ProviderOut
Target = TargetOut
Mailbox = MailboxOut
MessageSummary = MessageOut
MessageDetail = MessageDetailOut
MessageSource = SourceOut
GmailAccount = GmailAccountOut
OAuthStart = OAuthStartOut
GmailCreds = GmailCredsOut
Retention = RetentionOut
DomainCacheProvider = DomainCacheProviderOut
DomainCache = DomainCacheOut

_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Ошибки
# --------------------------------------------------------------------------- #
class ClientError(Exception):
    """Базовая ошибка клиента mailtmapi."""


class WaitTimeoutError(ClientError, TimeoutError):
    """Истекло время ожидания входящего письма, ссылки или кода подтверждения."""


class ApiError(ClientError):
    """Ошибка HTTP-ответа сервиса: не-2xx статус с detail из тела ответа."""

    def __init__(self, status_code: int | None, detail: str = "") -> None:
        self.status_code = status_code
        self.detail = detail or (f"HTTP {status_code}" if status_code else "request failed")
        super().__init__(self.detail)


class AuthenticationError(ApiError):
    """HTTP 401: Неверный или отсутствующий API-ключ."""


class ForbiddenError(ApiError):
    """HTTP 403: Доступ запрещён (недостаточно прав у ключа для ресурса/действия)."""


class NotFoundError(ApiError):
    """HTTP 404: Запрошенный ресурс не найден."""


class ValidationError(ApiError):
    """HTTP 400 или 422: Ошибка валидации параметров запроса."""


class RateLimitError(ApiError):
    """HTTP 429: Превышен лимит запросов."""


class UpstreamProviderError(ApiError):
    """HTTP 502/504: Сбой или таймаут внешнего почтового сервиса."""


# --------------------------------------------------------------------------- #
# Автообновление с git
# --------------------------------------------------------------------------- #
def _parse_version(text: str) -> str | None:
    match = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE)
    return match.group(1) if match else None


def _fetch_client(source_url: str | None) -> str:
    url = source_url or CLIENT_SOURCE
    resp = httpx.get(url, timeout=15.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def check_update(source_url: str | None = None) -> tuple[str, str] | None:
    """Вернуть (локальная, удалённая) версии, если на git новая. Иначе None."""
    remote = _parse_version(_fetch_client(source_url))
    if not remote:
        raise ClientError("could not read __version__ from the client source")
    if remote == __version__:
        return None
    return (__version__, remote)


def _atomic_replace(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    if os.name == "nt":
        with open(tmp, encoding="utf-8") as src, open(path, "w", encoding="utf-8", newline="") as dst:
            dst.write(src.read())
        with suppress(OSError):
            os.remove(tmp)
    else:
        os.replace(tmp, path)


def self_update(
    source_url: str | None = None,
    *,
    after: Callable[[], None] | None = None,
) -> bool:
    """Обновить исполняемый файл клиента новой версией из git.

    Возвращает True если файл был перезаписан, False если версия уже актуальна.
    Переопределить источник можно env-переменной MAILTMAPI_CLIENT_SOURCE.
    """
    text = _fetch_client(source_url)
    remote = _parse_version(text)
    if not remote:
        raise ClientError("could not read __version__ from the client source")
    if remote == __version__:
        return False

    import inspect

    path = inspect.getsourcefile(MailTMAPI) or __file__
    _atomic_replace(path, text)
    logger.info("client updated {} -> {} ({})", __version__, remote, path)
    if after is not None:
        after()
    return True


# --------------------------------------------------------------------------- #
# Транспорт
# --------------------------------------------------------------------------- #
class _Transport:
    """Общий HTTP-слой: один AsyncClient, ключ, логгирование, ошибки."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 30.0,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=base_url.rstrip("/"), timeout=timeout
        )
        self._owns_client = client is None
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["X-API-Key"] = api_key

    def set_api_key(self, api_key: str) -> None:
        """Обновить API-ключ на лету (пустая строка — убрать)."""
        if api_key:
            self._headers["X-API-Key"] = api_key
        else:
            self._headers.pop("X-API-Key", None)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        started = time.perf_counter()
        try:
            resp = await self._client.request(
                method, path, params=params, json=json, headers=self._headers
            )
        except httpx.HTTPError as exc:
            logger.opt(exception=False).warning("{} {} failed: {}", method, path, exc)
            raise ApiError(None, f"network error: {exc}") from exc
        elapsed = (time.perf_counter() - started) * 1000
        if resp.status_code >= 400:
            detail = _extract_detail(resp)
            logger.warning(
                "{} {} -> {} ({:.0f}ms): {}", method, path, resp.status_code, elapsed, detail
            )
            if resp.status_code == 401:
                raise AuthenticationError(resp.status_code, detail)
            if resp.status_code == 403:
                raise ForbiddenError(resp.status_code, detail)
            if resp.status_code == 404:
                raise NotFoundError(resp.status_code, detail)
            if resp.status_code in (400, 422):
                raise ValidationError(resp.status_code, detail)
            if resp.status_code == 429:
                raise RateLimitError(resp.status_code, detail)
            if resp.status_code in (502, 504):
                raise UpstreamProviderError(resp.status_code, detail)
            raise ApiError(resp.status_code, detail)
        logger.debug("{} {} -> {} ({:.0f}ms)", method, path, resp.status_code, elapsed)
        if resp.status_code == 204:
            return None
        return resp.json()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> _Transport:
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()


def _extract_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except Exception:
        return resp.text[:300]
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str) and detail:
            return detail
        return str(body)[:300]
    return str(body)[:300]


def _mailbox_id_val(mailbox_id: int | MailboxOut) -> int:
    return mailbox_id.id if hasattr(mailbox_id, "id") else int(mailbox_id)


# --------------------------------------------------------------------------- #
# Ресурсные API
# --------------------------------------------------------------------------- #
class HealthAPI:
    """GET /health — проверка живости сервиса (без API-ключа)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def ping(self) -> HealthOut:
        return HealthOut.model_validate(await self._t.request("GET", "/health"))


class ConfigAPI:
    """GET /v1/config — публичные факты о сервере (без API-ключа)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def get(self) -> dict[str, Any]:
        return await self._t.request("GET", "/v1/config")


class ProvidersAPI:
    """Провайдеры и цели (домены / родительские аккаунты)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self) -> list[Provider]:
        """Все доступные провайдеры."""
        return [Provider.model_validate(p) for p in await self._t.request("GET", "/v1/providers")]

    async def targets(self, provider: str | None = None) -> builtins.list[Target]:
        """Цели создания ящика: домены (domain-провайдеры) или Gmail-аккаунты."""
        params = {"provider": provider} if provider else None
        return [
            Target.model_validate(t)
            for t in await self._t.request("GET", "/v1/targets", params=params)
        ]


class MailboxesAPI:
    """Создание, список, получение и удаление ящиков."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def create(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        """Создать ящик. Для domain-провайдеров — domain, для Gmail — parent_id."""
        payload = {
            k: v
            for k, v in {
                "provider": provider,
                "domain": domain,
                "parent_id": parent_id,
                "address": address,
                "password": password,
            }.items()
            if v is not None
        }
        return Mailbox.model_validate(await self._t.request("POST", "/v1/mailboxes", json=payload))

    async def list(
        self,
        *,
        provider: str | None = None,
        active: bool | None = None,
        q: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Mailbox]:
        """Список ящиков. active=None — без фильтра (включая удалённые)."""
        params: dict[str, Any] = {}
        if provider:
            params["provider"] = provider
        if active is not None:
            params["active"] = str(active).lower()
        if q:
            params["q"] = q
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        return [
            Mailbox.model_validate(m)
            for m in await self._t.request("GET", "/v1/mailboxes", params=params or None)
        ]

    async def get(self, mailbox_id: int | Mailbox) -> Mailbox:
        mid = _mailbox_id_val(mailbox_id)
        return Mailbox.model_validate(
            await self._t.request("GET", f"/v1/mailboxes/{mid}")
        )

    async def by_address(self, email: str) -> Mailbox:
        """Найти ящик по полному адресу."""
        return Mailbox.model_validate(
            await self._t.request("GET", f"/v1/mailboxes/by-address/{quote(email, safe='')}")
        )

    async def delete(self, mailbox_id: int | Mailbox) -> None:
        """Удалить ящик (и на стороне провайдера, и локально)."""
        mid = _mailbox_id_val(mailbox_id)
        await self._t.request("DELETE", f"/v1/mailboxes/{mid}")


class MessagesAPI:
    """Письма ящика: список, чтение, отметки, удаление, ожидание новой почты."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        """Список писем (страница)."""
        mid = _mailbox_id_val(mailbox_id)
        return [
            MessageSummary.model_validate(m)
            for m in await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages", params={"page": page}
            )
        ]

    async def get(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        """Полное письмо с текстом и HTML."""
        mid = _mailbox_id_val(mailbox_id)
        return MessageDetail.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}"
            )
        )

    async def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        mid = _mailbox_id_val(mailbox_id)
        return MessageSummary.model_validate(
            await self._t.request(
                "POST", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}/read"
            )
        )

    async def delete(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        mid = _mailbox_id_val(mailbox_id)
        await self._t.request(
            "DELETE", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}"
        )

    async def source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        """Сырые исходники письма."""
        mid = _mailbox_id_val(mailbox_id)
        return MessageSource.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}/source"
            )
        )

    async def wait_for(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
        mark_seen: bool = False,
    ) -> MessageSummary:
        """Поллить список, пока не появится подходящее письмо (по умолчанию — любое).

        При mark_seen=True найденное письмо сразу помечается прочитанным.
        По истечении timeout бросается WaitTimeoutError (также является TimeoutError).
        """
        mid = _mailbox_id_val(mailbox_id)
        deadline = time.monotonic() + timeout
        while True:
            for m in await self.list(mid):
                if predicate is None or predicate(m):
                    if mark_seen:
                        await self.mark_read(mid, m.message_api_id)
                    return m
            if time.monotonic() >= deadline:
                raise WaitTimeoutError(f"no message arrived within {timeout}s")
            await asyncio.sleep(interval)

    async def wait_for_confirmation_email(
        self,
        mailbox_id: int | Mailbox,
        *,
        sender_domain: str | None = None,
        url_contain: builtins.list[str] | None = None,
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> dict[str, str | None] | None:
        """Ожидает письмо подтверждения и извлекает из него ссылку/код.

        Параметры (все опциональны, но нужен `url_contain` или `digit_code_mask`):
            sender_domain    — фильтр по домену отправителя, e.g. "gmail.com"
            url_contain      — подстроки, которые должны быть в ссылке,
                               e.g. ["confirm", "verify", "activate", "token"]
            digit_code_mask  — regexp для кода подтверждения

        Возвращает dict с ключами: message_id, from_address, subject,
        confirmation_link, confirmation_code. None по истечении timeout.
        """
        mid = _mailbox_id_val(mailbox_id)
        if timeout < 0:
            raise ValueError("timeout must be >= 0")
        if check_interval <= 0:
            raise ValueError("check_interval must be > 0")

        keywords: list[str] = []
        for keyword in url_contain or []:
            if keyword:
                keywords.append(keyword.casefold())
        try:
            code_pattern = (
                re.compile(digit_code_mask, re.IGNORECASE) if digit_code_mask else None
            )
        except re.error as exc:
            raise ValueError(
                f"Invalid regular expression digit_code_mask: {digit_code_mask!r}"
            ) from exc

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        def _is_from_domain(address: str, domain: str) -> bool:
            match = re.search(r"<([^>]+)>", address)
            email = match.group(1) if match else address
            email_domain = email.rsplit("@", 1)[-1].strip().casefold()
            return email_domain == domain.casefold().lstrip("@")

        examined: set[str] = set()

        while loop.time() < deadline:
            for msg in await self.list(mid):
                message_id = msg.message_api_id
                if message_id in examined:
                    continue
                if sender_domain and not _is_from_domain(msg.from_address, sender_domain):
                    examined.add(message_id)
                    continue

                try:
                    detail = await self.get(mid, message_id)
                except Exception:
                    logger.exception("Failed to load message details for %s", message_id)
                    continue

                examined.add(message_id)

                body = "\n".join(filter(None, [detail.text or "", *detail.html]))

                urls = _URL_RE.findall(body)
                confirmation_link = next(
                    (
                        url
                        for url in urls
                        if not keywords or any(kw in url.casefold() for kw in keywords)
                    ),
                    None,
                )

                confirmation_code = None
                if code_pattern:
                    match = code_pattern.search(body)
                    if match:
                        confirmation_code = (
                            match.group(1) if match.lastindex else match.group(0)
                        )

                if confirmation_link is None and confirmation_code is None:
                    continue

                logger.info(
                    "Confirmation email found from %s (subject: %s)",
                    msg.from_address,
                    msg.subject,
                )
                return {
                    "message_id": message_id,
                    "from_address": msg.from_address,
                    "subject": msg.subject,
                    "confirmation_link": confirmation_link,
                    "confirmation_code": confirmation_code,
                }

            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            await asyncio.sleep(min(check_interval, remaining))

        return None

    async def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Ожидает письмо и возвращает цифровой код подтверждения (строку).

        Бросает WaitTimeoutError по истечении timeout.
        """
        res = await self.wait_for_confirmation_email(
            mailbox_id,
            sender_domain=sender_domain,
            digit_code_mask=pattern,
            timeout=timeout,
            check_interval=check_interval,
        )
        if not res or not res.get("confirmation_code"):
            raise WaitTimeoutError(f"no verification code arrived within {timeout}s")
        return str(res["confirmation_code"])

    async def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Ожидает письмо и возвращает URL подтверждения.

        Бросает WaitTimeoutError по истечении timeout.
        """
        res = await self.wait_for_confirmation_email(
            mailbox_id,
            sender_domain=sender_domain,
            url_contain=url_contain or ["http"],
            timeout=timeout,
            check_interval=check_interval,
        )
        if not res or not res.get("confirmation_link"):
            raise WaitTimeoutError(f"no confirmation link arrived within {timeout}s")
        return str(res["confirmation_link"])

    async def iter_messages(
        self,
        mailbox_id: int | Mailbox,
        *,
        poll_interval: float = 3.0,
        timeout: float | None = None,
    ) -> AsyncIterator[MessageSummary]:
        """Асинхронный генератор: непрерывно поллит ящик и возвращает новые письма по мере их поступления."""
        mid = _mailbox_id_val(mailbox_id)
        seen_ids: set[str] = set()
        loop = asyncio.get_running_loop()
        deadline = (loop.time() + timeout) if timeout is not None else None

        for m in await self.list(mid):
            seen_ids.add(m.message_api_id)

        while True:
            if deadline is not None and loop.time() >= deadline:
                break
            for m in await self.list(mid):
                if m.message_api_id not in seen_ids:
                    seen_ids.add(m.message_api_id)
                    yield m
            if deadline is not None and loop.time() + poll_interval >= deadline:
                break
            await asyncio.sleep(poll_interval)


class GmailAPI:
    """OAuth-подключение и управление Gmail-аккаунтами."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def oauth_start(self) -> OAuthStart:
        """URL для OAuth: открой его в браузере и выбери любой Google-аккаунт."""
        return OAuthStart.model_validate(
            await self._t.request("POST", "/v1/gmail/oauth/start")
        )

    async def import_account(
        self,
        *,
        refresh_token: str | None = None,
        token_json: Any = None,
    ) -> GmailAccount:
        """Импорт уже полученного токена (refresh_token или token_json)."""
        payload: dict[str, Any] = {}
        if refresh_token:
            payload["refresh_token"] = refresh_token
        if token_json is not None:
            payload["token_json"] = token_json
        return GmailAccount.model_validate(
            await self._t.request("POST", "/v1/gmail/accounts/import", json=payload)
        )

    async def accounts(self) -> list[GmailAccount]:
        return [
            GmailAccount.model_validate(a)
            for a in await self._t.request("GET", "/v1/gmail/accounts")
        ]

    async def delete_account(self, parent_id: int) -> None:
        await self._t.request("DELETE", f"/v1/gmail/accounts/{parent_id}")

    async def sync(self, parent_id: int) -> GmailAccount:
        """Обновить профиль и send-as алиасы аккаунта."""
        return GmailAccount.model_validate(
            await self._t.request("POST", f"/v1/gmail/accounts/{parent_id}/sync")
        )


class KeysAPI:
    """Управление API-ключами: список, создание, просмотр, ротация, удаление."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self) -> builtins.list[ApiKeyOut]:
        """Root only. Список выпущенных ключей (без секретов)."""
        data = await self._t.request("GET", "/v1/admin/keys")
        return [ApiKeyOut.model_validate(k) for k in data]

    async def create(
        self,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
        retention: builtins.list[dict[str, Any]] | None = None,
    ) -> ApiKeyCreatedOut:
        """Root only. Создать ключ (секрет возвращается только в ответе на создание)."""
        payload: dict[str, Any] = {
            "name": name,
            "expires_at": expires_at,
            "scope": scope or {"providers": [], "parent_ids": [], "actions": []},
            "retention": retention or [],
        }
        return ApiKeyCreatedOut.model_validate(
            await self._t.request("POST", "/v1/admin/keys", json=payload)
        )

    async def get(self, key_id: int) -> ApiKeyOut:
        """Root only. Информация о ключе по ID (без секрета)."""
        return ApiKeyOut.model_validate(await self._t.request("GET", f"/v1/admin/keys/{key_id}"))

    async def me(self) -> ApiKeyMeOut:
        """Информация о текущем активном ключе (из заголовка X-API-Key)."""
        return ApiKeyMeOut.model_validate(await self._t.request("GET", "/v1/admin/keys/me"))

    async def secret(self, key_id: int) -> str:
        """Root only. Раскрыть секрет ключа."""
        data = await self._t.request("GET", f"/v1/admin/keys/{key_id}/secret")
        return str(data.get("secret") or "")

    async def update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
    ) -> ApiKeyOut:
        """Root only. Обновить имя, дату истечения или права ключа."""
        payload = {
            "name": name,
            "expires_at": expires_at,
            "scope": scope or {"providers": [], "parent_ids": [], "actions": []},
        }
        return ApiKeyOut.model_validate(
            await self._t.request("PATCH", f"/v1/admin/keys/{key_id}", json=payload)
        )

    async def retention_set(
        self, key_id: int, retention: builtins.list[dict[str, Any]]
    ) -> builtins.list[KeyRetentionOut]:
        """Root only. Установить индивидуальные правила TTL для ключа."""
        data = await self._t.request("PUT", f"/v1/admin/keys/{key_id}/retention", json=retention)
        return [KeyRetentionOut.model_validate(r) for r in data]

    async def rotate(self, key_id: int) -> ApiKeyCreatedOut:
        """Root only. Ротировать секрет ключа (старый аннулируется, новый возвращается один раз)."""
        return ApiKeyCreatedOut.model_validate(
            await self._t.request("POST", f"/v1/admin/keys/{key_id}/rotate")
        )

    async def delete(self, key_id: int) -> None:
        """Root only. Удалить ключ."""
        await self._t.request("DELETE", f"/v1/admin/keys/{key_id}")


class AdminAPI:
    """Админка: статистика, retention (TTL-очистка), кэш доменов, Gmail-креды, ключи."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport
        self.keys_api = KeysAPI(transport)

    async def stats(self) -> dict:
        """Статистика: ящики, письма, провайдеры, тренд за 7 дней."""
        return await self._t.request("GET", "/v1/admin/stats")

    async def retention_list(self) -> list[Retention]:
        return [
            Retention.model_validate(r)
            for r in await self._t.request("GET", "/v1/admin/retention")
        ]

    async def retention_set(
        self,
        provider: str,
        *,
        mailbox_ttl_hours: int | None = None,
        message_ttl_hours: int | None = None,
    ) -> Retention:
        """Включить/обновить TTL-очистку для провайдера (хотя бы один TTL нужен)."""
        payload = {
            k: v
            for k, v in {
                "mailbox_ttl_hours": mailbox_ttl_hours,
                "message_ttl_hours": message_ttl_hours,
            }.items()
            if v is not None
        }
        return Retention.model_validate(
            await self._t.request(
                "PUT", f"/v1/admin/retention/{quote(provider, safe='')}", json=payload
            )
        )

    async def retention_disable(self, provider: str) -> None:
        await self._t.request(
            "DELETE", f"/v1/admin/retention/{quote(provider, safe='')}"
        )

    async def retention_run(self, *, force_maintenance: bool = False) -> SweepResult:
        """Прогнать очистку сейчас: удалить просроченные ящики и письма."""
        return SweepResult.model_validate(
            await self._t.request(
                "POST",
                "/v1/admin/retention/run",
                params={"force_maintenance": "true"} if force_maintenance else None,
            )
        )

    async def domain_cache(self) -> DomainCache:
        """Текущее состояние кэша доменов (включён ли, интервал, провайдеры)."""
        return DomainCache.model_validate(
            await self._t.request("GET", "/v1/admin/domain-cache")
        )

    async def domain_cache_save(
        self,
        *,
        enabled: bool | None = None,
        interval_seconds: int | None = None,
    ) -> DomainCache:
        """Обновить настройки кэша доменов (хотя бы один параметр нужен)."""
        payload = {
            k: v
            for k, v in {
                "enabled": enabled,
                "interval_seconds": interval_seconds,
            }.items()
            if v is not None
        }
        return DomainCache.model_validate(
            await self._t.request("PUT", "/v1/admin/domain-cache", json=payload)
        )

    async def domain_cache_run(self) -> DomainCacheRun:
        """Принудительно обновить кэш доменов сейчас."""
        return DomainCacheRun.model_validate(
            await self._t.request("POST", "/v1/admin/domain-cache/run")
        )

    async def gmail_creds(self) -> GmailCreds:
        return GmailCreds.model_validate(
            await self._t.request("GET", "/v1/admin/gmail/creds")
        )

    async def gmail_creds_save(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
    ) -> GmailCreds:
        payload: dict[str, str] = {"client_id": client_id, "client_secret": client_secret}
        if redirect_uri:
            payload["redirect_uri"] = redirect_uri
        return GmailCreds.model_validate(
            await self._t.request("PUT", "/v1/admin/gmail/creds", json=payload)
        )

    async def gmail_creds_clear(self) -> None:
        await self._t.request("DELETE", "/v1/admin/gmail/creds")

    async def keys(self) -> list[dict[str, Any]]:
        """Root only. Lists keys; the secret is not in the response."""
        return await self._t.request("GET", "/v1/admin/keys")

    async def key_create(
        self,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
        retention: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Root only. Creates a key; the response includes the secret once."""
        return await self._t.request(
            "POST",
            "/v1/admin/keys",
            json={
                "name": name,
                "expires_at": expires_at,
                "scope": scope,
                "retention": retention,
            },
        )

    async def key_get(self, key_id: int) -> dict[str, Any]:
        """Root only. Returns one key without the secret."""
        return await self._t.request("GET", f"/v1/admin/keys/{key_id}")

    async def key_me(self) -> dict[str, Any]:
        """Any authenticated key. Root gets is_root; an issued key gets no secret."""
        return await self._t.request("GET", "/v1/admin/keys/me")

    async def key_secret(self, key_id: int) -> dict[str, Any]:
        """Root only. Reveals the secret."""
        return await self._t.request("GET", f"/v1/admin/keys/{key_id}/secret")

    async def key_update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
    ) -> dict[str, Any]:
        """Root only. Updates name, expiry, and scope; the secret is unchanged."""
        return await self._t.request(
            "PATCH",
            f"/v1/admin/keys/{key_id}",
            json={"name": name, "expires_at": expires_at, "scope": scope},
        )

    async def key_retention_set(
        self, key_id: int, retention: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Root only. Replaces that key's retention rows."""
        return await self._t.request(
            "PUT", f"/v1/admin/keys/{key_id}/retention", json=retention
        )

    async def key_rotate(self, key_id: int) -> dict[str, Any]:
        """Root only. Rotates the secret; the response includes the new secret once."""
        return await self._t.request("POST", f"/v1/admin/keys/{key_id}/rotate")

    async def key_delete(self, key_id: int) -> None:
        """Root only. Deletes the key."""
        await self._t.request("DELETE", f"/v1/admin/keys/{key_id}")


# --------------------------------------------------------------------------- #
# Публичный клиент
# --------------------------------------------------------------------------- #
class MailTMAPI:
    """Асинхронный клиент mailtmapi. Используй как `async with` или закрывай вручную.

        async with MailTMAPI("http://127.0.0.1:8477", api_key="sk-…") as api:
            box = await api.create_temp_mailbox()
            code = await api.wait_for_code(box)
            print("Verification code:", code)

    Секции: .health, .config, .providers, .mailboxes, .messages, .gmail, .admin, .keys
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8477",
        api_key: str = "",
        timeout: float = 30.0,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._transport = _Transport(base_url, api_key, timeout, client=client)
        self.health = HealthAPI(self._transport)
        self.config = ConfigAPI(self._transport)
        self.providers = ProvidersAPI(self._transport)
        self.mailboxes = MailboxesAPI(self._transport)
        self.messages = MessagesAPI(self._transport)
        self.gmail = GmailAPI(self._transport)
        self.admin = AdminAPI(self._transport)
        self.keys = KeysAPI(self._transport)

    def set_api_key(self, api_key: str) -> None:
        """Обновить API-ключ на лету."""
        self._transport.set_api_key(api_key)

    async def check_client_version(self) -> str:
        """Версия сервера из /v1/config. Предупреждает при несовпадении версий."""
        cfg = await self.config.get()
        remote = str(cfg.get("client_version") or "")
        if remote and remote != __version__:
            logger.warning(
                "client {} != server {} — обнови клиент: `mailtmapi-client update`",
                __version__,
                remote,
            )
        return remote

    async def create_temp_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
    ) -> Mailbox:
        """Удобный хелпер: создать временный ящик в 1 вызов.

        Если domain не указан, автоматически берёт первый доступный домен провайдера.
        """
        if not domain and not provider:
            targets = await self.providers.targets()
            domain_targets = [t for t in targets if t.kind == "domain"]
            if domain_targets:
                domain = domain_targets[0].label
                provider = domain_targets[0].provider
        elif not domain and provider:
            targets = await self.providers.targets(provider=provider)
            if targets:
                domain = targets[0].label
        return await self.mailboxes.create(provider=provider, domain=domain)

    async def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Поллить ящик, пока не придёт письмо с цифровым кодом подтверждения."""
        return await self.messages.wait_for_code(
            mailbox_id,
            pattern=pattern,
            sender_domain=sender_domain,
            timeout=timeout,
            check_interval=check_interval,
        )

    async def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Поллить ящик, пока не придёт письмо со ссылкой подтверждения."""
        return await self.messages.wait_for_link(
            mailbox_id,
            url_contain=url_contain,
            sender_domain=sender_domain,
            timeout=timeout,
            check_interval=check_interval,
        )

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> MailTMAPI:
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()

    # --- SDK-совместимые плоские методы (deprecated, используй секции выше) ---

    async def create_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        return await self.mailboxes.create(
            provider=provider,
            domain=domain,
            parent_id=parent_id,
            address=address,
            password=password,
        )

    async def list_mailboxes(
        self, provider: str | None = None, active: bool | None = None
    ) -> list[Mailbox]:
        return await self.mailboxes.list(provider=provider, active=active)

    async def mailbox(self, mailbox_id: int | Mailbox) -> Mailbox:
        return await self.mailboxes.get(mailbox_id)

    async def mailbox_by_address(self, email: str) -> Mailbox:
        return await self.mailboxes.by_address(email)

    async def delete_mailbox(self, mailbox_id: int | Mailbox) -> None:
        await self.mailboxes.delete(mailbox_id)

    async def list_messages(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        return await self.messages.list(mailbox_id, page=page)

    async def get_message(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        return await self.messages.get(mailbox_id, message_id)

    async def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        return await self.messages.mark_read(mailbox_id, message_id)

    async def delete_message(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        await self.messages.delete(mailbox_id, message_id)

    async def get_source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        return await self.messages.source(mailbox_id, message_id)

    async def gmail_oauth_start(self) -> OAuthStart:
        return await self.gmail.oauth_start()

    async def gmail_import_account(
        self, *, refresh_token: str | None = None, token_json: Any = None
    ) -> GmailAccount:
        return await self.gmail.import_account(
            refresh_token=refresh_token, token_json=token_json
        )

    async def list_gmail_accounts(self) -> list[GmailAccount]:
        return await self.gmail.accounts()

    async def delete_gmail_account(self, parent_id: int) -> None:
        await self.gmail.delete_account(parent_id)

    async def sync_gmail_account(self, parent_id: int) -> GmailAccount:
        return await self.gmail.sync(parent_id)

    async def domain_cache_settings(self) -> DomainCache:
        return await self.admin.domain_cache()

    async def save_domain_cache_settings(
        self, *, enabled: bool | None = None, interval_seconds: int | None = None
    ) -> DomainCache:
        return await self.admin.domain_cache_save(
            enabled=enabled, interval_seconds=interval_seconds
        )

    async def refresh_domain_cache(self) -> DomainCacheRun:
        return await self.admin.domain_cache_run()

    async def wait_for_message(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
    ) -> MessageSummary:
        return await self.messages.wait_for(
            mailbox_id, timeout=timeout, interval=interval, predicate=predicate
        )


# --------------------------------------------------------------------------- #
# CLI: python client.py check|update|version
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__.split("\n\n")[1].strip(), file=sys.stderr)
        print(
            "\nusage:\n"
            "  mailtmapi-client version     — показать версию\n"
            "  mailtmapi-client check       — проверить новую версию на git\n"
            "  mailtmapi-client update      — обновить файл клиента из git\n"
            "  (или: python client.py check/update)\n",
            file=sys.stderr,
        )
        return 0
    if args[0] == "version":
        print(__version__)
        return 0
    if args[0] == "check":
        try:
            result = check_update(args[1] if len(args) > 1 else None)
        except Exception as exc:
            print(f"check failed: {exc}", file=sys.stderr)
            return 1
        if result is None:
            print(f"client is up to date ({__version__})")
            return 0
        print(f"update available: {result[0]} -> {result[1]}")
        return 2
    if args[0] == "update":
        try:
            updated = self_update(args[1] if len(args) > 1 else None)
        except Exception as exc:
            print(f"update failed: {exc}", file=sys.stderr)
            return 1
        if not updated:
            print(f"client is up to date ({__version__})")
            return 0
        print("updated. Перезапусти свои скрипты.")
        return 0
    print(f"unknown command: {args[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
