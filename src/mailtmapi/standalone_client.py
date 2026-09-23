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
from collections.abc import Callable
from typing import Any
from urllib.parse import quote

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict

__version__ = "0.2.0"

# Откуда клиент берёт себя для автообновления (переопределяется env-переменной).
CLIENT_SOURCE = os.environ.get(
    "MAILTMAPI_CLIENT_SOURCE",
    "https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py",
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


class ProviderOut(_Base):
    slug: str
    kind: str


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
    """Базовая ошибка клиента."""


class ApiError(ClientError):
    """Ошибка HTTP-ответа сервиса: не-2xx статус с detail из тела ответа."""

    def __init__(self, status_code: int | None, detail: str = "") -> None:
        self.status_code = status_code
        self.detail = detail or (f"HTTP {status_code}" if status_code else "request failed")
        super().__init__(self.detail)


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
    os.replace(tmp, path)


def self_update(source_url: str | None = None, *, after: Callable[[], None] | None = None) -> bool:
    """Скачать новую client.py из git и заменить текущий файл на диске.

    Возвращает True, если файл перезаписан. Новую версию подхватит только
    следующий запуск; для pip-установки можно дополнительно выполнить
    `pip install --upgrade "mailtmapi-client @ git+...#subdirectory=client"`.
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
        """Список ящиков. active=None — без фильтра (включая удалённые).

        q — подстрока адреса („%" и „_" считаются литералами), limit/offset —
        постраничная выборка (максимальный limit — 500).
        """
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

    async def get(self, mailbox_id: int) -> Mailbox:
        return Mailbox.model_validate(
            await self._t.request("GET", f"/v1/mailboxes/{mailbox_id}")
        )

    async def by_address(self, email: str) -> Mailbox:
        """Найти ящик по полному адресу."""
        return Mailbox.model_validate(
            await self._t.request("GET", f"/v1/mailboxes/by-address/{quote(email, safe='')}")
        )

    async def delete(self, mailbox_id: int) -> None:
        """Удалить ящик (и на стороне провайдера, и локально)."""
        await self._t.request("DELETE", f"/v1/mailboxes/{mailbox_id}")


class MessagesAPI:
    """Письма ящика: список, чтение, отметки, удаление, ожидание новой почты."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self, mailbox_id: int, page: int = 1) -> list[MessageSummary]:
        """Список писем (страница). Запрос к провайдеру может быть медленным."""
        return [
            MessageSummary.model_validate(m)
            for m in await self._t.request(
                "GET", f"/v1/mailboxes/{mailbox_id}/messages", params={"page": page}
            )
        ]

    async def get(self, mailbox_id: int, message_id: str) -> MessageDetail:
        """Полное письмо с текстом и HTML."""
        return MessageDetail.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mailbox_id}/messages/{quote(message_id, safe='')}"
            )
        )

    async def mark_read(self, mailbox_id: int, message_id: str) -> MessageSummary:
        return MessageSummary.model_validate(
            await self._t.request(
                "POST", f"/v1/mailboxes/{mailbox_id}/messages/{quote(message_id, safe='')}/read"
            )
        )

    async def delete(self, mailbox_id: int, message_id: str) -> None:
        await self._t.request(
            "DELETE", f"/v1/mailboxes/{mailbox_id}/messages/{quote(message_id, safe='')}"
        )

    async def source(self, mailbox_id: int, message_id: str) -> MessageSource:
        """Сырые исходники письма."""
        return MessageSource.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mailbox_id}/messages/{quote(message_id, safe='')}/source"
            )
        )

    async def wait_for(
        self,
        mailbox_id: int,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
        mark_seen: bool = False,
    ) -> MessageSummary:
        """Поллить список, пока не появится подходящее письмо (по умолчанию — любое).

        При mark_seen=True найденное письмо сразу помечается прочитанным.
        По истечении timeout — TimeoutError.
        """
        deadline = time.monotonic() + timeout
        while True:
            for m in await self.list(mailbox_id):
                if predicate is None or predicate(m):
                    if mark_seen:
                        await self.mark_read(mailbox_id, m.message_api_id)
                    return m
            if time.monotonic() >= deadline:
                raise TimeoutError(f"no message arrived within {timeout}s")
            await asyncio.sleep(interval)

    async def wait_for_confirmation_email(
        self,
        mailbox_id: int,
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
            for msg in await self.list(mailbox_id):
                message_id = msg.message_api_id
                if message_id in examined:
                    continue
                if sender_domain and not _is_from_domain(msg.from_address, sender_domain):
                    examined.add(message_id)
                    continue

                try:
                    detail = await self.get(mailbox_id, message_id)
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


class AdminAPI:
    """Админка: статистика, retention (TTL-очистка), кэш доменов, Gmail-креды."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

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

    async def retention_run(self) -> SweepResult:
        """Прогнать очистку сейчас: удалить просроченные ящики и письма."""
        return SweepResult.model_validate(
            await self._t.request("POST", "/v1/admin/retention/run")
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


# --------------------------------------------------------------------------- #
# Публичный клиент
# --------------------------------------------------------------------------- #
class MailTMAPI:
    """Асинхронный клиент mailtmapi. Используй как `async with` или закрывай вручную.

        api = MailTMAPI("http://127.0.0.1:8477", api_key="sk-…")
        await api.mailboxes.create(provider="mail.tm")
        await api.close()

    Секции: .health, .config, .providers, .mailboxes, .messages, .gmail, .admin
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

    def set_api_key(self, api_key: str) -> None:
        """Обновить API-ключ на лету."""
        self._transport.set_api_key(api_key)

    async def check_client_version(self) -> str:
        """Версия сервера из /v1/config. Предупреждает при несовпадении версий.

        Если сервер новее установленного клиента — залогирует совет
        `mailtmapi-client update`.
        """
        cfg = await self.config.get()
        remote = str(cfg.get("client_version") or "")
        if remote and remote != __version__:
            logger.warning(
                "client {} != server {} — обнови клиент: `mailtmapi-client update`",
                __version__,
                remote,
            )
        return remote

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

    async def mailbox(self, mailbox_id: int) -> Mailbox:
        return await self.mailboxes.get(mailbox_id)

    async def mailbox_by_address(self, email: str) -> Mailbox:
        return await self.mailboxes.by_address(email)

    async def delete_mailbox(self, mailbox_id: int) -> None:
        await self.mailboxes.delete(mailbox_id)

    async def list_messages(self, mailbox_id: int, page: int = 1) -> list[MessageSummary]:
        return await self.messages.list(mailbox_id, page=page)

    async def get_message(self, mailbox_id: int, message_id: str) -> MessageDetail:
        return await self.messages.get(mailbox_id, message_id)

    async def mark_read(self, mailbox_id: int, message_id: str) -> MessageSummary:
        return await self.messages.mark_read(mailbox_id, message_id)

    async def delete_message(self, mailbox_id: int, message_id: str) -> None:
        await self.messages.delete(mailbox_id, message_id)

    async def get_source(self, mailbox_id: int, message_id: str) -> MessageSource:
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
        mailbox_id: int,
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
