import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link, useRouter } from '../../context/RouterContext';
import { ArrowRight, Terminal, Server, Shield, Zap, Layers, CheckCircle2, ExternalLink, AlertTriangle } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsGettingStarted: React.FC = () => {
  const { assetUrl } = useRouter();
  return (
    <div className="space-y-10">
      {/* Introduction */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/60 text-cyan-700 dark:text-cyan-300 text-xs font-mono mb-4">
          <span>Overview & Getting Started</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white font-display mb-4" id="what-is-maily">
          Universal Temporary Email Gateway
        </h2>
        <p className="text-base leading-relaxed text-slate-700 dark:text-slate-300">
          <strong>Maily</strong> is an open-source, high-performance disposable email gateway designed specifically for automated testing (Playwright, Cypress, Selenium, Pytest), CI/CD verification pipelines, and AI agent workflows.
        </p>
        <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400 mt-3">
          Single-provider libraries break whenever that specific service encounters upstream downtime, alters its API response schema, or gets blocked by spam blacklists. Maily unifies <strong>8+ disposable email providers</strong> and <strong>40+ rotating domains</strong> under a single normalized OpenAPI 3.1 REST API and asynchronous Python SDK.
        </p>
      </section>

      {/* Concrete Metrics */}
      <section>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white font-display mb-4" id="performance-metrics">
          Key Performance & Reliability Benchmarks
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 shadow-sm">
            <div className="text-2xl font-bold font-mono text-cyan-600 dark:text-cyan-400">&lt; 2.5 ms</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">SQLite WAL Latency</div>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 shadow-sm">
            <div className="text-2xl font-bold font-mono text-emerald-600 dark:text-emerald-400">8+</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Unified Providers</div>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 shadow-sm">
            <div className="text-2xl font-bold font-mono text-indigo-600 dark:text-indigo-400">40+</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">Rotating Domains</div>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/50 shadow-sm">
            <div className="text-2xl font-bold font-mono text-fuchsia-600 dark:text-fuchsia-400">&lt; 1.0 s</div>
            <div className="text-xs text-slate-500 dark:text-slate-400 mt-1">OTP Extraction Delay</div>
          </div>
        </div>
      </section>

      {/* Gateway Server Prerequisite */}
      <Callout type="warning" title="Maily Gateway Server Required">
        <p className="text-xs leading-relaxed text-amber-800 dark:text-amber-200/90">
          Maily uses a client-server architecture. The Python SDK (<code className="text-cyan-600 dark:text-cyan-300 font-mono">maily-client</code>) and cURL scripts communicate with your self-hosted <strong>Maily Gateway Server</strong> at <code className="text-cyan-600 dark:text-cyan-300 font-mono">http://127.0.0.1:8477</code>. <strong>The client cannot work without a running server instance.</strong> Launch the server container first before running client scripts.
        </p>
      </Callout>

      {/* 60-Second Quickstart */}
      <section>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 className="text-xl font-bold text-slate-900 dark:text-white font-display" id="quickstart">
            Quickstart in 60 Seconds
          </h3>
          <a
            href="https://github.com/stormsia/maily#quickstart--getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white text-xs font-semibold border border-slate-300 dark:border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Quickstart in GitHub README ↗</span>
          </a>
        </div>

        <div className="space-y-6">
          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 font-mono text-xs">
                  1
                </span>
                <span>Launch Maily Gateway Server with Docker</span>
              </div>
              <a
                href="https://github.com/stormsia/maily#option-a--docker-pre-built-image-no-git-clone-required"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] font-mono text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 inline-flex items-center gap-1"
              >
                <span>README Docker Guide ↗</span>
              </a>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Run the official hardened, unprivileged container with embedded SQLite WAL storage and API key authentication:
            </p>
            <CodeBlock
              language="bash"
              code="docker run -d --name maily -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest"
            />
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 font-mono text-xs">
                  2
                </span>
                <span>Install Official Python SDK</span>
              </div>
              <a
                href="https://github.com/stormsia/maily#installation"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] font-mono text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 inline-flex items-center gap-1"
              >
                <span>README Install Guide ↗</span>
              </a>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Zero heavy dependencies. Compatible with Python 3.10+:
            </p>
            <CodeBlock
              language="bash"
              code={`# Using uv (recommended)
uv add maily-client

# Or using pip
pip install maily-client`}
            />
          </div>

          <div className="p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-cyan-600 dark:text-cyan-400 font-mono text-xs">
                  3
                </span>
                <span>Generate Mailbox & Extract OTP in 4 Lines</span>
              </div>
              <a
                href="https://github.com/stormsia/maily#1-line-mailbox--verification-code-extraction"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[11px] font-mono text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 inline-flex items-center gap-1"
              >
                <span>README OTP Code ↗</span>
              </a>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">
              Create an isolated inbox and wait for verification codes without flaky loops:
            </p>
            <CodeBlock
              language="python"
              filename="quickstart.py"
              code={`import asyncio
from maily_client import Maily

async def main():
    async with Maily("http://127.0.0.1:8477", api_key="your_secret_api_key") as api:
        # Create an ephemeral mailbox (< 100 ms)
        box = await api.create_temp_mailbox(provider="mail.tm")
        print(f"Generated test email: {box.address}")

        # Wait for verification email and extract 6-digit OTP code in 1 line
        otp_code = await api.wait_for_code(box, pattern=r"\\b(\\d{6})\\b", timeout=30.0)
        print(f"Extracted OTP code: {otp_code}")

asyncio.run(main())`}
            />
          </div>
        </div>
      </section>

      {/* Feature Highlights Grid */}
      <section>
        <h3 className="text-xl font-bold text-slate-900 dark:text-white font-display mb-4" id="core-features">
          Engineered for Production Resiliency
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
            <h4 className="font-semibold text-cyan-600 dark:text-cyan-400 text-sm mb-1 flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Sub-Millisecond Queries
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              State stored in embedded SQLite configured with Write-Ahead Logging (WAL) and automatic compaction. Benchmarks at &lt; 2.5 ms latency under concurrent read/write loads.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
            <h4 className="font-semibold text-emerald-600 dark:text-emerald-400 text-sm mb-1 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              Cryptographic Encryption at Rest
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Sensitive provider credentials, Gmail OAuth refresh tokens, and raw message payloads are encrypted at rest using Fernet AES-128-CBC + HMAC-SHA256 with 256-bit keys.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
            <h4 className="font-semibold text-indigo-600 dark:text-indigo-400 text-sm mb-1 flex items-center gap-2">
              <Server className="w-4 h-4" />
              Zero External Infrastructure
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              No PostgreSQL, MySQL, Redis, or RabbitMQ dependencies. Starts in 1 second inside a single lightweight Docker container.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
            <h4 className="font-semibold text-fuchsia-600 dark:text-fuchsia-400 text-sm mb-1 flex items-center gap-2">
              <Terminal className="w-4 h-4" />
              Zero Outbound SMTP (Anti-Spam)
            </h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
              Strictly inbound-only architecture. Contains zero SMTP relay code, completely preventing your servers from ever being weaponized as a spam relay or phishing proxy.
            </p>
          </div>
        </div>
      </section>

      {/* Interactive API Explorers Banner */}
      <section className="p-6 rounded-2xl border border-slate-200 dark:border-slate-800 bg-gradient-to-r from-slate-100 to-slate-200/50 dark:from-slate-900/90 dark:to-slate-950/90 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h4 className="text-lg font-bold text-slate-900 dark:text-white font-display">Interactive OpenAPI / Scalar Documentation</h4>
            <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 max-w-xl">
              Inspect all 43 REST endpoints, test live requests with mock headers, and download the full OpenAPI 3.1 specification.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <a
              href={assetUrl('/scalar.html')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-semibold shadow-md transition-colors"
            >
              <span>Scalar API Explorer</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
            <a
              href={assetUrl('/openapi.json')}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-mono border border-slate-200 dark:border-slate-700 shadow-sm transition-colors"
            >
              <span>openapi.json</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>
      </section>

      {/* Navigation Links */}
      <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex justify-between items-center text-xs">
        <span className="text-slate-500 dark:text-slate-400">Next section:</span>
        <Link
          to="/docs/python"
          className="inline-flex items-center gap-1 text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 font-semibold"
        >
          <span>Python SDK Guide</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
