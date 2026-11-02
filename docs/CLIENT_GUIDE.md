# 📖 Maily Client SDK Developer Guide & Cookbook

A complete, practical reference manual and cookbook for [`maily-client`](https://pypi.org/project/maily-client/) — the zero-heavy-dependency, fully-typed async & sync Python SDK for the [maily](https://github.com/stormsia/maily) multi-provider temporary email platform.

---

## 📑 Table of Contents

1. [Architectural Overview & Highlights](#architectural-overview-highlights)
2. [Installation & Distribution Options](#installation-distribution-options)
3. [Core Concepts: Async vs Sync Engines](#core-concepts-async-vs-sync-engines)
4. [⚡ Quickstart Code Snippets](#quickstart-code-snippets)
5. [Workflow 1: Target Discovery & Provider Inspection](#workflow-1-target-discovery-provider-inspection)
6. [Workflow 2: Disposable Mailbox Lifecycle](#workflow-2-disposable-mailbox-lifecycle)
7. [Workflow 3: Messages & Magic Extraction (OTP, Links, Streaming)](#workflow-3-messages-magic-extraction-otp-links-streaming)
8. [Critical Rule: Attribute Access vs. Dictionary Indexing](#critical-rule-attribute-access-vs-dictionary-indexing)
9. [Flat Facade Shortcuts vs. Resource Namespaces](#flat-facade-shortcuts-vs-resource-namespaces)
10. [Data Models & Response Types Reference](#data-models-response-types-reference)
11. [Workflow 4: Scoped API Key Management](#workflow-4-scoped-api-key-management)
12. [Workflow 5: Server Admin, Retention & Maintenance](#workflow-5-server-admin-retention-maintenance)
13. [Workflow 6: Gmail OAuth Multi-Tenant Management](#workflow-6-gmail-oauth-multi-tenant-management)
14. [Resilient Networking, Retries & Error Handling](#resilient-networking-retries-error-handling)
15. [Cookbook & Integration Recipes](#cookbook-integration-recipes)
    * [Recipe 1: Pytest Async Fixture](#recipe-1-pytest-async-fixture-automated-signup)
    * [Recipe 2: Pytest Sync Fixture](#recipe-2-pytest-sync-fixture-standard-pytest)
    * [Recipe 3: Playwright Web Automation](#recipe-3-playwright-web-automation-otp-form-fill)
    * [Recipe 4: Selenium WebDriver Activation Link](#recipe-4-selenium-webdriver-activation-link-flow)
    * [Recipe 5: FastAPI Dependency Injection](#recipe-5-fastapi-lifespan-dependency-injection)
    * [Recipe 6: Corporate Proxy & Custom HTTP Transport](#recipe-6-corporate-proxy-custom-http-transport)
16. [Self-Updating CLI (`maily-client`)](#self-updating-cli-maily-client)

---

## 🏗️ Architectural Overview & Highlights

`maily-client` is engineered specifically for testing suites, automation scripts, scrapers, and microservices:

* **Zero Heavy Dependencies**: Powered exclusively by `httpx`, `pydantic`, and `loguru`. No heavy frameworks or server baggage.
* **Dual Execution Engines**: Async-first with high concurrency (`Maily`), plus a transparent synchronous facade (`SyncMaily`) for traditional blocking environments.
* **Type-Safe Autocompletion (PEP 561)**: Includes `py.typed` marker and typed Pydantic models for IDE completion and strict static analysis with Mypy and Pyright.
* **Single-File Vendoring Option**: The entire client is packaged into a self-contained, single-file module `maily_client.py` that can be directly vendored into external repositories without installation.
* **Magic Extraction Engine**: Built-in polling and regex extractors for 4–8 digit OTP codes (`wait_for_code`) and account activation URLs (`wait_for_link`).
* **Resilient Networking**: Optional exponential backoff retry policy handling transient upstream failures (HTTP 502/504, connection drops) and automatically honoring HTTP 429 `Retry-After`.

---

## 📦 Installation & Distribution Options

### Option 1: Preferred — via PyPI

```bash
pip install maily-client
```

Or using modern package managers like `uv` or `poetry`:
```bash
uv add maily-client
# or: poetry add maily-client
```

Import in Python:
```python
from maily_client import Maily, SyncMaily, WaitTimeoutError
```

### Option 2: Direct from GitHub Repository

```bash
pip install "maily-client @ git+https://github.com/stormsia/maily.git#subdirectory=client"
```

### Option 3: Zero-Install Single-File Vendoring

Because the client has no internal dependencies on the server, you can copy `maily_client.py` directly into your workspace:

```bash
# Linux / macOS
curl -sSL https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py -o maily_client.py

# Windows (PowerShell)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py" -OutFile "maily_client.py"
```

Dependencies for standalone file use:
```bash
pip install httpx loguru pydantic
```

---

## 🔄 Core Concepts: Async vs Sync Engines

`maily-client` offers two mirror execution engines with identical method signatures:

### 1. Async Engine: `Maily`
Use `Maily` inside asynchronous frameworks (`FastAPI`, `asyncio`, `pytest-asyncio`, `Playwright async`, `Tornado`). It uses `httpx.AsyncClient` under the hood:

```python
import asyncio
from maily_client import Maily


async def main():
    async with Maily("http://127.0.0.1:8477", api_key="sk-...") as api:
        box = await api.create_temp_mailbox()
        print(f"Async inbox: {box.address}")


asyncio.run(main())
```

### 2. Synchronous Facade: `SyncMaily`
Use `SyncMaily` for synchronous scripts, procedural tasks, standard `pytest`, `unittest`, or `Selenium WebDriver`. It runs an isolated background event loop on a dedicated thread, meaning **zero `asyncio.run()` boilerplate** and **zero event loop conflicts**:

```python
from maily_client import SyncMaily

with SyncMaily("http://127.0.0.1:8477", api_key="sk-...") as api:
    box = api.create_temp_mailbox()
    print(f"Sync inbox: {box.address}")
    code = api.wait_for_code(box, timeout=45.0)
    print(f"Extracted code: {code}")
```

### 3. Manual Lifecycle (Without Context Manager)
Both clients can also be initialized without context managers and closed explicitly:

```python
# Async
api = Maily("http://127.0.0.1:8477", api_key="sk-...")
# ... perform operations ...
await api.close()

# Sync
sync_api = SyncMaily("http://127.0.0.1:8477", api_key="sk-...")
# ... perform operations ...
sync_api.close()
```

---

## ⚡ Quickstart Code Snippets

<!-- doc-sync:client-quickstart:start -->
The repository includes a dedicated, self-contained standalone Python client package (`maily-client`) requiring only `httpx`, `pydantic`, and `loguru`. It supports both high-concurrency `async/await` (`Maily`) and a synchronous facade (`SyncMaily`).

> 📖 **Full Documentation:** See [CLIENT_GUIDE.md](https://github.com/stormsia/maily/blob/main/docs/CLIENT_GUIDE.md) and [maily-client README](https://github.com/stormsia/maily/blob/main/client/README.md) for comprehensive recipes (Pytest fixtures, Playwright/Selenium automation, streaming, and retry policies).

### Installation

#### Preferred — PyPI package:

```bash
pip install maily-client
```

#### Alternative options:

```bash
# Directly from GitHub repository:
pip install "maily-client @ git+https://github.com/stormsia/maily.git#subdirectory=client"

# Or download the zero-dependency single-file client directly:
curl -O https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py
```

> ⚠️ **Important: Attribute Access vs Dictionary Key Access**
>
> In `maily-client`, native dot/attribute access is supported **ONLY on Pydantic models and specifically `ExtractedConfirmation`** (which implements `Mapping` and supports dual access: e.g. `res.subject`, `res.confirmation_code` as well as `res["confirmation_link"]`).
>
> All other client methods returning standard Python dictionaries (such as `await api.config.get()`) **DO NOT support attribute/dot access**. You MUST use standard dictionary key indexing (`dict["key"]`), never dot access (`dict.key`).

### 1-Line Mailbox & Verification Code Extraction

```python
import asyncio

# Preferred when using maily-client SDK:
from maily_client import Maily, WaitTimeoutError
# (Or if using the maily-server package directly: from maily import Maily, WaitTimeoutError)


async def main():
    async with Maily("http://127.0.0.1:8477", api_key="your_secret_api_key") as api:
        # Create a disposable mailbox with automatic domain selection
        box = await api.create_temp_mailbox()
        print(f"Disposable email: {box.address}")

        # Send an email to box.address, then wait for the code:
        try:
            code = await api.wait_for_code(box, timeout=60.0)
            print(f"Received verification code: {code}")
        except WaitTimeoutError:
            print("Timed out waiting for email.")


asyncio.run(main())
```

### Confirmation Extraction (`ExtractedConfirmation` Dual Access)

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    # Wait for email and extract both verification code and activation link
    res = await api.wait_for_confirmation_email(box, digit_code_mask=r"\b(\d{6})\b")
    if res is not None:
        # 1. Attribute / dot access:
        print(f"Subject: {res.subject}")
        print(f"Code: {res.confirmation_code}")

        # 2. Key mapping access:
        print(f"Link: {res['confirmation_link']}")
        print(f"Code: {res['confirmation_code']}")
```

### Synchronous Client (`SyncMaily`)

```python
# Standalone client:
from maily_client import SyncMaily
# Or via server package: from maily import SyncMaily

with SyncMaily("http://127.0.0.1:8477", api_key="your_secret_api_key") as api:
    box = api.create_temp_mailbox()
    code = api.wait_for_code(box, timeout=45.0)
    print(f"Received code synchronously: {code}")
```

### Confirmation Link Extraction

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox(provider="tempmail.plus")
    print(f"Address: {box.address}")

    # Automatically extracts URLs containing 'confirm', 'verify', or 'activate'
    link = await api.wait_for_link(box, timeout=90.0)
    print(f"Confirmation URL: {link}")
```

### Real-Time Email Streaming (Async Iterator)

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.mailboxes.create(domain="mail.tm")

    # Continuously yields new messages as they arrive
    async for msg in api.messages.iter_messages(box, poll_interval=2.0, timeout=120.0):
        print(f"Incoming: {msg.subject} from {msg.from_address}")
        detail = await api.messages.get(box, msg.message_api_id)
        print("Body text:\n", detail.text)
```

### Granular Exception Handling

All API errors inherit from `ApiError`, which inherits from `ClientError`:

```python
from maily_client import (
    AuthenticationError,  # 401: Invalid API key
    ForbiddenError,  # 403: Scope denied
    NotFoundError,  # 404: Mailbox or message missing
    ValidationError,  # 422 / 400: Bad params
    RateLimitError,  # 429: Rate limited
    UpstreamProviderError,  # 502/504: Provider downtime
    WaitTimeoutError,  # Timeout waiting for email/code
)

try:
    detail = await api.messages.get(box, "unknown_id")
except NotFoundError:
    print("Message not found!")
except AuthenticationError:
    print("Check your API key!")
```

### Scoped API Key Management

```python
async with Maily("http://127.0.0.1:8477", api_key="root_secret") as api:
    # Create key restricted to mail.tm only
    new_key = await api.keys.create(
        name="bot-worker",
        scope={"providers": ["mail.tm"], "parent_ids": [], "actions": ["read", "write"]},
    )
    print(f"Key Prefix: {new_key.prefix} | Secret: {new_key.secret}")
```

### Retention & Database Maintenance

```python
async with Maily("http://127.0.0.1:8477", api_key="root_secret") as api:
    # Run regular retention sweep (triggers DB maintenance if interval has elapsed)
    res = await api.admin.retention_run()
    print(f"Deleted: {res.mailboxes_deleted} boxes, {res.messages_deleted} messages")

    # Or force immediate full database maintenance (VACUUM, REINDEX, ANALYZE):
    res = await api.admin.retention_run(force_maintenance=True)
```
<!-- doc-sync:client-quickstart:end -->

---

## 🌐 Workflow 1: Target Discovery & Provider Inspection

Before creating a mailbox, you can discover all available domains, providers, and their operational capabilities.

### 1. Fetching Usable Targets (`api.providers.targets`)

Returns a list of `Target` objects (`.id`, `.provider`, `.kind`, `.label`).
`kind` is `"domain"` for public disposable providers or `"parent"` for connected Gmail accounts:

```python
async with Maily("http://127.0.0.1:8477") as api:
    # Discover all active targets
    targets = await api.providers.targets()
    for t in targets:
        print(f"Target: {t.label} | Provider: {t.provider} | Kind: {t.kind}")

    # Filter targets by specific provider
    mailtm_targets = await api.providers.targets(provider="mail.tm")
    print(f"mail.tm domains: {[t.label for t in mailtm_targets]}")
```

### 2. Inspecting Provider Capabilities (`api.providers.list`)

Each provider adapter exposes granular boolean capability flags (`ProviderCapabilities`):

```python
async with Maily("http://127.0.0.1:8477") as api:
    providers = await api.providers.list()
    for p in providers:
        caps = p.capabilities
        print(f"\nProvider: {p.slug} ({p.kind})")
        print(f"  Custom Username : {caps.can_choose_username}")
        print(f"  Custom Domain   : {caps.can_choose_domain}")
        print(f"  Password / PIN  : {caps.can_set_password}")
        print(f"  Delete Mailbox  : {caps.supports_delete_mailbox}")
        print(f"  MIME Source     : {caps.supports_source}")
        print(f"  Read Tracking   : {caps.supports_mark_read}")
```

---

## 📬 Workflow 2: Disposable Mailbox Lifecycle

`Maily` makes creating disposable mailboxes effortless, whether you need automatic domain selection or full control over usernames and passwords.

### 1. Automatic 1-Line Disposable Mailbox (`api.create_temp_mailbox`)

Automatically discovers active domains and provisions a mailbox:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()
    print(f"Address: {box.address} (Provider: {box.provider}, ID: {box.id})")
```

### 2. Provider-Specific Mailbox Creation

Target a specific provider (e.g. `tempmail.plus`) and optionally specify a domain:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox(provider="tempmail.plus")
    print(f"Created: {box.address}")
```

### 3. Custom Username & Domain (`api.mailboxes.create`)

When you need a predictable username:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.mailboxes.create(
        provider="mail.tm",
        domain="mail.tm",
        address="qa-bot-2026@mail.tm",
    )
    print(f"Custom mailbox: {box.address}")
```

### 4. Password & PIN Protection

Certain providers support mailbox authentication secrets (`can_set_password: True`):
* `mail.tm`: requires password for persistent mailbox logins.
* `tempmail.plus`: supports optional 4-digit numeric PIN code protection.

```python
async with Maily("http://127.0.0.1:8477") as api:
    # mail.tm with password
    box1 = await api.mailboxes.create(
        domain="mail.tm",
        address="user99@mail.tm",
        password="MySecretPassword123!",
    )

    # tempmail.plus with PIN code
    box2 = await api.mailboxes.create(
        provider="tempmail.plus",
        domain="fexpost.com",
        password="4821",  # 4-digit PIN
    )
```

### 5. Parent Gmail Account Mailboxes (OAuth2 + Plus-Addressing)

If a Gmail parent account is connected, create sub-inboxes with plus or dot aliasing:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.mailboxes.create(
        provider="gmail",
        parent_id=1,
        address="myaccount+signup_test@gmail.com",
    )
    print(f"Gmail alias: {box.address}")
```

### 6. Listing & Searching Mailboxes

List mailboxes with provider filtering, active status, text search, and pagination:

```python
async with Maily("http://127.0.0.1:8477") as api:
    # Filter active mailboxes on mail.tm
    boxes = await api.mailboxes.list(provider="mail.tm", active=True, limit=50)

    # Search mailboxes matching query string
    matching = await api.mailboxes.list(q="qa-bot")
```

### 7. Lookup & Deletion

```python
async with Maily("http://127.0.0.1:8477") as api:
    # Lookup by ID
    box = await api.mailboxes.get(mailbox_id=12)

    # Lookup by exact email address
    box = await api.mailboxes.by_address("qa-bot-2026@mail.tm")

    # Delete mailbox (purges both locally and upstream on provider)
    await api.mailboxes.delete(box)
    # Or using root facade:
    # await api.delete_mailbox(box)
```

---

## ✉️ Workflow 3: Messages & Magic Extraction (OTP, Links, Streaming)

### 1. Magic OTP Verification Code Extraction (`api.wait_for_code`)

Polls the mailbox until an incoming email arrives containing a numeric verification code.
> [!NOTE]
> `wait_for_code` raises `WaitTimeoutError` if timeout elapses before code arrives.

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    # Wait up to 60 seconds for an incoming email with 6-digit code
    code = await api.wait_for_code(
        box,
        pattern=r"\b(\d{6})\b",  # Custom regex (defaults to 4-8 digits)
        sender_domain="auth.acme.com",  # Optional sender domain filter
        timeout=60.0,
        check_interval=2.0,  # Poll every 2 seconds
    )
    print(f"Your OTP code is: {code}")
```

### 2. Magic Activation Link Extraction (`api.wait_for_link`)

Extracts action URLs (e.g. account verification, password reset, login magic links) from HTML or text bodies.
> [!NOTE]
> `wait_for_link` raises `WaitTimeoutError` if timeout elapses before link arrives.

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    # Find link containing specific keywords
    link = await api.wait_for_link(
        box,
        url_contain=["verify", "confirm", "activate", "token"],
        sender_domain="acme.com",
        timeout=90.0,
    )
    print(f"Action URL: {link}")
```

### 3. Dual-Access Confirmation (`api.wait_for_confirmation_email`)

Extracts **both** the code and the activation link in a single polling loop, returning an `ExtractedConfirmation` object.
> [!TIP]
> Unlike `wait_for_code` and `wait_for_link`, `wait_for_confirmation_email` returns `None` on timeout rather than raising `WaitTimeoutError`, allowing clean `if confirmation:` checks.

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    confirmation = await api.wait_for_confirmation_email(
        box,
        digit_code_mask=r"\b(\d{6})\b",
        url_contain=["verify", "token"],
        timeout=60.0,
    )

    if confirmation is not None:
        print(f"Subject   : {confirmation.subject}")
        print(f"Sender    : {confirmation.from_address}")
        print(f"OTP Code  : {confirmation.confirmation_code}")
        print(f"Link URL  : {confirmation.confirmation_link}")
        print(f"Message ID: {confirmation.message_id}")
    else:
        print("Confirmation email did not arrive in time.")
```

### 4. Custom Predicate Polling (`api.messages.wait_for`)

Wait for a message satisfying an arbitrary Python function:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    # Wait for an email whose subject starts with 'Invoice #'
    msg = await api.messages.wait_for(
        box,
        predicate=lambda m: m.subject.startswith("Invoice #"),
        timeout=120.0,
        interval=3.0,
        mark_seen=True,  # Automatically mark as read
    )
    print(f"Found invoice email: {msg.subject} from {msg.from_address}")
```

### 5. Real-Time Streaming Generator (`api.messages.iter_messages`)

Continuously listens for incoming emails and yields them as they arrive:

```python
async with Maily("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()
    print(f"Streaming incoming emails on {box.address}...")

    async for msg in api.messages.iter_messages(box, poll_interval=2.0, timeout=300.0):
        print(f"Incoming: {msg.subject} from {msg.from_address}")
        detail = await api.messages.get(box, msg.message_api_id)
        print(f"Body: {detail.text}")
        if "STOP" in msg.subject:
            break
```

> **Sync variant:** In `SyncMaily`, `api.messages.iter_messages(box)` is a standard synchronous Python generator (`for msg in api.messages.iter_messages(box): ...`).

### 6. Inspecting Body, HTML & Raw MIME RFC822 Source

```python
async with Maily("http://127.0.0.1:8477") as api:
    # 1. Fetch message detail (plain text & HTML parts)
    detail = await api.messages.get(box, "msg_id_123")
    print(f"Plain text content: {detail.text}")
    print(f"HTML rendering: {detail.html[0] if detail.html else 'No HTML'}")
    print(f"Has attachments: {detail.has_attachments}, Size: {detail.size} bytes")

    # 2. Raw RFC822 MIME source data
    source = await api.messages.source(box, "msg_id_123")
    print(f"MIME Source header excerpt:\n{source.data[:300]}")
    print(f"Download URL: {source.download_url}")

    # 3. Mark read & delete
    await api.messages.mark_read(box, "msg_id_123")
    await api.messages.delete(box, "msg_id_123")
```

---

## ⚠️ Critical Rule: Attribute Access vs. Dictionary Indexing

> [!WARNING]
> In `maily-client`:
> * **Dot/Attribute access** (`res.code`) is supported **ONLY** on Pydantic response models and specifically `ExtractedConfirmation` (which implements Python's `Mapping` protocol).
> * **Standard dictionary responses** (such as `await api.config.get()` or raw JSON mappings) **DO NOT support dot access**. You must access values using bracket notation (`dict["key"]`).

```python
# 1. ExtractedConfirmation supports BOTH syntaxes:
res = await api.wait_for_confirmation_email(box)
if res:
    print(res.confirmation_code)  # ✅ Dot access works
    print(res["confirmation_code"])  # ✅ Bracket access works

# 2. Dictionary responses:
config = await api.config.get()
print(config["client_version"])  # ✅ CORRECT: dictionary bracket indexing
# print(config.client_version)        # ❌ ERROR: AttributeError ('dict' has no attribute 'client_version')
```

---

## ⚡ Flat Facade Shortcuts vs. Resource Namespaces

For maximum convenience during scripting, `Maily` and `SyncMaily` expose **19 root facade methods** that forward directly to their respective resource section:

| # | Facade Root Method Signature | Equivalent Resource Namespace Call | Description |
|---|---|---|---|
| 1 | `api.create_temp_mailbox(*, provider, domain)` | `api.create_temp_mailbox(...)` | Auto-selects domain and creates mailbox in 1 call |
| 2 | `api.create_mailbox(...)` | `api.mailboxes.create(...)` | Creates mailbox with full parameters |
| 3 | `api.list_mailboxes(provider, active)` | `api.mailboxes.list(...)` | Lists registered mailboxes |
| 4 | `api.mailbox(mailbox_id)` | `api.mailboxes.get(...)` | Retrieves mailbox by ID |
| 5 | `api.mailbox_by_address(email)` | `api.mailboxes.by_address(...)` | Finds mailbox by email address string |
| 6 | `api.delete_mailbox(mailbox_id)` | `api.mailboxes.delete(...)` | Purges mailbox and messages |
| 7 | `api.list_messages(mailbox_id, page)` | `api.messages.list(...)` | Lists message headers in mailbox |
| 8 | `api.get_message(mailbox_id, msg_id)` | `api.messages.get(...)` | Retrieves full message detail (text/HTML) |
| 9 | `api.mark_read(mailbox_id, msg_id)` | `api.messages.mark_read(...)` | Marks message as read on upstream provider |
| 10 | `api.delete_message(mailbox_id, msg_id)` | `api.messages.delete(...)` | Permanently deletes a message |
| 11 | `api.get_source(mailbox_id, msg_id)` | `api.messages.source(...)` | Fetches raw RFC822 MIME source data |
| 12 | `api.wait_for_code(box, ...)` | `api.messages.wait_for_code(...)` | 1-line OTP verification code extractor |
| 13 | `api.wait_for_link(box, ...)` | `api.messages.wait_for_link(...)` | 1-line activation URL extractor |
| 14 | `api.wait_for_confirmation_email(...)`| `api.messages.wait_for_confirmation_email(...)`| Dual code & link confirmation extractor |
| 15 | `api.wait_for_message(box, ...)` | `api.messages.wait_for(...)` | Custom predicate message polling |
| 16 | `api.gmail_oauth_start()` | `api.gmail.oauth_start()` | Initiates Google OAuth2 consent URL |
| 17 | `api.gmail_import_account(...)` | `api.gmail.import_account(...)` | Connects Gmail account via refresh token |
| 18 | `api.list_gmail_accounts()` | `api.gmail.accounts()` | Lists connected parent Gmail accounts |
| 19 | `api.delete_gmail_account(parent_id)` | `api.gmail.delete_account(...)` | Disconnects a parent Gmail account |

---

## 📋 Data Models & Response Types Reference

All models are fully typed Pydantic models importable directly from `maily_client`:

| Model Name | Attributes | Description |
|---|---|---|
| `Mailbox` | `.id` (int), `.provider` (str), `.address` (str), `.parent_id` (int \| None), `.is_active` (bool), `.created_at` | Represents a provisioned disposable or parent mailbox |
| `MessageSummary` | `.id` (int), `.message_api_id` (str), `.subject` (str), `.from_address` (str), `.from_name` (str), `.seen` (bool), `.has_attachments` (bool), `.size` (int), `.received_at` | Summary metadata for an incoming email |
| `MessageDetail` | All fields of `MessageSummary` + `.text` (str), `.html` (list[str]) | Full message payload with decoded plain text and HTML bodies |
| `MessageSource` | `.id` (str), `.data` (str), `.download_url` (str) | Raw unmodified RFC822 MIME source text and direct link |
| `Target` | `.id` (str), `.provider` (str), `.kind` ("domain" \| "parent"), `.label` (str) | Available creation target (domain or parent Gmail) |
| `Provider` | `.slug` (str), `.kind` (str), `.capabilities` (`ProviderCapabilities`) | Provider adapter descriptor and supported features |
| `ExtractedConfirmation`| `.message_id`, `.from_address`, `.subject`, `.confirmation_link`, `.confirmation_code` | Dual-access container for extracted activation URLs and OTP codes |
| `SweepResult` | `.mailboxes_deleted` (int), `.messages_deleted` (int) | Result counts from an admin retention sweep |
| `ApiKeyOut` | `.id` (int), `.name` (str), `.prefix` (str), `.scope` (`KeyScopeOut`), `.expires_at` | Metadata for an issued API key |
| `ApiKeyCreatedOut` | All fields of `ApiKeyOut` + `.secret` (str) | Newly generated API key including unmasked plaintext secret |

---

## 🔑 Workflow 4: Scoped API Key Management

The server protects all API actions with scoped API keys. Using a root API key, you can issue restricted tokens for worker processes, test runners, or microservices:

```python
async with Maily("http://127.0.0.1:8477", api_key="root_master_key") as api:
    # 1. Inspect current caller identity
    me = await api.keys.me()
    print(f"Is root: {me.is_root}, Name: {me.name}")

    # 2. Issue a scoped key restricted to mail.tm with read-only access
    new_key = await api.keys.create(
        name="test-worker-alpha",
        scope={
            "providers": ["mail.tm"],
            "parent_ids": [],
            "actions": ["read"],
        },
        expires_in_days=30,
    )
    print(f"Issued Key ID : {new_key.id}")
    print(f"Secret Token  : {new_key.secret}")  # Reveal secret (only shown on create)

    # 3. Rotate key secret
    rotated = await api.keys.rotate(new_key.id)
    print(f"New Secret    : {rotated.secret}")

    # 4. Revoke key
    await api.keys.delete(new_key.id)
```

---

## ⚙️ Workflow 5: Server Admin, Retention & Maintenance

Automate housekeeping and periodic SQLite maintenance directly from client scripts:

```python
async with Maily("http://127.0.0.1:8477", api_key="root_master_key") as api:
    # 1. Configure per-provider TTL retention policies
    await api.admin.retention_set(
        provider="mail.tm",
        mailbox_ttl_hours=24,
        message_ttl_hours=12,
    )

    # 2. Trigger retention sweep
    sweep = await api.admin.retention_run()
    print(f"Deleted: {sweep.mailboxes_deleted} mailboxes, {sweep.messages_deleted} messages")

    # 3. Force immediate thorough database maintenance (VACUUM, REINDEX, ANALYZE)
    await api.admin.retention_run(force_maintenance=True)

    # 4. Refresh background provider domain cache
    cache_run = await api.admin.domain_cache_run()
    print(f"Refreshed provider domains: {cache_run.refreshed}")

    # 5. Fetch operational stats
    stats = await api.admin.stats(days=7)
    print(f"Incoming trend: {stats}")
```

---

## 📬 Workflow 6: Gmail OAuth Multi-Tenant Management

Connect real Gmail parent accounts to aggregate `username+alias@gmail.com` addresses into the same unified API:

```python
async with Maily("http://127.0.0.1:8477", api_key="root_master_key") as api:
    # 1. Initiate OAuth pairing
    oauth = await api.gmail.oauth_start()
    print(f"Open this URL to authorize Gmail account: {oauth.auth_url}")

    # 2. Or import via existing refresh token
    account = await api.gmail.import_account(
        refresh_token="1//0g...",
    )
    print(f"Connected: {account.email} (ID: {account.id})")

    # 3. Trigger immediate upstream sync
    await api.gmail.sync(parent_id=account.id)

    # 4. List registered send-as aliases
    accounts = await api.gmail.accounts()
    for acc in accounts:
        print(f"Gmail Account: {acc.email}, Aliases: {acc.send_as}")
```

---

## 🛡️ Resilient Networking, Retries & Error Handling

### 1. Granular Exception Hierarchy

All API exceptions inherit from `ApiError`, which inherits from `ClientError`:

```
ClientError
 ├── WaitTimeoutError        (Raised on wait_for_code / wait_for_link timeout)
 └── ApiError                (Non-2xx HTTP responses from server)
      ├── AuthenticationError   (HTTP 401: Invalid or missing X-API-Key)
      ├── ForbiddenError        (HTTP 403: Scoped key lacks permission)
      ├── NotFoundError         (HTTP 404: Mailbox or message ID does not exist)
      ├── ValidationError       (HTTP 422 / 400: Malformed parameter or validation error)
      ├── RateLimitError        (HTTP 429: Rate limited by server or provider)
      └── UpstreamProviderError (HTTP 502 / 504: Upstream temp-mail provider outage)
```

Catching specific errors:
```python
from maily_client import Maily, NotFoundError, RateLimitError, AuthenticationError

async with Maily("http://127.0.0.1:8477") as api:
    try:
        msg = await api.messages.get(box, "nonexistent-id")
    except NotFoundError:
        print("Message was already deleted.")
    except RateLimitError as e:
        print(f"Rate limited: {e.detail}")
    except AuthenticationError:
        print("Invalid credentials.")
```

### 2. Automatic Retries & Rate-Limit Backoff

Configure automatic retry policies on connection failures, HTTP 502/504 errors, and HTTP 429:

```python
from maily_client import Maily

# Retries up to 3 times with exponential backoff starting at 0.5s
# Automatically pauses when server returns HTTP 429 Retry-After header
api = Maily(
    base_url="http://127.0.0.1:8477",
    api_key="your_secret_key",
    timeout=45.0,
    max_retries=3,
    retry_backoff=0.5,
)
```

---

## 🧪 Cookbook & Integration Recipes

### Recipe 1: Pytest Async Fixture (Automated Signup)

```python
# conftest.py
import pytest_asyncio
from maily_client import Maily, Mailbox


@pytest_asyncio.fixture
async def temp_mailbox():
    async with Maily("http://127.0.0.1:8477") as api:
        box: Mailbox = await api.create_temp_mailbox()
        try:
            yield api, box
        finally:
            await api.mailboxes.delete(box)


# test_auth.py
import pytest


@pytest.mark.asyncio
async def test_user_registration(temp_mailbox):
    api, box = temp_mailbox

    # 1. Trigger registration on your service
    # await client.post("/auth/register", json={"email": box.address})

    # 2. Wait for 6-digit confirmation code
    code = await api.wait_for_code(box, timeout=45.0)
    assert len(code) == 6
```

### Recipe 2: Pytest Sync Fixture (Standard `pytest`)

```python
# conftest.py
import pytest
from maily_client import SyncMaily


@pytest.fixture
def sync_mailbox():
    with SyncMaily("http://127.0.0.1:8477") as api:
        box = api.create_temp_mailbox()
        try:
            yield api, box
        finally:
            api.delete_mailbox(box)


# test_sync_flow.py
def test_sync_code(sync_mailbox):
    api, box = sync_mailbox
    code = api.wait_for_code(box, timeout=30.0)
    assert code.isdigit()
```

### Recipe 3: Playwright Web Automation (OTP Form Fill)

```python
import asyncio
from maily_client import Maily
from playwright.async_api import async_playwright


async def test_playwright_signup():
    async with Maily("http://127.0.0.1:8477") as mail_api:
        box = await mail_api.create_temp_mailbox()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await page.goto("https://example.com/signup")
            await page.fill('input[name="email"]', box.address)
            await page.fill('input[name="password"]', "SuperSecretPass123!")
            await page.click('button[type="submit"]')

            # Wait for 6-digit OTP code sent to temporary mailbox
            otp = await mail_api.wait_for_code(box, pattern=r"\b(\d{6})\b", timeout=60.0)

            # Fill OTP in registration form
            await page.fill('input[name="otp"]', otp)
            await page.click('button[id="verify"]')

            await page.wait_for_selector(".dashboard-welcome")
            await browser.close()


asyncio.run(test_playwright_signup())
```

### Recipe 4: Selenium WebDriver Activation Link Flow

```python
from maily_client import SyncMaily
from selenium import webdriver
from selenium.webdriver.common.by import By


def test_selenium_activation():
    with SyncMaily("http://127.0.0.1:8477") as mail_api:
        box = mail_api.create_temp_mailbox()

        driver = webdriver.Chrome()
        try:
            driver.get("https://example.com/register")
            driver.find_element(By.NAME, "email").send_keys(box.address)
            driver.find_element(By.ID, "submit").click()

            # Wait for activation URL
            link = mail_api.wait_for_link(box, timeout=60.0)

            # Navigate directly to activation link
            driver.get(link)
            assert "Welcome" in driver.page_source
        finally:
            driver.quit()
            mail_api.delete_mailbox(box)
```

### Recipe 5: FastAPI Lifespan & Dependency Injection

Integrate `Maily` into a FastAPI backend service:

```python
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI
from maily_client import Maily


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Initialize shared client on startup
    app.state.maily = Maily("http://127.0.0.1:8477", api_key="secret_token")
    yield
    # Clean up on shutdown
    await app.state.maily.close()


app = FastAPI(lifespan=lifespan)


def get_maily() -> Maily:
    return app.state.maily


@app.post("/test-email")
async def send_and_wait(mail: Maily = Depends(get_maily)):
    box = await mail.create_temp_mailbox()
    return {"address": box.address}
```

### Recipe 6: Corporate Proxy & Custom HTTP Transport

```python
import httpx
from maily_client import Maily

# Custom httpx client configured with corporate HTTP/SOCKS proxy
custom_http = httpx.AsyncClient(
    proxy="http://corp-proxy.internal:8080",
    verify=False,
)

async with Maily("http://127.0.0.1:8477", client=custom_http) as api:
    box = await api.create_temp_mailbox()
    print(f"Proxied mailbox: {box.address}")
```

---

## 💻 Self-Updating CLI (`maily-client`)

When installed, the package provides a built-in CLI for checking and updating the client:

```bash
# Print current version
maily-client version

# Check GitHub repository for newer version
maily-client check

# Automatically download and install latest client file from GitHub
maily-client update
```

### Programmatic Updates from Python

```python
from maily_client import check_update, self_update

# Check if a newer version is on GitHub
update_info = check_update()
if update_info:
    current_ver, remote_ver = update_info
    print(f"Update available: {current_ver} -> {remote_ver}")
    self_update()
```
