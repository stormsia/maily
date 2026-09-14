"""
MailClient — multi-provider high-level facade.

Supports any number of ``MailProvider`` instances simultaneously.
Provider selection when creating an account:

  - by explicit ``provider`` name (e.g. ``"mail.tm"`` or ``"tempmail.plus"``)
  - by target ``domain`` (e.g. ``"mailto.plus"`` → auto-routes to the
    provider that owns that domain)
  - nothing → a random provider + domain is chosen automatically

Typical usage::

    async with MailClient() as client:
        # any provider, any domain
        acc = await client.create_account()

        # specific domain zone
        acc = await client.create_account(domain="mailto.plus")

        # specific provider
        acc = await client.create_account(provider="mail.tm")

        # get all available domains across every provider
        domains = await client.get_all_domains()
"""
from __future__ import annotations

import asyncio
import logging
import random
import re
from typing import Any

from ..core.base_provider import MailProvider
from ..db.manager import db_manager
from ..db.models import ALL_MODELS, AccountRecord, MessageRecord
from ..providers.mailtm import MailTMProvider
from ..providers.tempmail_plus import TempMailPlusProvider
from ..schemas.domains import Domain
from ..schemas.message import OneMessage
from ..utils.exceptions import MailAPIError, MailValidationError
from ..utils.misc import random_password, random_string

logger = logging.getLogger(__name__)

_URL_RE = re.compile(r"https?://[^\s'\"<>\]]+")


def _default_providers(proxy: str | None) -> list[MailProvider]:
    """Return the default provider stack used when none are supplied."""
    return [
        MailTMProvider(proxy=proxy),
        TempMailPlusProvider(proxy=proxy),
    ]


class MailClient:
    """
    Multi-provider temporary email client with local SQLite persistence.

    Providers are queried in registration order.  Domain ownership is
    discovered lazily and cached per-provider.

    Args:
        providers: One or more ``MailProvider`` instances.  When omitted,
                   both ``MailTMProvider`` and ``TempMailPlusProvider``
                   are registered automatically.
        db_path:   Path to the SQLite database (WAL mode, 64 MB cache).
                   Pass ``:memory:`` for an ephemeral in-process database.
        proxy:     HTTP proxy forwarded to all auto-created providers.
    """

    def __init__(
        self,
        *providers: MailProvider,
        db_path: str = "mailtm.db",
        proxy: str | None = None,
    ) -> None:
        # Accept a single positional provider for the common single-provider case
        # while keeping the old MailClient(provider=...) call shape working via
        # keyword fallback in the keyword-only section below.
        self._providers: list[MailProvider] = list(providers) or _default_providers(proxy)

        # name → provider fast-lookup
        self._by_name: dict[str, MailProvider] = {
            p.provider_name: p for p in self._providers
        }

        # domain → provider cache  (populated lazily by _resolve_provider)
        self._domain_map: dict[str, MailProvider] = {}
        self._domain_map_lock = asyncio.Lock()

        # Init DB
        db_manager.initialize(db_path)
        db_manager.create_tables(ALL_MODELS)
        db_manager.optimize()

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "MailClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close all provider HTTP sessions and the database connection."""
        await asyncio.gather(*(p.close() for p in self._providers), return_exceptions=True)
        db_manager.close()

    # ------------------------------------------------------------------
    # Provider registry
    # ------------------------------------------------------------------

    def register_provider(self, provider: MailProvider) -> None:
        """
        Register an additional provider at runtime.

        The new provider is appended to the end of the list (lowest priority).
        The domain cache is cleared so the next call to
        :meth:`get_all_domains` re-discovers all domains.
        """
        self._providers.append(provider)
        self._by_name[provider.provider_name] = provider
        self._domain_map.clear()
        logger.info("Provider %r registered", provider.provider_name)

    @property
    def providers(self) -> list[MailProvider]:
        """Registered providers in priority order."""
        return list(self._providers)

    # ------------------------------------------------------------------
    # Domain aggregation
    # ------------------------------------------------------------------

    async def get_all_domains(
        self,
        *,
        provider: str | None = None,
    ) -> list[dict[str, str]]:
        """
        Return all available domains across every registered provider.

        Each entry is a dict::

            {"domain": "mail.tm", "provider": "mail.tm", "id": "..."}

        Args:
            provider: When given, restrict to that provider only.

        Returns:
            Flat list of domain dicts, sorted alphabetically.
        """
        targets = (
            [self._get_provider(provider)]
            if provider
            else self._providers
        )

        results: list[dict[str, str]] = []
        domain_tasks = await asyncio.gather(
            *(p.get_domains() for p in targets),
            return_exceptions=True,
        )

        for prov, outcome in zip(targets, domain_tasks):
            if isinstance(outcome, Exception):
                logger.warning(
                    "get_all_domains: provider %r failed: %s", prov.provider_name, outcome
                )
                continue
            for d in outcome:
                results.append(
                    {
                        "domain": d.domain,
                        "provider": prov.provider_name,
                        "id": d.id,
                        "isActive": str(d.isActive),
                    }
                )
                # Update the internal domain→provider map while we're at it
                self._domain_map[d.domain.lower()] = prov

        results.sort(key=lambda x: x["domain"])
        return results

    # ------------------------------------------------------------------
    # Provider resolution helpers
    # ------------------------------------------------------------------

    def _get_provider(self, name: str) -> MailProvider:
        """Return the registered provider with the given name or raise."""
        if name not in self._by_name:
            available = ", ".join(self._by_name)
            raise MailValidationError(
                f"Unknown provider {name!r}. Available: {available}"
            )
        return self._by_name[name]

    async def _resolve_provider(
        self,
        provider_name: str | None,
        domain: str | None,
    ) -> tuple[MailProvider, str]:
        """
        Resolve (provider, domain_hostname) from user intent.

        Priority:
          1. provider_name + domain both given  → use that provider + domain
          2. only domain given                   → look up which provider owns it
          3. only provider_name given            → pick first domain of that provider
          4. nothing given                       → random provider + random domain
        """
        if provider_name and domain:
            prov = self._get_provider(provider_name)
            return prov, domain

        if domain:
            domain_lower = domain.lower()
            # Check cache first
            async with self._domain_map_lock:
                if domain_lower in self._domain_map:
                    return self._domain_map[domain_lower], domain_lower

            # Cache miss → refresh all domains and try again
            await self.get_all_domains()
            async with self._domain_map_lock:
                if domain_lower not in self._domain_map:
                    raise MailValidationError(
                        f"Domain {domain!r} is not available on any registered provider. "
                        f"Call get_all_domains() to see what is available."
                    )
                return self._domain_map[domain_lower], domain_lower

        if provider_name:
            prov = self._get_provider(provider_name)
            dom = await prov.get_first_domain()
            return prov, dom

        # Fully automatic — pick a random provider and a random domain from it
        prov = random.choice(self._providers)
        try:
            domains = await prov.get_domains()
            dom = random.choice(domains).domain
        except Exception as exc:
            logger.warning(
                "_resolve_provider: provider %r failed (%s), falling back to first available",
                prov.provider_name,
                exc,
            )
            for fallback in self._providers:
                if fallback is prov:
                    continue
                try:
                    dom = await fallback.get_first_domain()
                    prov = fallback
                    break
                except Exception:
                    continue
            else:
                raise MailAPIError("All providers failed to return available domains")

        return prov, dom

    # ------------------------------------------------------------------
    # Account management
    # ------------------------------------------------------------------

    async def create_account(
        self,
        address: str | None = None,
        password: str | None = None,
        *,
        provider: str | None = None,
        domain: str | None = None,
    ) -> AccountRecord:
        """
        Create a new temporary email account.

        Selection rules (mutually exclusive kwargs, in priority order):

        1. ``address`` given                  → used as-is; ``provider`` must match
        2. ``provider`` + ``domain`` both given→ create address on that specific combo
        3. ``domain`` only                    → auto-route to the provider that owns it
        4. ``provider`` only                  → pick first available domain of that provider
        5. nothing                            → random provider + random domain

        Args:
            address:  Full email address to register.  Auto-generated if omitted.
            password: Account password.  Auto-generated with ``random_password`` if omitted.
            provider: Provider slug (e.g. ``"mail.tm"`` or ``"tempmail.plus"``).
            domain:   Target domain hostname (e.g. ``"mailto.plus"``).

        Returns:
            The persisted :class:`~mailtmapi.db.models.AccountRecord`.
        """
        if password is None:
            password = random_password(16)

        if address:
            # Address given → resolve provider from the address domain part
            addr_domain = address.split("@", 1)[-1].lower() if "@" in address else ""
            if provider:
                prov = self._get_provider(provider)
            elif addr_domain:
                prov, _ = await self._resolve_provider(None, addr_domain)
            else:
                raise MailValidationError("Cannot determine provider for address without domain")
        else:
            prov, resolved_domain = await self._resolve_provider(provider, domain)
            address = f"{random_string(10)}@{resolved_domain}"

        account = await prov.create_account(address, password)

        record, created = AccountRecord.get_or_create(
            api_id=account.id,
            defaults=dict(
                provider=prov.provider_name,
                address=account.address,
                password=password,
                token=account.token.token,
                quota=account.quota,
                used=account.used,
                is_active=not account.isDisabled,
                is_deleted=account.isDeleted,
            ),
        )
        if not created:
            record.token = account.token.token
            record.is_active = not account.isDisabled
            import datetime
            record.updated_at = datetime.datetime.utcnow()
            record.save()

        logger.info(
            "Account %s [%s] %s",
            record.address,
            prov.provider_name,
            "created" if created else "refreshed",
        )
        return record

    async def delete_account(self, account_id: int) -> bool:
        """Delete account from provider API and mark inactive in DB."""
        record: AccountRecord = AccountRecord.get_by_id(account_id)
        prov = self._get_provider(record.provider)
        success = await prov.delete_account(record.api_id, record.token)
        if success:
            record.is_active = False
            record.is_deleted = True
            import datetime
            record.updated_at = datetime.datetime.utcnow()
            record.save()
            logger.info("Account %s deleted", record.address)
        return success

    def get_all_accounts(
        self,
        *,
        active_only: bool = True,
        provider: str | None = None,
    ) -> list[AccountRecord]:
        """
        Return accounts from the local DB.

        Args:
            active_only: Filter out deleted/disabled accounts (default True).
            provider:    Restrict to a specific provider slug (optional).
        """
        query = AccountRecord.select()
        if provider:
            query = query.where(AccountRecord.provider == provider)
        if active_only:
            query = query.where(AccountRecord.is_active == True)  # noqa: E712
        return list(query.order_by(AccountRecord.created_at.desc()))

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    def _provider_for_account(self, record: AccountRecord) -> MailProvider:
        """Return the provider that owns *record*."""
        if record.provider not in self._by_name:
            raise MailAPIError(
                f"Account {record.address!r} belongs to provider {record.provider!r} "
                f"which is not registered in this client."
            )
        return self._by_name[record.provider]
    async def get_account_by_email(
        self,
        email: str,
    ) -> AccountRecord | None:
        """Fetch messages from the correct provider and sync to local DB."""
        record: AccountRecord = AccountRecord.get_or_none(AccountRecord.address == email)
        return record


    
    async def get_messages(
        self,
        account_id: int,
        *,
        page: int = 1,
    ) -> list[MessageRecord]:
        """Fetch messages from the correct provider and sync to local DB."""
        record: AccountRecord = AccountRecord.get_by_id(account_id)
        prov = self._provider_for_account(record)
        messages = await prov.get_messages(record.token, page=page)

        import datetime
        now = datetime.datetime.utcnow()
        synced: list[MessageRecord] = []
        for msg in messages.hydra_member:
            msg_record, created = MessageRecord.get_or_create(
                message_api_id=msg.id,
                defaults=dict(
                    account=record,
                    provider=prov.provider_name,
                    subject=msg.subject,
                    from_address=msg.from_.address,
                    from_name=msg.from_.name,
                    seen=msg.seen,
                    is_deleted=msg.isDeleted,
                    has_attachments=msg.hasAttachments,
                    size=msg.size,
                    received_at=msg.createdAt or now,
                ),
            )
            
            # Update mutable fields if record already existed
            if not created:
                changed = (
                    msg_record.seen != msg.seen
                    or msg_record.is_deleted != msg.isDeleted
                    or msg_record.has_attachments != msg.hasAttachments
                    or msg_record.size != msg.size
                )
                if changed:
                    MessageRecord.update(
                        seen=msg.seen,
                        is_deleted=msg.isDeleted,
                        has_attachments=msg.hasAttachments,
                        size=msg.size,
                    ).where(MessageRecord.message_api_id == msg.id).execute()
                    
                    msg_record.seen = msg.seen
                    msg_record.is_deleted = msg.isDeleted

            synced.append(msg_record)

        return synced

    async def get_message_detail(
        self, account_id: int, message_api_id: str
    ) -> OneMessage:
        """Fetch full message detail (body + attachments) from the provider."""
        record: AccountRecord = AccountRecord.get_by_id(account_id)
        prov = self._provider_for_account(record)
        return await prov.get_message_by_id(message_api_id, record.token)

    async def cache_message_body(
        self, account_id: int, message_api_id: str
    ) -> MessageRecord:
        """Fetch full message detail and persist the body to DB."""
        detail = await self.get_message_detail(account_id, message_api_id)
        
        msg_record = MessageRecord.get(
            MessageRecord.message_api_id == message_api_id
        )
        msg_record.body_text =detail.text or " ".join(detail.html)
        msg_record.body_html = "\n".join(detail.html) if detail.html else None
        msg_record.save()
        return msg_record

    async def mark_message_as_read(
        self, message_api_id: str, account_id: int
    ) -> bool:
        """Mark a message as read on the provider and in the local DB."""
        record: AccountRecord = AccountRecord.get_by_id(account_id)
        prov = self._provider_for_account(record)
        success = await prov.mark_message_read(message_api_id, record.token)
        if success:
            (
                MessageRecord.update(seen=True)
                .where(MessageRecord.message_api_id == message_api_id)
                .execute()
            )
        return success

    def get_account_messages(self, account_id: int) -> list[MessageRecord]:
        """Return all cached messages for *account_id*, newest first."""
        return list(
            MessageRecord.select()
            .where(MessageRecord.account == account_id)
            .order_by(MessageRecord.received_at.desc())
        )

    def get_unread_count(self, account_id: int) -> int:
        """Return number of unseen messages cached locally."""
        return (
            MessageRecord.select()
            .where(
                MessageRecord.account == account_id,
                MessageRecord.seen == False,  # noqa: E712
            )
            .count()
        )

    # ------------------------------------------------------------------
    # Polling helpers
    # ------------------------------------------------------------------

    async def wait_for_messages(
        self,
        account_id: int,
        *,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> list[MessageRecord]:
        """
        Poll until at least one new message arrives or *timeout* expires.

        Returns new messages (empty list on timeout).
        """
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout
        known_ids: set[str] = {
            m.message_api_id for m in self.get_account_messages(account_id)
        }

        while loop.time() < deadline:
            current = await self.get_messages(account_id)
            new = [m for m in current if m.message_api_id not in known_ids]
            if new:
                return new
            remaining = deadline - loop.time()
            await asyncio.sleep(min(check_interval, max(remaining, 0)))

        return []

    async def wait_for_confirmation_email(
        self,
        account_id: int,
        *,
        sender_domain: str | None = None,
        url_contain: list=[],
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> dict[str, str | None] | None:
        """
        `sender_domain`="gmail.com" - optional, if not set, will not be used
        `url_contain` = ["confirm", "verify", "activate", "token"] - optional, should set `url_contains` or `digit_code_mask`
        `digit_code_mask`="regexp" - optional, should set `url_contains` or `digit_code_mask`
        
        Ожидает письмо подтверждения.

        Возвращает словарь с ключами:
        message_id, from_address, subject,
        confirmation_link, confirmation_code.

        Возвращает None по истечении timeout.
        """

        if timeout < 0:
            raise ValueError("timeout must be >= 0")

        if check_interval <= 0:
            raise ValueError("check_interval must be > 0")

        keywords = [
            keyword.casefold()
            for keyword in (
                url_contain
                
            )
            if keyword
        ]

        try:
            code_pattern = (
                re.compile(digit_code_mask, re.IGNORECASE)
                if digit_code_mask
                else None
            )
        except re.error as exc:
            raise ValueError(
                f"Invalid regular expression digit_code_mask: "
                f"{digit_code_mask!r}"
            ) from exc

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        initial_messages = self.get_account_messages(account_id)
        seen_ids: set[str] = {
            message.message_api_id
            for message in initial_messages
        }

        def is_from_domain(address: str, domain: str) -> bool:
            match = re.search(r"<([^>]+)>", address)
            email = match.group(1) if match else address

            email_domain = email.rsplit("@", 1)[-1].strip().casefold()
            return email_domain == domain.casefold().lstrip("@")

        while loop.time() < deadline:
            messages = await self.get_messages(account_id)

            for msg in messages:
                message_id = msg.message_api_id

                if message_id in seen_ids:
                    continue

                if sender_domain and not is_from_domain(
                    msg.from_address,
                    sender_domain,
                ):
                    continue

                try:
                    detail = await self.get_message_detail(
                        account_id,
                        message_id,
                    )
                except Exception:
                    logger.exception(
                        "Failed to load message details for %s",
                        message_id,
                    )
                    # Не добавляем message_id в seen_ids:
                    # письмо можно будет повторить на следующей итерации.
                    continue

                seen_ids.add(message_id)

                text = detail.text or ""
                html = " ".join(detail.html or [])
                body = f"{text}\n{html}"

                urls = _URL_RE.findall(body)

                confirmation_link = next(
                    (
                        url
                        for url in urls
                        if not keywords
                        or any(
                            keyword in url.casefold()
                            for keyword in keywords
                        )
                    ),
                    None,
                )

                confirmation_code = None

                if code_pattern:
                    match = code_pattern.search(body)

                    if match:
                        confirmation_code = (
                            match.group(1)
                            if match.lastindex
                            else match.group(0)
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

