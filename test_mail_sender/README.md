# test_mail_sender

**Autonomous, asynchronous test email dispatcher designed for CI pipelines, autotests, and integration suites.**

This module is completely decoupled from the main project codebase. It has zero dependencies on internal project models, databases, or configuration, and only requires standard `httpx`. It can be easily ported and used in any external test suite or CI environment.

---

## 🎯 Provider Architecture

### 1. Primary: `WeSendTestMail` (`https://www.wesendtestmail.com`)
* **Endpoint**: `POST https://www.wesendtestmail.com/send-mail`
* **Token & Session Handling**:
  * The service is built on Laravel and protected with CSRF tokens and session cookies (`wesendtestmail_session`, `XSRF-TOKEN`).
  * On the first request, the client automatically sends a lightweight GET request to `https://www.wesendtestmail.com/`, parses the CSRF token from `<meta name="csrf-token" content="...">` (or `<input name="_token" value="...">`), stores session cookies in the HTTP client cookie jar, and caches the token.
  * When sending emails, it sends `X-CSRF-TOKEN: <token>`, `Accept: application/json`, `X-Requested-With: XMLHttpRequest`, and a `multipart/form-data` payload (`_token`, `email`).
  * **Reliability & Token Rotation**: If the service responds with `HTTP 419` (CSRF token mismatch / Page Expired), the client invalidates the cached token, performs a fresh GET to refresh cookies and CSRF token, and transparently retries the send request. Concurrent requests are synchronized via an `asyncio.Lock` to avoid token stampedes.

### 2. Fallback: `XeraMail` (`https://xeramail.com`)
* **Endpoint**: `POST https://xeramail.com/api/send-test-email`
* **Token & Header Handling**:
  * Accepts a direct JSON payload: `{"to": "<email>"}` alongside browser-like headers (`User-Agent`, `Referer`, `Origin`).
  * No CSRF tokens are required for the API endpoint.
  * Includes built-in support for an optional `cf_clearance` cookie token (configured via constructor argument or `XERAMAIL_CF_CLEARANCE` environment variable) in case Cloudflare Bot Protection is triggered in strict CI IP ranges.

---

## 🚀 Python Usage

### One-liner Quick Send
```python
import asyncio
from test_mail_sender import send_test_email


async def main():
    result = await send_test_email("my_inbox@mailto.plus")
    print(f"Provider used: {result.provider}")
    print(f"Success: {result.success}, latency: {result.duration_ms:.1f}ms")
    if result.fallback_used:
        print("Note: Primary service failed; delivered via fallback!")


asyncio.run(main())
```

### Context Manager (Recommended for Test Suites)
```python
import asyncio
from test_mail_sender import TestEmailSender


async def run_tests():
    async with TestEmailSender(timeout=15.0) as sender:
        # Default Auto mode: primary first -> transparent fallback if primary fails
        res1 = await sender.send("test_inbox_1@mailto.plus")

        # Explicit fallback or primary mode
        res2 = await sender.send("test_inbox_2@mailto.plus", mode="fallback")

        # Concurrent batch sending
        results = await sender.send_all(
            [
                "box1@mailto.plus",
                "box2@mailto.plus",
                "box3@mailto.plus",
            ],
            concurrency=3,
        )


asyncio.run(run_tests())
```

---

## 💻 CLI Usage (for CI & Shell Scripts)

The module can be executed directly as a command-line tool:

### Send Test Email
```bash
# Standard mode (human-readable status and latency)
python -m test_mail_sender send my_box@mailto.plus

# Shorthand:
python -m test_mail_sender my_box@mailto.plus

# JSON output for CI parsing with jq or shell pipelines:
python -m test_mail_sender my_box@mailto.plus --json

# Explicitly select provider:
python -m test_mail_sender my_box@mailto.plus --mode fallback
python -m test_mail_sender my_box@mailto.plus --mode primary
```

### Health Check / Probe
Probes both primary and fallback services sequentially and reports status and latency:
```bash
python -m test_mail_sender probe my_box@mailto.plus
```
Example output:
```text
Probing both test email providers with target: my_box@mailto.plus...

[1/2] Probing Primary (WeSendTestMail)...
  OK: Test email sent successfully to my_box@mailto.plus (1972.9ms)

[2/2] Probing Fallback (XeraMail)...
  OK: Test email sent via xeramail (messageId: <...>) (218.4ms)

Probe Summary:
  Primary (wesendtestmail.com): OPERATIONAL
  Fallback (xeramail.com):      OPERATIONAL
```

---

## 📊 Result Model (`EmailSendResult`)

The `EmailSendResult` object provides full delivery diagnostics:
- `email`: target recipient address.
- `success`: boolean status flag.
- `provider`: name of the provider that succeeded (`"wesendtestmail"` or `"xeramail"`).
- `fallback_used`: boolean indicating whether failover was triggered.
- `message_id`: message ID if returned by the provider.
- `detail`: descriptive status message.
- `duration_ms`: total elapsed duration in milliseconds.
- `attempts`: list of all provider attempts with status codes, error details, and latencies (`AttemptInfo`).
