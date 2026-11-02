# maily-client

[![PyPI version](https://img.shields.io/pypi/v/maily-client.svg)](https://pypi.org/project/maily-client/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/maily-client.svg)](https://pypi.org/project/maily-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/maily-client.svg)](https://pypi.org/project/maily-client/)
[![CI Pipeline](https://github.com/stormsia/maily/actions/workflows/ci.yml/badge.svg)](https://github.com/stormsia/maily/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Typing: Typed](https://img.shields.io/badge/typing-typed-blue.svg)](https://peps.python.org/pep-0561/)
[![maily-server](https://img.shields.io/pypi/v/maily-server.svg?label=maily-server)](https://pypi.org/project/maily-server/)
[![API Docs](https://img.shields.io/badge/Docs-GitHub%20Pages-success?logo=github)](https://stormsia.github.io/maily/)

**Fast, fully-typed async & sync Python SDK for the [maily](https://github.com/stormsia/maily) multi-provider temporary email platform.**

Built for integration tests (Pytest, Playwright, Selenium, Cypress), automation bots, and QA verification pipelines. Features 1-line disposable mailbox creation, automatic OTP verification code extraction via regex, magic activation link parsing, real-time message streaming, and resilient networking.

---

### 🔗 Quick Links

- 📖 **Documentation & Guides:** [https://stormsia.github.io/maily/](https://stormsia.github.io/maily/)
- 🚀 **Server Package (PyPI):** [https://pypi.org/project/maily-server/](https://pypi.org/project/maily-server/)
- 📦 **Client Package (PyPI):** [https://pypi.org/project/maily-client/](https://pypi.org/project/maily-client/)
- 🐙 **GitHub Repository:** [https://github.com/stormsia/maily](https://github.com/stormsia/maily)
- 🐛 **Issue Tracker:** [https://github.com/stormsia/maily/issues](https://github.com/stormsia/maily/issues)
- 📝 **Changelog:** [https://github.com/stormsia/maily/blob/main/CHANGELOG.md](https://github.com/stormsia/maily/blob/main/CHANGELOG.md)

---

## ✨ Key Features

- **Standard Import (`maily_client`)**: Clean, conflict-free Python imports (`from maily_client import Maily, SyncMaily`).
- **Single-File Portability**: Ships as a lightweight client requiring only `httpx`, `loguru`, and `pydantic`. Zero heavy dependencies.
- **Fully Typed (PEP 561)**: 100% type annotations with `py.typed` compliance and Pydantic response models for rich IDE autocompletion.
- **Async & Sync Support**: Native `async/await` (`Maily`) with high-concurrency polling, plus a lightweight synchronous facade (`SyncMaily`) for traditional test suites.
- **Magic Verification Extraction**: Built-in polling and regex extraction for OTP verification codes (`wait_for_code`) and account activation links (`wait_for_link`).
- **Resilient Networking**: Optional exponential backoff retry policy handling transient errors (HTTP 502/504, connection timeouts) and honoring HTTP 429 `Retry-After`.
- **Self-Updating CLI**: Built-in CLI tool `maily-client` to check for and apply updates directly from git.

---

## 📦 Installation & Import

### Preferred — via PyPI:

```bash
pip install maily-client
```

### Import in Python:

```python
from maily_client import Maily, SyncMaily, WaitTimeoutError
```

### Alternative 1: Direct from GitHub:

```bash
pip install "maily-client @ git+https://github.com/stormsia/maily.git#subdirectory=client"
```

### Alternative 2: Standalone Single-File Download (Zero Install)

Because the client has no internal server dependencies, you can download `maily_client.py` directly into your project:

```bash
# Linux / macOS
curl -O https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py

# Windows PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py" -OutFile "maily_client.py"
```

Dependencies for standalone use:
```bash
pip install httpx loguru pydantic
```

---

## ⚠️ Important: Attribute Access vs Dictionary Key Access

> **CRITICAL RULE:**
> In `maily-client`, **native dot/attribute access is supported ONLY on Pydantic models and specifically `ExtractedConfirmation`** (which implements `Mapping` and allows dual access: both `res.confirmation_code` and `res["confirmation_code"]`).
>
> **All other client methods returning standard Python dictionaries** (such as `await api.config.get()`, `sync_api.config.get()`, or raw response dicts) **DO NOT support attribute/dot access**. You MUST access dictionary values using standard bracket key indexing (`d["key"]`), NEVER dot syntax (`d.key`).

```python
# 1. ExtractedConfirmation (Pydantic model implementing Mapping) supports BOTH:
res = await api.wait_for_confirmation_email(box, digit_code_mask=r"\b(\d{6})\b")
if res is not None:
    # ✅ Attribute / dot access:
    print(res.subject)
    print(res.confirmation_code)
    print(res.confirmation_link)
    print(res.message_id)
    print(res.from_address)

    # ✅ Dictionary mapping access:
    print(res["confirmation_code"])
    print(res["confirmation_link"])
    print(res["subject"])

# 2. Standard dictionary responses (e.g., api.config.get()):
cfg = await api.config.get()
print(cfg["client_version"])  # ✅ CORRECT: standard dictionary indexing
# print(cfg.client_version)   # ❌ ERROR: AttributeError ('dict' object has no attribute 'client_version')
```

---

## 🚀 Quickstart

### 1. Basic Mailbox Creation & Health Check

```python
import asyncio
from maily_client import Maily


async def main() -> None:
    # Connect to your self-hosted maily server
    async with Maily("http://127.0.0.1:8477", api_key="your_secret_api_key") as api:
        # Check server health
        health = await api.health.ping()
        print(f"Server health: {health.status}")

        # Create a temporary disposable mailbox (auto-selects available domain)
        box = await api.create_temp_mailbox()
        print(f"Created mailbox: {box.address} (ID: {box.id})")


asyncio.run(main())
```

### 2. Waiting for OTP / Verification Code (`wait_for_code`)

Ideal for automated signup flows (e.g., Pytest, Playwright, Selenium):

```python
import asyncio
from maily_client import Maily, WaitTimeoutError


async def main() -> None:
    async with Maily("http://127.0.0.1:8477") as api:
        box = await api.create_temp_mailbox()
        print(f"Use {box.address} in your registration form...")

        # Wait up to 60 seconds for an incoming email with an OTP
        # Default pattern matches 4 to 8 digits (\b\d{4,8}\b)
        try:
            otp_code = await api.wait_for_code(
                box,
                pattern=r"\b(\d{6})\b",  # Optional custom regex
                sender_domain="auth.example.com",  # Optional sender domain filter
                timeout=60.0,
                check_interval=2.0,
            )
            print(f"Extracted verification code: {otp_code}")
        except WaitTimeoutError:
            print("Timed out waiting for verification code.")


asyncio.run(main())
```

### 3. Waiting for Activation Link (`wait_for_link`)

Extract confirmation or magic links automatically from incoming HTML or plain-text emails:

```python
import asyncio
from maily_client import Maily


async def main() -> None:
    async with Maily("http://127.0.0.1:8477") as api:
        box = await api.create_temp_mailbox()
        print(f"Waiting for activation email to: {box.address}...")

        # Find link containing specific keywords
        activation_url = await api.wait_for_link(
            box,
            url_contain=["verify", "activate", "confirm"],
            sender_domain="example.com",
            timeout=60.0,
        )
        print(f"Activation link: {activation_url}")


asyncio.run(main())
```

### 4. Advanced Confirmation Extraction (`wait_for_confirmation_email`)

Extract both link and code simultaneously in a single polling loop with dual-access support:

```python
import asyncio
from maily_client import ExtractedConfirmation, Maily


async def main() -> None:
    async with Maily("http://127.0.0.1:8477") as api:
        box = await api.create_temp_mailbox()

        res: ExtractedConfirmation | None = await api.wait_for_confirmation_email(
            box,
            sender_domain="service.com",
            url_contain=["token", "confirm"],
            digit_code_mask=r"\b(\d{6})\b",
            timeout=60.0,
            check_interval=3.0,
        )
        if res is not None:
            # Dual-access: attribute access
            print(f"Subject: {res.subject}")
            print(f"From: {res.from_address}")
            print(f"Message ID: {res.message_id}")
            print(f"Code: {res.confirmation_code}")
            print(f"Link: {res.confirmation_link}")

            # Dual-access: dictionary mapping access
            code = res["confirmation_code"]
            link = res["confirmation_link"]
            print(f"Code from dict access: {code}, Link: {link}")


asyncio.run(main())
```

### 5. Synchronous Facade (`SyncMaily`)

For synchronous test suites (standard Pytest, unittest, Selenium) or scripts where `async/await` is inconvenient:

```python
from maily_client import SyncMaily

# Sync context manager automatically manages an isolated background thread and event loop
with SyncMaily("http://127.0.0.1:8477", api_key="your_secret_api_key") as api:
    # 1. Create a mailbox synchronously
    box = api.create_temp_mailbox()
    print(f"Created mailbox: {box.address}")

    # 2. Wait for code synchronously (blocks until email arrives or timeout raises WaitTimeoutError)
    code = api.wait_for_code(box, timeout=45.0)
    print(f"Verification code: {code}")

    # 3. Wait for confirmation email synchronously
    res = api.wait_for_confirmation_email(
        box,
        url_contain=["verify"],
        digit_code_mask=r"\b(\d{6})\b",
        timeout=30.0,
    )
    if res:
        print(f"Link: {res.confirmation_link}, Code: {res['confirmation_code']}")

    # 4. Access sync sections directly
    messages = api.messages.list(box)
    print(f"Total messages: {len(messages)}")

    # 5. Clean up mailbox
    api.delete_mailbox(box)
```

---

## 🛠️ API Overview & Structure

`Maily` exposes organized domain resource sections as well as top-level flat convenience methods:

### Resource Sections

| Section | Description | Key Methods |
| :--- | :--- | :--- |
| `api.mailboxes` | Mailbox lifecycle | `create()`, `list()`, `get()`, `by_address()`, `delete()` |
| `api.messages` | Message inspection & polling | `list()`, `get()`, `mark_read()`, `delete()`, `source()`, `wait_for()`, `wait_for_confirmation_email()`, `wait_for_code()`, `wait_for_link()`, `iter_messages()` |
| `api.providers` | Upstream provider status | `list()`, `targets()` |
| `api.gmail` | Gmail OAuth multi-tenant management | `oauth_start()`, `import_account()`, `accounts()`, `delete_account()`, `sync()` |
| `api.admin` | Server administration | `stats()`, `retention_list()`, `retention_set()`, `retention_disable()`, `retention_run()`, `domain_cache()`, `domain_cache_save()`, `domain_cache_run()` |
| `api.keys` | API keys management | `create()`, `list()`, `get()`, `delete()`, `me()`, `update()`, `rotate()`, `secret()`, `retention_set()` |
| `api.health` | System health | `ping()` |
| `api.config` | Server public configuration | `get()` (returns `dict[str, Any]` — use `dict["key"]`) |

---

## ⚡ Flat Facade Shortcut Methods

Both `Maily` (async) and `SyncMaily` (sync) provide direct top-level facade shortcuts for rapid automation. All 19 flat shortcut methods forward directly to their respective section implementations:

| # | Facade Method Signature | Return Type | Description |
|---|---|---|---|
| 1 | `create_mailbox(*, provider=None, domain=None, parent_id=None, address=None, password=None)` | `Mailbox` | Creates a new disposable or parent mailbox. |
| 2 | `list_mailboxes(provider=None, active=None)` | `list[Mailbox]` | Lists mailboxes registered under the active API key. |
| 3 | `mailbox(mailbox_id: int \| Mailbox)` | `Mailbox` | Retrieves details and metadata for a specific mailbox ID. |
| 4 | `mailbox_by_address(email: str)` | `Mailbox` | Finds a mailbox by its exact email address string. |
| 5 | `delete_mailbox(mailbox_id: int \| Mailbox)` | `None` | Deletes a mailbox and purges all its stored messages. |
| 6 | `list_messages(mailbox_id: int \| Mailbox, page: int = 1)` | `list[MessageSummary]` | Lists message headers/summaries received by the mailbox. |
| 7 | `get_message(mailbox_id: int \| Mailbox, message_id: str)` | `MessageDetail` | Retrieves complete message body, HTML, attachments, and text. |
| 8 | `mark_read(mailbox_id: int \| Mailbox, message_id: str)` | `MessageSummary` | Marks the specified message as read on the upstream provider. |
| 9 | `delete_message(mailbox_id: int \| Mailbox, message_id: str)` | `None` | Permanently deletes a message from the mailbox. |
| 10 | `get_source(mailbox_id: int \| Mailbox, message_id: str)` | `MessageSource` | Fetches the raw RFC822 MIME source data and download URL. |
| 11 | `gmail_oauth_start()` | `OAuthStart` | Initiates Google OAuth2 consent flow, returning `auth_url` and `state`. |
| 12 | `gmail_import_account(*, refresh_token=None, token_json=None)` | `GmailAccount` | Connects a Gmail parent account via OAuth refresh token or JSON credential. |
| 13 | `list_gmail_accounts()` | `list[GmailAccount]` | Lists all registered Gmail parent accounts and their `send_as` aliases. |
| 14 | `delete_gmail_account(parent_id: int)` | `None` | Removes a connected Gmail parent account and disables its aliases. |
| 15 | `sync_gmail_account(parent_id: int)` | `GmailAccount` | Triggers immediate upstream IMAP/REST synchronization for a Gmail account. |
| 16 | `domain_cache_settings()` | `DomainCache` | Inspects provider domain background cache status and refresh interval. |
| 17 | `save_domain_cache_settings(*, enabled=None, interval_seconds=None)` | `DomainCache` | Updates background domain cache configuration. |
| 18 | `refresh_domain_cache()` | `DomainCacheRun` | Triggers an immediate cache refresh sweep across all providers. |
| 19 | `wait_for_message(mailbox_id, *, timeout=120.0, interval=2.0, predicate=None)` | `MessageSummary` | Polls mailbox until a message arrives matching an optional predicate filter. |

### Additional Root Convenience Methods

- `create_temp_mailbox(*, provider: str | None = None, domain: str | None = None) -> Mailbox` — Instantly creates a temporary mailbox, automatically selecting the best available active domain if omitted.
- `wait_for_code(mailbox_id, *, pattern=r"\b(\d{4,8})\b", sender_domain=None, timeout=60.0, check_interval=3.0) -> str` — Polls for incoming email and returns the extracted digit verification code (raises `WaitTimeoutError` on timeout).
- `wait_for_link(mailbox_id, *, url_contain=None, sender_domain=None, timeout=60.0, check_interval=3.0) -> str` — Polls for incoming email and returns the matching activation URL (raises `WaitTimeoutError` on timeout).
- `wait_for_confirmation_email(mailbox_id, *, sender_domain=None, url_contain=None, digit_code_mask=None, timeout=60.0, check_interval=5.0) -> ExtractedConfirmation | None` — High-level extractor returning `ExtractedConfirmation` (supports dot and dict access) or `None` on timeout.
- `check_client_version() -> str` — Queries `/v1/config` and logs a warning via Loguru if the client version does not match the server.

---

## 💻 CLI Commands

The package includes a command-line interface executable as `maily-client` (or via `python -m maily_client`):

```bash
# Display help and usage
maily-client --help

# Show current installed client version
maily-client version

# Check GitHub repository for newer version (exit codes: 0=up-to-date, 2=update available, 1=network error)
maily-client check

# Download and replace local client file with latest release from GitHub
maily-client update
```

### CLI Exit Codes

| Exit Code | Meaning |
| :---: | :--- |
| `0` | Success / local client file is already up to date. |
| `1` | Network or I/O failure (failed to connect to GitHub or file write error). |
| `2` | Update available (when running `check`), or invalid CLI argument. |

### Environment Variables

- `MAILY_CLIENT_SOURCE`: URL to fetch the canonical client from when checking or updating (defaults to GitHub `main` branch raw file: `https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py`).

---

## 🛡️ Error Handling & Resiliency

The client provides explicit exceptions inheriting from `ClientError`:

```
ClientError
 ├── WaitTimeoutError
 └── ApiError
      ├── AuthenticationError   (HTTP 401: Invalid API key or missing Authorization header)
      ├── ForbiddenError        (HTTP 403: Scoped API key does not have permission)
      ├── NotFoundError         (HTTP 404: Mailbox or message does not exist)
      ├── ValidationError       (HTTP 422: Malformed input or schema validation failure)
      ├── RateLimitError        (HTTP 429: Rate limited by server or upstream provider)
      └── UpstreamProviderError (HTTP 502 / 504: Upstream temporary mail provider failure)
```

### HTTP 422 Validation Error Formatting

FastAPI validation errors returning a list of field error objects (`[{"loc": ["body", "domain"], "msg": "..."}]`) are automatically formatted into readable messages:

```python
from maily_client import Maily, ValidationError

async with Maily("http://127.0.0.1:8477") as api:
    try:
        # Invalid input parameters
        await api.mailboxes.create(domain="invalid domain!@#")
    except ValidationError as exc:
        print(f"Status Code: {exc.status_code}")  # 422
        # Clean formatted string: "body -> domain: Value error, invalid domain name characters"
        print(f"Validation Detail: {exc.detail}")
```

### HTTP 429 Rate Limiting & Automatic Retries

When `max_retries > 0`, the client automatically honors HTTP 429 `Retry-After` headers and applies exponential backoff for transient HTTP 502/504 errors and network connection timeouts:

```python
from maily_client import Maily, RateLimitError

# Configure client-side retry policy
api = Maily(
    "http://127.0.0.1:8477",
    max_retries=3,  # Retry up to 3 times before raising
    retry_backoff=0.5,  # Base backoff in seconds (0.5s, 1.0s, 2.0s)
)

try:
    box = await api.create_temp_mailbox()
except RateLimitError as exc:
    # If retries are exhausted or max_retries is 0
    print(f"Rate limited (HTTP 429). Server message: {exc.detail}")
```

---

## 📄 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
