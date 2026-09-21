from __future__ import annotations

import asyncio
import logging
import time
from contextlib import suppress

from mailtmapi.exceptions import MailAPIError, MailAuthError, MailValidationError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import (
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Target,
    TargetKind,
)
from mailtmapi.utils.misc import random_string
from mailtmapi.utils.retry import async_retry

from .oauth import GmailOAuth
from .parse import is_base_or_alias, raw_to_detail, raw_to_source, raw_to_summary, strip_plus
from .store import GmailParent, GmailParentStore

logger = logging.getLogger(__name__)

_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailProvider:
    slug = "gmail"
    kind: TargetKind = "parent"

    def __init__(
        self,
        store: GmailParentStore,
        oauth: GmailOAuth,
        http: HttpClient | None = None,
    ) -> None:
        self._store = store
        self._oauth = oauth
        self._http = http or HttpClient()
        self._owns_http = http is None
        self._parent_rr = 0
        self._alias_rr: dict[int, int] = {}
        self._page_tokens: dict[str, str] = {}
        self._lock = asyncio.Lock()  # ponytail: global lock, per-parent if throughput matters

    async def close(self) -> None:
        if self._owns_http:
            await self._http.close()

    async def _ensure_access(self, parent: GmailParent) -> str:
        async with self._lock:
            if (
                parent.access_token
                and parent.access_expires_at
                and parent.access_expires_at > time.time() + 60
            ):
                return parent.access_token
            try:
                tokens = await self._oauth.refresh(parent.refresh_token)
            except MailAuthError:
                # Refresh token was rejected (revoked, or test-mode lapse).
                # Flag the account expired so the dashboard can prompt to
                # reconnect — active mailboxes keep working against the cache,
                # but no new mailboxes are picked from it.
                parent.status = "expired"
                if parent.id:
                    with suppress(Exception):
                        await self._store.update(parent)
                raise
            parent.access_token = tokens["access_token"]
            parent.access_expires_at = tokens["expires_at"]
            if tokens.get("refresh_token"):
                parent.refresh_token = tokens["refresh_token"]
            if tokens.get("scopes"):
                parent.scopes = tokens["scopes"]
            await self._store.update(parent)
            return parent.access_token  # type: ignore[return-value]

    async def _api_get(self, parent: GmailParent, url: str, params: dict | None = None) -> dict:
        token = await self._ensure_access(parent)
        resp = await self._http.get(
            url, params=params, headers={"Authorization": f"Bearer {token}"}
        )
        return resp.json()

    async def _api_post(
        self, parent: GmailParent, url: str, json_body: dict | None = None
    ) -> dict:
        token = await self._ensure_access(parent)
        kwargs: dict = {"headers": {"Authorization": f"Bearer {token}"}}
        if json_body is not None:
            kwargs["json"] = json_body
        resp = await self._http.post(url, **kwargs)
        return resp.json()

    async def list_targets(self) -> list[Target]:
        return [
            Target(
                id=str(p.id),
                kind="parent",
                provider="gmail",
                label=strip_plus(p.email),
            )
            for p in await self._store.list_active()
        ]

    async def _pick_parent(self, spec: MailboxSpec) -> GmailParent:
        if spec.parent_id is not None:
            return await self._store.get(spec.parent_id)
        active = await self._store.list_active()
        if not active:
            raise MailValidationError("no active gmail parents")
        parent = active[self._parent_rr % len(active)]
        self._parent_rr += 1
        return parent

    async def sync_profile(self, parent: GmailParent) -> GmailParent:
        """Fetch profile + sendAs and persist if the parent is already stored."""
        parent.send_as = []
        await self._bases_for(parent)
        return parent

    async def _bases_for(self, parent: GmailParent) -> list[str]:
        if parent.send_as:
            return parent.send_as
        profile = await self._api_get(parent, f"{_API_BASE}/profile")
        email = strip_plus(profile["emailAddress"])
        parent.email = email
        domain = email.rsplit("@", 1)[-1].lower()
        bases = [email]
        try:
            settings = await self._api_get(parent, f"{_API_BASE}/settings/sendAs")
            for send_as in settings.get("sendAs", []):
                alias_addr = send_as.get("sendAsEmail", "")
                if not alias_addr or "+" in alias_addr.rsplit("@", 1)[0]:
                    continue
                if alias_addr.rsplit("@", 1)[-1].lower() == domain:
                    bases.append(alias_addr)
        except MailAPIError as exc:
            logger.warning("gmail: could not list sendAs aliases (%s); using profile only", exc)
        seen: set[str] = set()
        deduped: list[str] = []
        for b in bases:
            key = b.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(b)
        parent.send_as = deduped
        if parent.id:
            await self._store.update(parent)
        return parent.send_as

    def _next_alias(self, parent: GmailParent, bases: list[str]) -> str:
        if not bases:
            raise MailValidationError("gmail: no base address available")
        i = self._alias_rr.get(parent.id, 0)
        base = bases[i % len(bases)]
        self._alias_rr[parent.id] = i + 1
        local, domain = base.rsplit("@", 1)
        return f"{local}+{random_string(10)}@{domain}"

    @async_retry(max_attempts=3)
    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        parent = await self._pick_parent(spec)
        bases = await self._bases_for(parent)
        if spec.address:
            if not is_base_or_alias(spec.address, bases):
                raise MailValidationError("address is not an alias of the chosen gmail parent")
            alias = spec.address
        else:
            alias = self._next_alias(parent, bases)
        return MailboxInfo(
            provider="gmail",
            address=alias,
            token=alias,
            provider_account_id=alias,
            parent_id=parent.id,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        return True

    async def _resolve_parent(self, mailbox: MailboxInfo) -> GmailParent:
        if mailbox.parent_id is not None:
            return await self._store.get(mailbox.parent_id)
        alias = mailbox.address or mailbox.token
        wanted = strip_plus(alias).lower()
        for parent in await self._store.list_active():
            candidates = [parent.email, *parent.send_as]
            if any(strip_plus(addr).lower() == wanted for addr in candidates if addr):
                return parent
        raise MailValidationError("no parent for mailbox")

    @async_retry(max_attempts=3)
    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        parent = await self._resolve_parent(mailbox)
        alias = mailbox.address or mailbox.token
        params: dict = {"q": f'to:("{alias}") in:anywhere -in:trash', "maxResults": 100}
        if page > 1:
            stored = self._page_tokens.get(alias)
            if not stored:
                return []
            params["pageToken"] = stored
        data = await self._api_get(parent, f"{_API_BASE}/messages", params=params)
        nxt = data.get("nextPageToken") or ""
        if nxt:
            self._page_tokens[alias] = nxt
        else:
            self._page_tokens.pop(alias, None)
        message_list: list[dict] = data.get("messages") or []
        token = await self._ensure_access(parent)

        async def _full(msg_id: str) -> dict:
            resp = await self._http.get(
                f"{_API_BASE}/messages/{msg_id}",
                params={"format": "full"},
                headers={"Authorization": f"Bearer {token}"},
            )
            return resp.json()

        results = await asyncio.gather(
            *[_full(m["id"]) for m in message_list],
            return_exceptions=True,
        )
        out: list[MessageSummary] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Failed to fetch message detail: %s", result)
                continue
            if isinstance(result, dict):
                out.append(raw_to_summary(result))
        return out

    @async_retry(max_attempts=3)
    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        parent = await self._resolve_parent(mailbox)
        data = await self._api_get(
            parent, f"{_API_BASE}/messages/{message_id}", params={"format": "full"}
        )
        return raw_to_detail(data)

    @async_retry(max_attempts=3)
    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        parent = await self._resolve_parent(mailbox)
        result = await self._api_post(parent, f"{_API_BASE}/messages/{message_id}/trash")
        return "id" in result or "threadId" in result

    @async_retry(max_attempts=3)
    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        parent = await self._resolve_parent(mailbox)
        result = await self._api_post(
            parent,
            f"{_API_BASE}/messages/{message_id}/modify",
            json_body={"removeLabelIds": ["UNREAD"]},
        )
        return "id" in result or "threadId" in result

    @async_retry(max_attempts=3)
    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        parent = await self._resolve_parent(mailbox)
        data = await self._api_get(
            parent, f"{_API_BASE}/messages/{message_id}", params={"format": "raw"}
        )
        return raw_to_source(data, message_id)
