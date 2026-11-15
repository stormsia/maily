import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, CheckCircle2, Terminal, Code2, Zap, Shield, Sparkles, AlertTriangle } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsPython: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Overview */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Python SDK · maily-client</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display mb-4" id="python-overview">
          Official Python Client SDK
        </h2>
        <p className="text-base leading-relaxed text-slate-300">
          The official Python SDK is published to PyPI as <code className="text-cyan-400 font-mono">maily-client</code>. It is engineered specifically for testing suites, automation scripts, and microservices with zero heavy server dependencies.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4">
          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-300">
            <span className="font-semibold text-cyan-400 block mb-0.5">Dual Engines</span>
            Async-first <code className="font-mono text-slate-200">Maily</code> and sync <code className="font-mono text-slate-200">SyncMaily</code>.
          </div>
          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-300">
            <span className="font-semibold text-emerald-400 block mb-0.5">PEP 561 Typed</span>
            Strict Pydantic v2 models for complete IDE autocomplete.
          </div>
          <div className="p-3 rounded-lg border border-slate-800 bg-slate-900/40 text-xs text-slate-300">
            <span className="font-semibold text-indigo-400 block mb-0.5">Magic Extraction</span>
            Native 1-line OTP code and magic link extractors.
          </div>
        </div>
      </section>

      {/* Gateway Server Prerequisite */}
      <Callout type="warning" title="Maily Gateway Server Required">
        <p className="text-xs leading-relaxed text-amber-200/90">
          The <code className="text-cyan-300 font-mono">maily-client</code> library is an HTTP client communicating with your self-hosted <strong>Maily Gateway Server</strong> at <code className="text-cyan-300 font-mono">http://127.0.0.1:8477</code>. <strong>The client cannot work without a running server instance.</strong> Launch the server container first (<code className="text-slate-200 font-mono">docker run -d -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest</code>).
        </p>
      </Callout>

      {/* Installation */}
      <section>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <h3 className="text-xl font-bold text-white font-display" id="installation">
            Installation
          </h3>
          <a
            href="https://github.com/stormsia/maily#standalone-python-client-sdk-maily-client"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Python SDK in GitHub README ↗</span>
          </a>
        </div>
        <CodeBlock
          language="bash"
          code={`# Modern uv package manager (recommended)
uv add maily-client

# Standard pip installation
pip install maily-client

# Direct single-file vendoring (no external install needed)
curl -O https://raw.githubusercontent.com/stormsia/maily/main/client/maily_client.py`}
        />
      </section>

      {/* Async Quickstart */}
      <section>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
          <h3 className="text-xl font-bold text-white font-display" id="async-quickstart">
            Asynchronous Engine (<code className="font-mono text-cyan-400">Maily</code>)
          </h3>
          <a
            href="https://github.com/stormsia/maily#1-line-mailbox--verification-code-extraction"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>OTP Extraction in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-sm text-slate-400 mb-3">
          Recommended for high-concurrency test suites and modern async frameworks (Playwright, FastAPI, Aiohttp):
        </p>
        <CodeBlock
          language="python"
          filename="async_quickstart.py"
          code={`import asyncio
from maily_client import Maily, WaitTimeoutError

async def main():
    # Pass api_key matching MAILY_API_KEY if auth is enabled
    async with Maily("http://127.0.0.1:8477", api_key="secret_token") as api:
        # 1. Discover available targets and providers
        targets = await api.list_targets()
        print(f"Available provider domains: {[t.name for t in targets]}")

        # 2. Provision an isolated disposable inbox (< 100 ms)
        mailbox = await api.create_temp_mailbox(provider="mail.tm")
        print(f"Provisioned inbox address: {mailbox.address}")

        # 3. Trigger your application's signup or OTP verification email here...

        # 4. Extract 6-digit OTP code in 1 line with automatic polling & regex
        try:
            otp_code = await api.wait_for_code(mailbox, pattern=r"\\b(\\d{6})\\b", timeout=30.0)
            print(f"Extracted verification PIN: {otp_code}")
        except WaitTimeoutError:
            print("Timed out waiting for verification email.")

        # 5. Clean up mailbox when finished
        await api.delete_mailbox(mailbox)

asyncio.run(main())`}
        />
      </section>

      {/* Synchronous Engine */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="sync-quickstart">
          Synchronous Engine (<code className="font-mono text-cyan-400">SyncMaily</code>)
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Drop-in transparent wrapper for blocking test runners, standard scripts, and legacy Pytest fixtures without asyncio:
        </p>
        <CodeBlock
          language="python"
          filename="sync_quickstart.py"
          code={`from maily_client import SyncMaily

with SyncMaily("http://127.0.0.1:8477") as client:
    # Synchronously provision disposable inbox
    box = client.create_temp_mailbox(provider="tempmailplus")
    print(f"Sync mailbox created: {box.address}")

    # Synchronously wait for confirmation link
    confirm_url = client.wait_for_link(box, timeout=25.0)
    print(f"Account activation URL: {confirm_url}")`}
        />
      </section>

      {/* Magic Link & OTP Extraction */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="magic-extractors">
          Magic Extractors: OTP Codes & Activation Links
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Maily eliminates custom parsing logic by providing built-in extractors that inspect both HTML and plaintext bodies:
        </p>
        <CodeBlock
          language="python"
          filename="magic_extraction.py"
          code={`# Extract standard 6-digit numeric OTP code
code = await api.wait_for_code(mailbox, pattern=r"\\b(\\d{6})\\b", timeout=30.0)

# Extract alphanumeric 8-character verification token
token = await api.wait_for_code(mailbox, pattern=r"\\b([A-Z0-9]{8})\\b", timeout=30.0)

# Extract password reset activation link
reset_link = await api.wait_for_link(
    mailbox,
    pattern=r"https?://[^\\s>]+auth/reset-password[^\\s>]*",
    timeout=30.0
)`}
        />
      </section>

      {/* Real-time SSE Streaming */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="sse-streaming">
          Real-Time Server-Sent Events (SSE) Streaming
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Instead of polling HTTP endpoints, stream incoming messages over a persistent Server-Sent Events connection with sub-second latency:
        </p>
        <CodeBlock
          language="python"
          filename="sse_streaming.py"
          code={`async with Maily("http://127.0.0.1:8477") as client:
    box = await client.create_temp_mailbox()

    # Stream incoming emails as they arrive upstream
    async for message in client.stream_messages(box, timeout=45.0):
        print(f"New incoming email from: {message.from_address}")
        print(f"Subject: {message.subject}")
        if "Security Code" in message.subject:
            break`}
        />
      </section>

      {/* Pytest Fixtures */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="pytest-fixtures">
          Production Pytest Async Fixtures
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          Include this fixture in your <code className="text-cyan-400 font-mono">conftest.py</code> to provide clean, isolated mailboxes with automated teardown:
        </p>
        <CodeBlock
          language="python"
          filename="conftest.py"
          code={`import pytest
import pytest_asyncio
from maily_client import Maily

@pytest_asyncio.fixture
async def temp_email():
    '''Yield an isolated temporary mailbox and auto-delete it after test completion.'''
    async with Maily("http://127.0.0.1:8477") as api:
        box = await api.create_temp_mailbox()
        try:
            yield box, api
        finally:
            await api.delete_mailbox(box)

@pytest.mark.asyncio
async def test_email_verification_flow(temp_email):
    box, api = temp_email
    # Trigger email dispatch to box.address...
    otp = await api.wait_for_code(box, timeout=20.0)
    assert len(otp) == 6`}
        />
      </section>

      {/* Data Models & Error Hierarchy */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="models-and-errors">
          Pydantic v2 Models & Error Hierarchy
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-white text-sm mb-2 flex items-center gap-2">
              <Code2 className="w-4 h-4 text-cyan-400" />
              Pydantic Data Models
            </h4>
            <ul className="text-xs text-slate-400 space-y-1.5 font-mono">
              <li><strong className="text-slate-200">Mailbox</strong>: id, address, provider, token, created_at</li>
              <li><strong className="text-slate-200">Message</strong>: id, mailbox_id, from_address, subject, intro, text, html, created_at</li>
              <li><strong className="text-slate-200">Attachment</strong>: id, filename, content_type, size, download_url</li>
              <li><strong className="text-slate-200">TargetInfo</strong>: name, kind, domains, capabilities</li>
            </ul>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-white text-sm mb-2 flex items-center gap-2">
              <Shield className="w-4 h-4 text-emerald-400" />
              Exception Hierarchy
            </h4>
            <ul className="text-xs text-slate-400 space-y-1.5 font-mono">
              <li><strong className="text-slate-200">MailyError</strong>: Base exception for all SDK errors</li>
              <li><strong className="text-slate-200">WaitTimeoutError</strong>: Raised when timeout expires during polling</li>
              <li><strong className="text-slate-200">UpstreamProviderError</strong>: Upstream disposable service failure</li>
              <li><strong className="text-slate-200">AuthenticationError</strong>: Invalid or revoked X-API-Key</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link
          to="/docs"
          className="text-slate-400 hover:text-white"
        >
          ← Getting Started
        </Link>
        <Link
          to="/docs/curl"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>cURL & REST API Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
