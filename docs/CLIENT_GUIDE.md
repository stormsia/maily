# MailTMAPI Client Developer Guide & Cookbook

A comprehensive guide and cookbook for [`mailtmapi-client`](https://pypi.org/project/mailtmapi-client/) — the standalone, fully-typed Python SDK for the [mailtmapi](https://github.com/stormsia/mailtmapi) disposable multi-provider mail API.

---

## 📑 Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Core Concepts: Async vs Sync](#core-concepts-async-vs-sync)
- [Cookbook & Integration Recipes](#cookbook--integration-recipes)
  - [Recipe 1: Pytest Test Fixture (Automated E2E Signup)](#recipe-1-pytest-test-fixture-automated-e2e-signup)
  - [Recipe 2: Playwright Web Automation (OTP Form Fill)](#recipe-2-playwright-web-automation-otp-form-fill)
  - [Recipe 3: Selenium Email Activation Link Click](#recipe-3-selenium-email-activation-link-click)
  - [Recipe 4: Slow Email Delivery & Polling Tuning](#recipe-4-slow-email-delivery--polling-tuning)
  - [Recipe 5: Resilient Retries & HTTP 429 Rate Limiting](#recipe-5-resilient-retries--http-429-rate-limiting)
  - [Recipe 6: Streaming Inbound Messages](#recipe-6-streaming-inbound-messages)
- [Resource API Reference](#resource-api-reference)
  - [Mailboxes API (`.mailboxes`)](#mailboxes-api-mailboxes)
  - [Messages API (`.messages`)](#messages-api-messages)
  - [Gmail OAuth API (`.gmail`)](#gmail-oauth-api-gmail)
  - [API Key Administration (`.keys`)](#api-key-administration-keys)
  - [Admin & Retention Maintenance (`.admin`)](#admin--retention-maintenance-admin)
  - [Health & System (`.health`)](#health--system-health)
- [Error Handling & 422 Validation Details](#error-handling--422-validation-details)
- [Self-Updating CLI (`mailtmapi-client`)](#self-updating-cli-mailtmapi-client)

---

## Overview

`mailtmapi-client` is engineered specifically for testing suites, automation scripts, and scrapers:
- **Zero Heavy Dependencies**: Powered exclusively by `httpx`, `pydantic`, and `loguru`.
- **PEP 561 Compliant**: Includes `py.typed` marker for static type checking with Mypy and Pyright.
- **Dual Execution Engines**: Async-first with high concurrency (`MailTMAPI`), plus a synchronous facade (`SyncMailTMAPI`).
- **Single-File Option**: The entire client is packaged into a single file `client.py` that can be vendored or downloaded directly.

---

## Installation

### Standard Installation (PyPI)

```bash
pip install mailtmapi-client
```

Or with `uv`:
```bash
uv add mailtmapi-client
```

### Zero-Install Single-File Vendoring

You can copy `client.py` directly into your repository:

```bash
# Linux / macOS
curl -sSL https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py -o client.py

# Windows PowerShell
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/stormsia/mailtmapi/main/client/client.py" -OutFile "client.py"
```

Requires runtime dependencies: `pip install httpx pydantic loguru`.

---

## Core Concepts: Async vs Sync

### Async Engine: `MailTMAPI`

Use `MailTMAPI` with `async with` context manager in FastAPI, Asyncio scripts, or `pytest-asyncio`:

```python
import asyncio
from mailtmapi.client import MailTMAPI


async def run() -> None:
    async with MailTMAPI("http://127.0.0.1:8477", api_key="sk-your-key") as client:
        box = await client.create_temp_mailbox()
        print(f"Created: {box.address}")


asyncio.run(run())
```

### Synchronous Facade: `SyncMailTMAPI`

For synchronous test suites (standard Pytest, unittest, Selenium, or quick procedural scripts), use `SyncMailTMAPI`. It wraps async coroutines seamlessly without requiring manual `asyncio.run()` boilerplate:

```python
from mailtmapi.client import SyncMailTMAPI

with SyncMailTMAPI("http://127.0.0.1:8477", api_key="sk-your-key") as client:
    box = client.create_temp_mailbox()
    print(f"Sync mailbox created: {box.address}")

    # Synchronous wait for OTP code
    code = client.wait_for_code(box, timeout=60.0)
    print(f"Received code: {code}")
```

### ⚠️ Attribute Access vs. Dictionary Key Access

> **CRITICAL RULE:**
> Native attribute/dot access is supported **ONLY on Pydantic models and specifically `ExtractedConfirmation`** (which implements `Mapping` and allows dual access: both `res.confirmation_code` and `res["confirmation_code"]`).
>
> **All other client methods returning standard Python dictionaries** (such as `await api.config.get()` or raw response dicts) **DO NOT support attribute/dot access**. You MUST access dictionary values using standard bracket key indexing (`d["key"]`), NEVER dot syntax (`d.key`).

```python
# 1. ExtractedConfirmation (Pydantic model implementing Mapping) supports BOTH:
res = await api.wait_for_confirmation_email(box, digit_code_mask=r"\b(\d{6})\b")
if res is not None:
    # ✅ Attribute / dot access:
    print(res.subject)
    print(res.confirmation_code)
    print(res.confirmation_link)

    # ✅ Dictionary mapping access:
    print(res["confirmation_code"])
    print(res["confirmation_link"])

# 2. Standard dictionary responses (e.g. api.config.get()):
cfg = await api.config.get()
print(cfg["client_version"])  # ✅ CORRECT: standard dictionary indexing
# print(cfg.client_version)   # ❌ ERROR: AttributeError ('dict' object has no attribute 'client_version')
```

---

## Cookbook & Integration Recipes

### Recipe 1: Pytest Test Fixture (Automated E2E Signup)

Set up a reusable pytest fixture that generates a fresh disposable mailbox per test and tears it down automatically on test completion:

```python
# conftest.py
import pytest
from mailtmapi.client import MailTMAPI, MailboxDetail


@pytest.fixture
async def temp_mailbox():
    async with MailTMAPI("http://127.0.0.1:8477") as client:
        # Create a fresh mailbox
        box: MailboxDetail = await client.create_temp_mailbox()
        try:
            yield client, box
        finally:
            # Clean up after test finishes
            await client.mailboxes.delete(box)


# test_signup.py
import pytest


@pytest.mark.asyncio
async def test_user_registration_flow(temp_mailbox):
    client, box = temp_mailbox

    # 1. Trigger registration on your service
    # await my_app.register(email=box.address)

    # 2. Wait for confirmation code (e.g. 6-digit OTP)
    code = await client.wait_for_code(box, timeout=45.0)
    assert code is not None
    assert len(code) == 6

    # 3. Complete verification on your service
    # res = await my_app.verify_code(email=box.address, code=code)
    # assert res.is_success
```

---

### Recipe 2: Playwright Web Automation (OTP Form Fill)

Automate a complete browser signup flow in Playwright:

```python
import asyncio
from mailtmapi.client import MailTMAPI
from playwright.async_api import async_playwright


async def test_web_signup():
    async with MailTMAPI("http://127.0.0.1:8477") as mail_api:
        # Create disposable inbox
        box = await mail_api.create_temp_mailbox()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to registration page
            await page.goto("https://app.example.com/signup")
            await page.fill('input[name="email"]', box.address)
            await page.fill('input[name="password"]', "SecurePass123!")
            await page.click('button[type="submit"]')

            # Wait for the confirmation code sent by auth.example.com
            code = await mail_api.wait_for_code(
                box,
                pattern=r"\b(\d{6})\b",
                sender_domain="example.com",
                timeout=60.0,
            )

            # Fill OTP in modal and submit
            await page.fill('input[name="otp"]', code)
            await page.click('button[id="verify-otp"]')

            # Assert welcome screen
            await page.wait_for_selector(".dashboard-welcome")
            await browser.close()


asyncio.run(test_web_signup())
```

---

### Recipe 3: Selenium Email Activation Link Click

Automate clicking an email verification link using Selenium WebDriver and the synchronous client `SyncMailTMAPI`:

```python
from mailtmapi.client import SyncMailTMAPI
from selenium import webdriver
from selenium.webdriver.common.by import By


def test_activation_link_flow():
    with SyncMailTMAPI("http://127.0.0.1:8477") as mail_api:
        box = mail_api.create_temp_mailbox()

        driver = webdriver.Chrome()
        try:
            driver.get("https://app.example.com/register")
            driver.find_element(By.NAME, "email").send_keys(box.address)
            driver.find_element(By.ID, "submit-btn").click()

            # Wait for activation URL in incoming email
            link = mail_api.wait_for_link(box, timeout=60.0)
            assert link.startswith("https://app.example.com/activate?")

            # Navigate directly to the activation link
            driver.get(link)
            assert "Account activated successfully" in driver.page_source
        finally:
            driver.quit()
            mail_api.mailboxes.delete(box)
```

---

### Recipe 4: Slow Email Delivery & Polling Tuning

Some external mail services or anti-spam filters experience delays. Fine-tune timeout and check interval to prevent unnecessary rate limiting while ensuring fast resolution:

```python
async with MailTMAPI("http://127.0.0.1:8477") as api:
    box = await api.create_temp_mailbox()

    # Poll every 3 seconds, wait up to 180 seconds
    confirmation = await api.wait_for_confirmation_email(
        box,
        timeout=180.0,
        check_interval=3.0,
        sender_domain="mailer.slow-delivery.org",
    )

    if confirmation:
        print(f"Subject: {confirmation.subject}")
        print(f"OTP: {confirmation.confirmation_code}")
        print(f"Link: {confirmation.confirmation_link}")

        # Backward-compatible dictionary access also supported:
        code = confirmation["confirmation_code"]
```

---

### Recipe 5: Resilient Retries & HTTP 429 Rate Limiting

Configure client-side retries with exponential backoff for unstable network conditions or rate-limited endpoints:

```python
from mailtmapi.client import MailTMAPI

# Automatically retry up to 3 times on HTTP 502/504 or connection timeouts
# Automatically respects HTTP 429 'Retry-After' header
api = MailTMAPI(
    base_url="http://127.0.0.1:8477",
    api_key="your-api-key",
    max_retries=3,
    retry_backoff=0.5,  # initial backoff seconds (doubles each attempt)
)
```

---

### Recipe 6: Streaming Inbound Messages

Continuously listen for incoming messages using an async generator:

```python
async with MailTMAPI("http://127.0.0.1:8477") as api:
    box = await api.mailboxes.create(domain="mail.tm")

    print(f"Listening for emails on {box.address}...")
    async for msg in api.messages.iter_messages(box, poll_interval=2.0, timeout=120.0):
        print(f"[{msg.received_at}] From: {msg.from_address} | {msg.subject}")
        full = await api.messages.get(box, msg.message_api_id)
        print("Text snippet:", full.text[:100] if full.text else "(no text)")
```

---

## Resource API Reference

The client provides clean modular namespaces alongside flat convenience shortcuts on `api`.

### Mailboxes API (`.mailboxes`)

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `api.mailboxes.create` | `provider=None, domain=None, username=None, password=None` | `MailboxDetail` | Creates a new mailbox on requested domain or provider. |
| `api.mailboxes.create_temp` | `provider=None, domain=None` | `MailboxDetail` | Generates a random username and password for a disposable box. |
| `api.mailboxes.list` | *none* | `list[MailboxDetail]` | Lists active mailboxes registered under credentials. |
| `api.mailboxes.get` | `mailbox_id: str` | `MailboxDetail` | Fetches details and credentials for an existing mailbox. |
| `api.mailboxes.delete` | `mailbox: MailboxDetail \| str` | `bool` | Deletes a mailbox and its messages. |

*Shortcuts available on root*: `api.create_temp_mailbox()`, `api.delete_mailbox(box)`.

---

### Messages API (`.messages`)

| Method | Parameters | Returns | Description |
|---|---|---|---|
| `api.messages.list` | `mailbox: Mailbox \| int, page: int = 1` | `list[MessageSummary]` | Fetches message summaries in the mailbox. |
| `api.messages.get` | `mailbox, message_id: str` | `MessageDetail` | Retrieves full message body, HTML, attachments, and text. |
| `api.messages.source` | `mailbox, message_id: str` | `MessageSource` | Fetches raw RFC822 MIME source data and download URL. |
| `api.messages.mark_read` | `mailbox, message_id: str` | `MessageSummary` | Marks message as read on upstream provider. |
| `api.messages.delete` | `mailbox, message_id: str` | `None` | Deletes message permanently. |
| `api.messages.wait_for` | `mailbox, timeout=120.0, interval=2.0, predicate=None` | `MessageSummary` | Polls until a message matching optional predicate arrives. |
| `api.messages.wait_for_confirmation_email`| `mailbox, sender_domain=None, url_contain=None, digit_code_mask=None, timeout=60.0, check_interval=5.0` | `ExtractedConfirmation \| None` | Extracts code and link into a typed mapping object. |
| `api.messages.wait_for_code` | `mailbox, pattern=r"\b(\d{4,8})\b", sender_domain=None, timeout=60.0, check_interval=3.0` | `str` | Extracts verification code (raises `WaitTimeoutError` on timeout). |
| `api.messages.wait_for_link` | `mailbox, url_contain=None, sender_domain=None, timeout=60.0, check_interval=3.0` | `str` | Extracts confirmation link (raises `WaitTimeoutError` on timeout). |
| `api.messages.iter_messages` | `mailbox, poll_interval=2.0, timeout=120.0` | `AsyncIterator[MessageSummary]` | Yields messages in real-time as they arrive. |

*Shortcuts available on root*: `api.list_messages()`, `api.get_message()`, `api.mark_read()`, `api.delete_message()`, `api.get_source()`, `api.wait_for_code()`, `api.wait_for_link()`, `api.wait_for_confirmation_email()`.

---

### Gmail OAuth API (`.gmail`)

Manage private Gmail accounts connected via OAuth2:

```python
# Start OAuth flow (returns OAuthStart with auth_url and state)
oauth = await api.gmail.oauth_start()
print(f"Authorize at: {oauth.auth_url}")

# List connected Gmail accounts
accounts = await api.gmail.accounts()

# Trigger immediate background IMAP/REST sync
await api.gmail.sync(parent_id=7)

# Remove connected account
await api.gmail.delete_account(parent_id=7)
```

---

### API Key Administration (`.keys`)

Manage scoped API keys (requires Root API Key):

```python
# Create restricted key for automation worker
key = await api.keys.create(
    name="playwright-runner",
    scope={
        "providers": ["mail.tm", "tempmail.plus"],
        "parent_ids": [],
        "actions": ["read", "write"],
    },
)
print(f"Issued Key Secret: {key.secret}")

# List all keys
all_keys = await api.keys.list()

# Revoke key
await api.keys.delete(key.id)
```

---

### Admin & Retention Maintenance (`.admin`)

Trigger retention sweeps and database maintenance:

```python
# Execute retention purge and opportunistic DB optimization
res = await api.admin.retention_run()
print(f"Purged {res.mailboxes_deleted} boxes, {res.messages_deleted} messages")

# Force immediate full database maintenance (VACUUM, REINDEX, ANALYZE)
res = await api.admin.retention_run(force_maintenance=True)

# Inspect & refresh provider domain cache
settings = await api.admin.domain_cache_settings()
await api.admin.refresh_domain_cache()
```

---

### Health & System (`.health`)

```python
# Quick healthcheck
status = await api.health.ping()
assert status.status == "healthy"

# Check server and client version alignment
await api.check_client_version()
```

---

## Error Handling & 422 Validation Details

`mailtmapi-client` raises strongly-typed exceptions rooted in `ClientError`:

```
ClientError
└── ApiError
    ├── AuthenticationError    (HTTP 401: Invalid API key or missing header)
    ├── ForbiddenError         (HTTP 403: Scope denied or unauthorized action)
    ├── NotFoundError          (HTTP 404: Mailbox or message does not exist)
    ├── ValidationError        (HTTP 422 / 400: Malformed input or schema failure)
    ├── RateLimitError         (HTTP 429: Too many requests)
    └── UpstreamProviderError  (HTTP 502 / 504: Upstream provider failure)
└── WaitTimeoutError           (Timeout exceeded while polling for message/code)
```

### Enhanced 422 Validation Error Messages

FastAPI field errors are automatically formatted into readable messages:

```python
from mailtmapi.client import MailTMAPI, ValidationError

async with MailTMAPI("http://127.0.0.1:8477") as api:
    try:
        await api.mailboxes.create(domain="invalid domain!@#")
    except ValidationError as exc:
        # Instead of raw unformatted JSON:
        # exc.detail -> "body -> domain: Value error, invalid domain name characters"
        print(f"Validation failed: {exc}")
```

---

## Self-Updating CLI (`mailtmapi-client`)

When installed as a package, `mailtmapi-client` provides a command-line interface:

```bash
# Print current client version
mailtmapi-client version

# Check if a newer version is available in git
mailtmapi-client check

# Automatically download and update standalone client.py
mailtmapi-client update
```
