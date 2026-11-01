# Guide: Adding New Email Providers to mailtmapi (for AI Agents & Developers)

This guide provides an end-to-end, deterministic specification for adding new temporary-email provider adapters to `mailtmapi`. It is tailored specifically for **AI coding agents** and human contributors to ensure high reliability, 100% test coverage, and clean architectural alignment.

---

## 🏗️ 1. Architecture & Core Contracts

Every provider adapter in `mailtmapi` is a class implementing the `MailProvider` protocol (`src/mailtmapi/providers/base.py`).

Most providers communicate via HTTP and should inherit from `HttpProvider`, which provides:
- An owned or shared `HttpClient` (with proxy support and configurable default headers).
- Target domain caching with double-checked locking (`list_targets(fresh=...)`).
- Resilient JSON request helpers (`_get_json`, `_post_json`, `_delete_json`) decorated with `@async_retry()`.
- Default fallback hooks for optional capabilities (`delete_mailbox`, `mark_read`).

```
                ┌────────────────────────────┐
                │   MailProvider (Protocol)  │
                └─────────────┬──────────────┘
                              │ implements
                ┌─────────────▼──────────────┐
                │    HttpProvider (Base)     │
                └─────────────┬──────────────┘
                              │ inherits
     ┌────────────────────────┼────────────────────────┐
     ▼                        ▼                        ▼
MailTM                   TempMailPlus              YourNewProvider
(mail.tm)              (tempmail.plus)          (custom-service.tld)
```

---

## 📋 2. Provider Capabilities Matrix

Each provider declares its capabilities via `ProviderCapabilities`:

```python
from mailtmapi.providers.base import ProviderCapabilities

capabilities = ProviderCapabilities(
    can_choose_username=True,  # User can pick 'custom_name@...'
    can_choose_domain=True,  # User can choose from list_targets()
    can_set_password=False,  # Remote supports mailbox passwords / PINs
    supports_delete_mailbox=True,  # Remote has API to destroy the mailbox
    supports_delete_message=True,  # Remote has API to delete individual messages
    supports_mark_read=False,  # Remote has API/flag to mark message as read
    supports_source=True,  # Remote returns raw RFC822 MIME source
    supports_attachments=True,  # Remote supports file attachments
)
```

---

## 📂 3. Directory Layout

Place every provider in its own directory under `src/mailtmapi/providers/<provider_slug>/`:

```
src/mailtmapi/providers/my_provider/
├── __init__.py        # Re-exports the provider class
└── service.py         # Full implementation inheriting from HttpProvider
tests/
└── test_my_provider.py # Comprehensive hermetic test suite
```

---

## 💻 4. Step-by-Step Implementation Guide

### Step 4.1: Create `src/mailtmapi/providers/my_provider/__init__.py`

```python
from .service import MyProvider

__all__ = ["MyProvider"]
```

### Step 4.2: Implement `src/mailtmapi/providers/my_provider/service.py`

Below is the standard, production-tested template for a domain-based provider:

```python
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...http import HttpClient
from ...utils.misc import random_string
from ...utils.retry import async_retry
from ..base import (
    Attachment,
    HttpProvider,
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    ProviderCapabilities,
    Target,
    TargetKind,
    parse_from_value,
    parse_iso,
    split_address,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 300.0
_BASE_URL = "https://api.myprovider.com"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def _summary(raw: dict[str, Any], fallback_address: str = "") -> MessageSummary:
    from_raw = str(raw.get("from") or "")
    party = parse_from_value(from_raw)

    return MessageSummary(
        id=str(raw.get("id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=party,
        to=[Party(address=str(raw.get("to") or fallback_address))],
        intro=str(raw.get("intro") or "")[:200],
        seen=bool(raw.get("is_read") or raw.get("seen", False)),
        has_attachments=bool(raw.get("attachments")),
        size=int(raw.get("size") or 0),
        received_at=parse_iso(raw.get("created_at") or raw.get("date")),
    )


def _detail(raw: dict[str, Any], fallback_address: str = "") -> MessageDetail:
    s = _summary(raw, fallback_address)
    html_list = raw.get("html") or []
    if isinstance(html_list, str):
        html_list = [html_list]

    attachments: list[Attachment] = []
    for a in raw.get("attachments") or []:
        if isinstance(a, dict):
            attachments.append(
                Attachment(
                    id=str(a.get("id") or ""),
                    filename=str(a.get("filename") or ""),
                    content_type=str(a.get("content_type") or "application/octet-stream"),
                    size=int(a.get("size") or 0),
                    download_url=str(a.get("url") or ""),
                )
            )

    return MessageDetail(
        id=s.id,
        subject=s.subject,
        from_=s.from_,
        to=s.to,
        intro=s.intro,
        seen=s.seen,
        has_attachments=bool(attachments) or s.has_attachments,
        size=s.size or len(str(raw.get("text") or "")),
        received_at=s.received_at,
        text=str(raw.get("text") or ""),
        html=list(html_list),
        attachments=attachments,
    )


class MyProvider(HttpProvider):
    slug = "myprovider.com"
    name = "MyProvider"
    website = "https://myprovider.com"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = _BASE_URL

    capabilities = ProviderCapabilities(
        can_choose_username=True,
        can_choose_domain=True,
        can_set_password=False,
        supports_delete_mailbox=True,
        supports_delete_message=True,
        supports_mark_read=True,
        supports_source=True,
        supports_attachments=True,
    )

    def __init__(self, http: HttpClient | None = None, proxy: str | None = None) -> None:
        super().__init__(http=http, proxy=proxy)

    def _auth_headers(self, token: str) -> dict[str, str]:
        headers = self._headers()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        """Fetch usable domain targets from upstream."""
        data = await self._get_json(f"{self.BASE_URL}/api/domains")
        if not isinstance(data, list):
            raise MailAPIError(f"{self.slug}: unexpected domains response")

        targets: list[Target] = []
        for item in data:
            domain = str(item.get("domain") or item.get("name") or "")
            if domain:
                targets.append(Target(id=domain, kind="domain", provider=self.slug, label=domain))
        return targets

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        """Create a mailbox. spec.address or spec.domain may be provided."""
        if spec.address:
            try:
                username, domain = split_address(spec.address)
            except ValueError as exc:
                raise MailValidationError(f"{self.slug}: invalid address {spec.address!r}") from exc
        else:
            username = random_string(10)
            if spec.domain:
                domain = spec.domain
            else:
                targets = await self.list_targets()
                if not targets:
                    raise MailAPIError(f"{self.slug}: no targets available")
                domain = targets[0].label

        full_address = f"{username}@{domain}"

        # Upstream request (e.g. POST /api/accounts)
        payload = {"address": full_address}
        resp = await self._post_json(f"{self.BASE_URL}/api/accounts", payload)
        if not isinstance(resp, dict) or not resp.get("token"):
            raise MailAPIError(f"{self.slug}: failed to create mailbox")

        return MailboxInfo(
            provider=self.slug,
            address=full_address,
            token=str(resp["token"]),
            provider_account_id=str(resp.get("id") or ""),
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        """Destroy mailbox on upstream service."""
        try:
            await self._delete_json(
                f"{self.BASE_URL}/api/accounts/{quote(mailbox.provider_account_id or mailbox.address, safe='')}"
            )
        except Exception:
            logger.warning("{}: upstream delete failed for {}", self.slug, mailbox.address)
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        """Fetch list of messages."""
        headers = self._auth_headers(mailbox.token)
        resp = await self._http.get(
            f"{self.BASE_URL}/api/messages",
            params={"page": page},
            headers=headers,
        )
        if resp.status_code == 404:
            return []
        data = resp.json()
        if not isinstance(data, list):
            data = data.get("messages", []) if isinstance(data, dict) else []
        return [_summary(m, mailbox.address) for m in data if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        """Fetch full message content."""
        headers = self._auth_headers(mailbox.token)
        resp = await self._http.get(
            f"{self.BASE_URL}/api/messages/{quote(message_id, safe='')}",
            headers=headers,
        )
        if resp.status_code == 404:
            raise MailNotFoundError(f"{self.slug}: message {message_id!r} not found")
        data = resp.json()
        if not isinstance(data, dict):
            raise MailAPIError(f"{self.slug}: invalid message detail")
        return _detail(data, mailbox.address)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        """Delete message on upstream service."""
        headers = self._auth_headers(mailbox.token)
        await self._http.delete(
            f"{self.BASE_URL}/api/messages/{quote(message_id, safe='')}",
            headers=headers,
        )
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        """Mark message as read on upstream service."""
        headers = self._auth_headers(mailbox.token)
        await self._http.patch(
            f"{self.BASE_URL}/api/messages/{quote(message_id, safe='')}",
            json={"is_read": True},
            headers=headers,
        )
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        """Fetch raw RFC822 source."""
        headers = self._auth_headers(mailbox.token)
        resp = await self._http.get(
            f"{self.BASE_URL}/api/messages/{quote(message_id, safe='')}/source",
            headers=headers,
        )
        if resp.status_code == 404:
            raise MailNotFoundError(f"{self.slug}: source for {message_id!r} not found")
        raw_text = resp.text
        return MessageSource(id=message_id, data=raw_text)
```

---

## 🔌 5. Registration & Live Test Integration

Provider registration is centralized in `src/mailtmapi/providers/registry.py`:

1. Import your new provider in `src/mailtmapi/providers/registry.py`:
   ```python
   from .my_provider import MyProvider
   ```
2. Register it in `create_public_providers()`:
   ```python
   def create_public_providers(
       http: Any = None,
       settings: Any = None,
   ) -> list[MailProvider]:
       ...
       return [
           MailTM(http=http),
           TempMailPlus(http=http),
           TempMailIO(http=http),
           TempTF(http=http, gmail_dot=temp_tf_dot, gmail_plus=temp_tf_plus),
           AnonymMailNet(http=http),
           DispoEmailOrg(http=http),
           NoopMail(http=http),
           MyProvider(http=http),  # <--- Registered here
       ]
   ```

Both `src/mailtmapi/app/main.py` and the live verification suite (`scripts/test_providers_live.py`) load active adapters directly from `create_public_providers()`.

---

### 🌐 Live Verification Suite, E2E Delivery & Issue Automation

The repository includes an autonomous live test runner (`scripts/test_providers_live.py`). It dynamically instantiates providers as factories `(slug, name, website, lambda client: Provider(http=client))`.

#### 1. Required Provider Metadata Attributes
Ensure your provider class defines these 3 class attributes:
```python
class MyProvider(HttpProvider):
    slug = "myprovider.com"  # Unique provider key used in API routes and state
    name = "MyProvider"  # Human-readable display title for tables and alerts
    website = "https://myprovider.com"  # Official service homepage URL
```

#### 2. What Gets Verified Live in CI
* **Target Discovery (`list_targets`)**: Verifies domain acquisition from upstream.
* **Mailbox Creation (`create_mailbox`)**: Generates an ephemeral mailbox with a random address.
* **Inbox Listing (`list_messages`)**: Tests polling messages from upstream servers.
* **Real E2E Email Delivery (`execute_email_delivery`)**:
  * Dispatches an external email with a unique verification token via `scripts/test_mail_sender`;
  * Polls the inbox until the message arrives, measuring real latency (typically 3–15s).
* **Mailbox Cleanup (`delete_mailbox`)**: Destroys the test mailbox on the remote service.

#### 3. Automatic Health State Tracking & Circuit Breaker
* **State File (`.github/provider_health_state.json`)**:
  Tracks consecutive failures per provider. Automatically initializes newly registered slugs on first run with `consecutive_failures: 0` without manual JSON editing.
* **Circuit Breaker (3 Consecutive Failures)**:
  If a provider experiences **3 consecutive failures** on API operations OR email delivery during scheduled runs, an automated GitHub Issue is created with diagnostic logs and labels (`bug`, `provider-outage`, `automated-health`).
* **Auto-recovery**:
  When the provider recovers (both API and delivery pass), the issue is automatically commented and closed by the bot.
* **README & PR Badges**:
  - Live status table in `README.md` (`<!-- provider-status:start -->`) updates twice daily;
  - Sticky notice (`<!-- mailtmapi-pr-provider-health -->`) posts to Pull Requests affecting provider code.

> 🔒 **Excluded Providers (`EXCLUDED_LIVE_TEST_PROVIDERS`):**
> By default, **all** registered providers are automatically included in live health and delivery tests. The only exceptions are providers requiring pre-authenticated user credentials or private OAuth accounts (such as Gmail), which are registered in `EXCLUDED_LIVE_TEST_PROVIDERS = frozenset({"gmail"})`.

---

## 🧪 6. Writing Hermetic Unit Tests

Every new provider MUST have a dedicated test file `tests/test_<provider_name>.py`.
Tests must be hermetic and not rely on live internet connections. Use `httpx.MockTransport`.

```python
from __future__ import annotations

import httpx
import pytest

from mailtmapi.exceptions import MailNotFoundError, MailValidationError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.my_provider import MyProvider


def _provider_with_routes(routes: dict[tuple[str, str], httpx.Response]) -> MyProvider:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key in routes:
            return routes[key]
        return httpx.Response(404, json={"detail": f"no mock for {key}"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    http = HttpClient(client=client)
    return MyProvider(http=http)


@pytest.mark.asyncio
async def test_list_targets():
    routes = {
        ("GET", "/api/domains"): httpx.Response(
            200, json=[{"domain": "foo.com"}, {"domain": "bar.com"}]
        ),
    }
    p = _provider_with_routes(routes)
    targets = await p.list_targets()
    assert len(targets) == 2
    assert targets[0].label == "foo.com"
    assert targets[1].label == "bar.com"


@pytest.mark.asyncio
async def test_create_mailbox():
    routes = {
        ("GET", "/api/domains"): httpx.Response(200, json=[{"domain": "foo.com"}]),
        ("POST", "/api/accounts"): httpx.Response(201, json={"id": "acc_1", "token": "tok_xyz"}),
    }
    p = _provider_with_routes(routes)
    box = await p.create_mailbox(MailboxSpec(domain="foo.com"))
    assert box.provider == "myprovider.com"
    assert box.token == "tok_xyz"
    assert box.address.endswith("@foo.com")


@pytest.mark.asyncio
async def test_create_mailbox_invalid_address():
    p = _provider_with_routes({})
    with pytest.raises(MailValidationError):
        await p.create_mailbox(MailboxSpec(address="invalid_no_at"))


@pytest.mark.asyncio
async def test_list_and_get_messages():
    routes = {
        ("GET", "/api/messages"): httpx.Response(
            200,
            json=[
                {
                    "id": "m1",
                    "subject": "Hello",
                    "from": "Sender <s@test.com>",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ],
        ),
        ("GET", "/api/messages/m1"): httpx.Response(
            200,
            json={"id": "m1", "subject": "Hello", "text": "body", "html": ["<p>body</p>"]},
        ),
    }
    p = _provider_with_routes(routes)
    box = MailboxInfo(provider="myprovider.com", address="u@foo.com", token="tok_xyz")

    msgs = await p.list_messages(box)
    assert len(msgs) == 1
    assert msgs[0].id == "m1"
    assert msgs[0].from_.address == "s@test.com"

    detail = await p.get_message(box, "m1")
    assert detail.text == "body"


@pytest.mark.asyncio
async def test_message_not_found():
    p = _provider_with_routes({})
    box = MailboxInfo(provider="myprovider.com", address="u@foo.com", token="tok_xyz")
    with pytest.raises(MailNotFoundError):
        await p.get_message(box, "nonexistent")
```

---

## 📖 7. Updating Documentation & Configuration

Whenever a new provider is added or updated, ensure project documentation and configuration files are kept in sync:

1. **`README.md`**:
   - Increment the supported providers count in the **✨ Features** section.
   - Add the provider name and a concise description to the features list.
   - Add a row to the **🌐 Supported Providers & Capabilities** table detailing its capabilities (`Target Kind`, `Custom Username`, `Custom Domain`, `Passwords / PIN`, `Raw Source`, `Read Tracking`).
   - If the provider introduces new settings in `src/mailtmapi/settings.py`, document all environment variables in the **⚙️ Configuration Reference** table.

2. **Web Dashboard & Developer Hub (`src/mailtmapi/static/docs.html`)**:
   - Add a corresponding row to the **Supported Providers** table in `#tab-providers` with appropriate badge classes (`badge--domain`, `badge--yes`, `badge--no`, etc.).

3. **Environment Template (`.env.example`)**:
   - If the provider has optional or configurable settings (e.g. custom headers, origins, syntax toggles), document them with commented defaults and explanatory notes.

4. **This Guide (`docs/ADDING_PROVIDERS.md`)**:
   - Keep provider lists, capabilities matrix, and registry examples up to date.

---

## ✅ 8. AI Agent Pre-flight Verification Checklist

Before finalizing any new provider implementation, execute the following commands in the workspace:

1. **Ruff linting check**:
   ```bash
   uv run ruff check src tests client scripts
   ```
2. **Mypy type-checking check**:
   ```bash
   uv run mypy src
   ```
3. **Execute the provider unit test**:
   ```bash
   uv run pytest tests/test_<provider_name>.py
   ```
4. **Execute the full test suite**:
   ```bash
   uv run pytest
   ```
5. **Verify live provider operations & real email delivery**:
   ```bash
   # Quick API-only check (skips external email delivery):
   uv run python scripts/test_providers_live.py --providers <my_slug> --no-delivery

   # Full live E2E check (including real email dispatch & inbox polling):
   uv run python scripts/test_providers_live.py --providers <my_slug>
   ```
6. **Verify standalone client mirror integrity**:
   ```bash
   python scripts/build_client.py --check
   ```
7. **Verify documentation and configuration sync**:
   - Verify `README.md`, `src/mailtmapi/static/docs.html`, and `.env.example` include the new provider and any new settings.
