import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, Terminal, CheckCircle2, ShieldCheck, Zap, Sparkles } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsRecipes: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Cookbook · Production Recipes</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="recipes-overview">
            Automated Testing Recipes (Playwright, Pytest & Cypress)
          </h2>
          <a
            href="https://github.com/stormsia/maily#e2e-test-automation-recipes-pytest-playwright-selenium"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Test Recipes in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          Maily eliminates flaky E2E signup tests by providing native 1-line verification code extraction via <code className="text-cyan-400 font-mono">await api.wait_for_code(box)</code>. Instead of maintaining fragile regexes or polling third-party mailboxes, test runners receive OTP codes and magic activation links with sub-second upstream detection.
        </p>
      </section>

      {/* Test Environment Callout */}
      <Callout type="note" title="Test Environment Architecture">
        <p className="text-xs leading-relaxed text-cyan-200/90">
          All test recipes require the <strong>Maily Gateway Server</strong> running locally or as a CI service container (<code className="font-mono text-white">ghcr.io/stormsia/maily:latest</code>) on <code className="font-mono text-white">http://127.0.0.1:8477</code>. Without the running server, test runners cannot provision mailboxes.
        </p>
      </Callout>

      {/* Recipe 1: Playwright Python */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-playwright-python">
          Recipe 1 — Playwright E2E User Signup & Email OTP (Python)
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Complete browser flow: generates an ephemeral inbox, completes registration form, extracts 6-digit OTP code, and verifies account activation:
        </p>
        <CodeBlock
          language="python"
          filename="test_signup_playwright.py"
          code={`import pytest
from playwright.async_api import async_playwright
from maily_client import Maily

@pytest.mark.asyncio
async def test_user_signup_and_email_verification():
    async with Maily("http://127.0.0.1:8477", api_key="test_key") as api, async_playwright() as p:
        # 1. Create an isolated ephemeral mailbox (< 100 ms)
        mailbox = await api.create_temp_mailbox(provider="mail.tm")
        print(f"Generated test address: {mailbox.address}")

        # 2. Open browser, fill registration form
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://app.example.com/signup")
        await page.fill('input[name="email"]', mailbox.address)
        await page.fill('input[name="password"]', "SecureP@ssw0rd123!")
        await page.click('button[type="submit"]')

        # 3. Wait for inbound verification email and extract 6-digit OTP in 1 line
        otp_code = await api.wait_for_code(mailbox, pattern=r"\\b(\\d{6})\\b", timeout=30.0)
        assert otp_code is not None, "Failed to extract OTP from email body"
        print(f"Received verification OTP: {otp_code}")

        # 4. Fill OTP and confirm verification success
        await page.fill('input[name="otp"]', otp_code)
        await page.click('button[id="verify-btn"]')
        await page.wait_for_selector(".dashboard-welcome")
        await browser.close()`}
        />
      </section>

      {/* Recipe 2: Pytest Fixture */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-pytest-fixture">
          Recipe 2 — Hermetic Pytest Async Fixture with Auto-Cleanup
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Manage mailbox lifecycle cleanly with automatic fixture teardown:
        </p>
        <CodeBlock
          language="python"
          filename="conftest.py"
          code={`import pytest_asyncio
import pytest
from maily_client import Maily

@pytest_asyncio.fixture
async def temp_email():
    """Yield a disposable mailbox and automatically delete it after test completion."""
    async with Maily("http://127.0.0.1:8477") as client:
        box = await client.create_temp_mailbox()
        try:
            yield box, client
        finally:
            await client.delete_mailbox(box)

@pytest.mark.asyncio
async def test_password_reset_flow(temp_email):
    box, client = temp_email
    # Trigger password reset in test application...
    reset_link = await client.wait_for_link(box, timeout=25.0)
    assert "reset-token" in reset_link`}
        />
      </section>

      {/* Recipe 3: TypeScript / Node.js Playwright */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-playwright-ts">
          Recipe 3 — Playwright Test (TypeScript / Node.js)
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Interact directly with the Maily REST API in Node.js / TypeScript test suites:
        </p>
        <CodeBlock
          language="typescript"
          filename="tests/signup.spec.ts"
          code={`import { test, expect } from '@playwright/test';

const MAILY_BASE = 'http://127.0.0.1:8477';

test('User registration with OTP verification', async ({ page }) => {
  // 1. Create mailbox via REST
  const boxRes = await fetch(\`\${MAILY_BASE}/v1/mailboxes\`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider: 'mail.tm' }),
  });
  const mailbox = await boxRes.json();

  // 2. Perform UI signup
  await page.goto('https://app.example.com/signup');
  await page.fill('#email', mailbox.address);
  await page.click('#submit');

  // 3. Poll for messages and extract OTP regex
  let otpCode: string | null = null;
  for (let attempt = 0; attempt < 15; attempt++) {
    await page.waitForTimeout(2000);
    const msgRes = await fetch(\`\${MAILY_BASE}/v1/mailboxes/\${mailbox.id}/messages\`);
    const messages = await msgRes.json();
    if (messages.length > 0) {
      const match = messages[0].intro.match(/\\b(\\d{6})\\b/);
      if (match) {
        otpCode = match[1];
        break;
      }
    }
  }

  expect(otpCode).not.toBeNull();
  await page.fill('#otp', otpCode!);
  await page.click('#verify-btn');
});`}
        />
      </section>

      {/* Recipe 4: Multi-Provider Failover & Domain Rotation */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-failover">
          Recipe 4 — Multi-Provider Failover & Domain Rotation
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Fallback across multiple provider networks if a domain is rejected by target form validation:
        </p>
        <CodeBlock
          language="python"
          filename="resilient_signup.py"
          code={`import pytest
from maily_client import Maily, UpstreamProviderError

@pytest.mark.asyncio
async def test_resilient_mailbox_creation():
    providers = ["tempmail.plus", "mail.tm", "temp-mail.io", "anonymmail.net"]
    async with Maily("http://127.0.0.1:8477") as client:
        box = None
        for prov in providers:
            try:
                box = await client.create_temp_mailbox(provider=prov)
                break
            except UpstreamProviderError:
                continue
        assert box is not None, "All providers temporarily unavailable"`}
        />
      </section>

      {/* Recipe 5: SSE Live Streaming */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-sse">
          Recipe 5 — Server-Sent Events (SSE) Live Email Streaming
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Receive incoming messages with zero polling delay using asynchronous generators:
        </p>
        <CodeBlock
          language="python"
          filename="sse_stream.py"
          code={`import pytest
from maily_client import Maily

@pytest.mark.asyncio
async def test_live_streaming_messages():
    async with Maily("http://127.0.0.1:8477") as client:
        box = await client.create_temp_mailbox()
        async for message in client.stream_messages(box, timeout=30.0):
            if "Welcome" in message.subject:
                print(f"Received welcome email from {message.from_address}")
                break`}
        />
      </section>

      {/* Recipe 6: Spam Trap & Blackhole Verification */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="recipe-spam-trap">
          Recipe 6 — Spam Trap & Outbound Blackhole Verification
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Verify that test systems do not leak outbound emails to unauthorized external recipients:
        </p>
        <CodeBlock
          language="python"
          filename="test_spam_trap.py"
          code={`import pytest
from maily_client import Maily

@pytest.mark.asyncio
async def test_zero_leakage_verification():
    """Ensure that internal notifications only hit authorized test domains."""
    async with Maily("http://127.0.0.1:8477") as client:
        box = await client.create_temp_mailbox()
        # Trigger internal workflow...
        messages = await client.get_messages(box)
        for msg in messages:
            # Confirm no unexpected CC/BCC headers leaked
            assert "external-recipient.com" not in msg.intro`}
        />
      </section>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/adding-providers" className="text-slate-400 hover:text-white">
          ← Adding Providers
        </Link>
        <Link
          to="/docs/architecture"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Architecture & Resilience</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
