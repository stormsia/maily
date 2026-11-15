---
name: maily-testing
description: Use Maily to spin up temporary email inboxes, receive incoming verification emails, and extract OTP codes in Playwright/Pytest browser tests.
metadata:
  version: 0.9.1
  author: stormsia
---

# Maily E2E Email Verification Skill

## 1. Quickstart Architecture

### Start Maily Gateway (Self-Hosted Docker):
```bash
docker run -d   --name maily-gateway   -p 8477:8477   -e MAILY_API_KEY=testkey   ghcr.io/stormsia/maily:latest
```

Verify gateway health:
```bash
curl -f http://127.0.0.1:8477/health || exit 1
```

### Install Client SDK:
```bash
pip install maily-client pytest-asyncio
```

## 2. Standard Playwright OTP Recipe

```python
import asyncio
from maily import Maily
from playwright.async_api import async_playwright


async def test_user_registration_flow():
    # Pass api_key matching MAILY_API_KEY to prevent HTTP 401 Unauthorized
    async with Maily("http://127.0.0.1:8477", api_key="testkey") as api:
        # 1. Create hermetic disposable inbox (< 100 ms)
        box = await api.create_temp_mailbox(provider="mail.tm")
        print(f"Created temporary mailbox: {box.address}")

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()

            # 2. Trigger signup flow on target application
            await page.goto("https://example.com/signup")
            await page.fill('input[name="email"]', box.address)
            await page.click('button[type="submit"]')

            # 3. High-level polling: extracts 4-8 digit OTP code automatically
            code = await api.wait_for_code(box, timeout=30.0)
            assert code is not None, "Failed to receive verification code"
            print(f"Extracted verification code: {code}")

            # 4. Fill OTP in registration form
            await page.fill('input[name="verification_code"]', code)
            await page.click("button#verify-submit")
            await page.wait_for_selector(".dashboard-welcome")

            await browser.close()
```

## 3. Best Practices
- Always supply `api_key="testkey"` matching `MAILY_API_KEY` to avoid HTTP 401 Unauthorized.
- Use `await api.wait_for_code(box)` for 1-line sub-second OTP extraction without regex boilerplate.
- For anti-bot protected sites, rotate providers via `api.create_temp_mailbox(provider="tempmailplus")`.
