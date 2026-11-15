import React, { useState } from 'react';
import {
  Terminal,
  ArrowRight,
  Check,
  Copy,
  Zap,
  ShieldCheck,
  Server,
  Inbox,
  Layers,
  RefreshCw,
  ExternalLink,
  Code2,
  Sparkles,
  Lock,
  Database,
  CheckCircle2,
  HelpCircle,
  ChevronDown,
  Star,
  AlertTriangle
} from 'lucide-react';
import { GithubIcon } from '../components/common/Icons';
import { Link } from '../context/RouterContext';
import { APP_VERSION_TAG } from '../data/version';
import { CodeBlock } from '../components/common/CodeBlock';
import { Callout } from '../components/common/Callout';
import { Tabs } from '../components/common/Tabs';
import { ScreenshotCarousel } from '../components/carousel/ScreenshotCarousel';
import { REPO_PROVIDERS } from '../data/repoProviders';
import { ROUTES } from '../data/routes';

export const HomePage: React.FC = () => {
  const [copiedCmd, setCopiedCmd] = useState(false);

  const dockerCmd = 'docker run -d -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest';

  const copyQuickCmd = () => {
    try {
      navigator.clipboard.writeText(dockerCmd);
      setCopiedCmd(true);
      setTimeout(() => setCopiedCmd(false), 2000);
    } catch {}
  };

  return (
    <div className="flex flex-col space-y-24 py-8">
      {/* Hero Section */}
      <section className="relative px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full text-center pt-8 sm:pt-16">
        {/* Subtle ambient light aura */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-cyan-500/10 blur-[120px] pointer-events-none rounded-full" />
        <div className="absolute top-1/3 left-1/3 -translate-x-1/2 -translate-y-1/2 w-72 h-72 bg-indigo-500/10 blur-[100px] pointer-events-none rounded-full" />

        {/* Release Pill button leading to GitHub */}
        <a
          href="https://github.com/stormsia/maily"
          target="_blank"
          rel="noopener noreferrer"
          role="button"
          aria-label="Maily on GitHub repository"
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs font-mono text-slate-700 dark:text-slate-300 shadow-sm mb-8 hover:border-cyan-500/60 hover:bg-slate-50 dark:hover:bg-slate-800/70 hover:text-cyan-700 dark:hover:text-cyan-300 transition-all group cursor-pointer"
        >
          <span className="flex h-2 w-2 rounded-full bg-cyan-500 animate-ping" />
          <span className="text-cyan-700 dark:text-cyan-400 font-semibold">Maily {APP_VERSION_TAG}</span>
          <span className="text-slate-300 dark:text-slate-700">·</span>
          <span>Self-Hosted Universal Temporary Email Gateway</span>
          <ArrowRight className="w-3.5 h-3.5 text-slate-400 group-hover:translate-x-0.5 group-hover:text-cyan-500 transition-all" />
        </a>

        {/* Headline */}
        <h1 className="text-4xl sm:text-6xl lg:text-7xl font-extrabold tracking-tight text-slate-900 dark:text-white font-display max-w-5xl mx-auto leading-[1.1]">
          Disposable Email Gateway for{' '}
          <span className="bg-gradient-to-r from-cyan-600 via-sky-500 to-indigo-600 dark:from-cyan-400 dark:via-sky-300 dark:to-indigo-400 bg-clip-text text-transparent">
            Automated Testing & AI
          </span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed">
          Aggregates 8+ disposable mail providers into one unified REST API and async Python SDK. Built with embedded SQLite WAL, AES-GCM encryption, and zero external DB dependencies.
        </p>

        {/* Priority Action Row: Star on GitHub (Top Priority) + Docs */}
        <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3.5 max-w-2xl mx-auto">
          {/* Top Priority Action: Star on GitHub */}
          <a
            href="https://github.com/stormsia/maily"
            target="_blank"
            rel="noopener noreferrer"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm border border-slate-700 shadow-xl shadow-cyan-950/20 hover:border-cyan-500/60 transition-all group"
          >
            <GithubIcon className="w-5 h-5 text-white group-hover:scale-110 transition-transform" />
            <span>Star on GitHub</span>
            <span className="flex items-center gap-1 px-2 py-0.5 text-xs font-mono rounded bg-slate-800 text-amber-300 border border-slate-700 font-bold ml-0.5">
              <Star className="w-3.5 h-3.5 fill-amber-300 text-amber-300" />
              <span>Star</span>
            </span>
          </a>

          {/* Secondary Action: Explore Documentation */}
          <Link
            to="/docs"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm shadow-md shadow-cyan-600/20 transition-all"
          >
            <span>Explore Documentation</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {/* Quick Run Box ($ docker run ...) */}
        <div className="mt-4 flex items-center justify-center max-w-xl mx-auto">
          <div className="w-full flex items-center justify-between gap-3 px-4 py-2.5 rounded-xl bg-white/70 dark:bg-slate-900/70 border border-slate-200 dark:border-slate-800 font-mono text-xs text-slate-800 dark:text-slate-200 backdrop-blur-sm shadow-sm">
            <span className="text-cyan-600 dark:text-cyan-400 select-none font-bold">$</span>
            <span className="truncate">{dockerCmd}</span>
            <button
              onClick={copyQuickCmd}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors shrink-0"
              aria-label="Copy command"
            >
              {copiedCmd ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Key Feature Badges */}
        <div className="mt-12 grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900/40 shadow-sm backdrop-blur-sm">
            <div className="flex items-center gap-2 text-cyan-600 dark:text-cyan-400 font-semibold text-sm mb-1 font-mono">
              <Zap className="w-4 h-4" />
              <span>Sub-ms Latency</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">Embedded SQLite WAL storage ensures instantaneous mailbox creation.</p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900/40 shadow-sm backdrop-blur-sm">
            <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 font-semibold text-sm mb-1 font-mono">
              <Layers className="w-4 h-4" />
              <span>8+ Providers</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">Mail.tm, TempMail.plus, Temp-Mail.io, Temp.tf, Gmail &amp; custom drivers.</p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900/40 shadow-sm backdrop-blur-sm">
            <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm mb-1 font-mono">
              <Lock className="w-4 h-4" />
              <span>AES-256 GCM</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">Sensitive tokens and stored payloads encrypted at rest automatically.</p>
          </div>
          <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800/80 bg-white dark:bg-slate-900/40 shadow-sm backdrop-blur-sm">
            <div className="flex items-center gap-2 text-fuchsia-600 dark:text-fuchsia-400 font-semibold text-sm mb-1 font-mono">
              <Server className="w-4 h-4" />
              <span>Zero-Config</span>
            </div>
            <p className="text-xs text-slate-600 dark:text-slate-400">No Redis, Postgres, or RabbitMQ. Single self-contained container.</p>
          </div>
        </div>
      </section>

      {/* Admin Console Interface Tour Carousel */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full" id="workstations">
        <div className="text-center max-w-2xl mx-auto mb-8">
          <div className="inline-flex items-center gap-1.5 text-xs font-mono font-medium text-cyan-600 dark:text-cyan-400 mb-2">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Interactive Web Console</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white tracking-tight font-display">
            Built-In Management Console & Workstations
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 dark:text-slate-400 mt-1">
            Visual control over disposable email infrastructure: live telemetry, multi-provider mailboxes, OTP inspector, TTL retention sweeper, and scoped API keys.
          </p>
        </div>
        <ScreenshotCarousel />
      </section>

      {/* Integration Quickstart Tabs */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-50 dark:bg-cyan-950/60 border border-cyan-200 dark:border-cyan-800/60 text-cyan-700 dark:text-cyan-300 text-xs font-mono mb-3">
            <Server className="w-3.5 h-3.5" />
            <span>Client-Server Architecture</span>
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
            Integrate in Under 60 Seconds
          </h2>
          <p className="mt-3 text-slate-600 dark:text-slate-400 text-sm">
            Launch the <strong>Maily Gateway Server</strong> first via Docker, then connect your test suite using the Python async SDK or direct REST cURL calls.
          </p>
        </div>

        <Tabs
          defaultTab="server"
          items={[
            {
              id: 'server',
              label: '1. Maily Gateway Server (Docker)',
              content: (
                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl border border-cyan-500/30 bg-cyan-500/5 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2.5">
                    <Server className="w-4 h-4 text-cyan-600 dark:text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-cyan-700 dark:text-cyan-300 font-semibold">Core Gateway Server:</strong> Run this self-hosted service first. The Python client SDK and REST requests talk to this server at <code className="font-mono text-cyan-600 dark:text-cyan-400">http://127.0.0.1:8477</code>.
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Option A — Instant single command with persistent volume:
                  </p>
                  <CodeBlock
                    language="bash"
                    filename="terminal"
                    code="docker run -d -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest"
                  />

                  <p className="text-xs text-slate-600 dark:text-slate-300 pt-2">
                    Option B — Official production Compose specification (<code className="font-mono text-cyan-600 dark:text-cyan-400">docker-compose.prod.yml</code>):
                  </p>
                  <CodeBlock
                    language="yaml"
                    filename="docker-compose.prod.yml"
                    code={`services:
  maily:
    image: ghcr.io/stormsia/maily:latest
    container_name: maily
    restart: unless-stopped
    ports:
      - "8477:8477"
    environment:
      - MAILY_HOST=0.0.0.0
      - MAILY_PORT=8477
      - MAILY_API_KEY=your_secret_api_key
      - MAILY_DATABASE_URL=sqlite+aiosqlite:////data/maily.db
    volumes:
      - maily_data:/data
    security_opt:
      - no-new-privileges:true

volumes:
  maily_data:`}
                  />

                  <div className="pt-2 flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3 text-xs font-mono text-slate-500 dark:text-slate-400">
                      <span>Dashboard: http://127.0.0.1:8477</span>
                      <span>•</span>
                      <span>Docs: http://127.0.0.1:8477/docs</span>
                    </div>
                    <a
                      href="https://github.com/stormsia/maily#option-a--docker-pre-built-image-no-git-clone-required"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 shadow-sm transition-all"
                    >
                      <GithubIcon className="w-3.5 h-3.5" />
                      <span>Docker Setup in GitHub README ↗</span>
                    </a>
                  </div>
                </div>
              ),
            },
            {
              id: 'python',
              label: '2. Python SDK (maily-client)',
              content: (
                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-amber-700 dark:text-amber-300 font-semibold">Maily Server Required:</strong> The <code className="font-mono text-cyan-600 dark:text-cyan-400">maily-client</code> library connects to your running Maily Gateway Server (<code className="font-mono">http://127.0.0.1:8477</code>). <strong>Without the server running, client calls will fail with a connection error.</strong>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Install with <code className="text-cyan-600 dark:text-cyan-400 font-mono">pip install maily-client</code> or <code className="text-cyan-600 dark:text-cyan-400 font-mono">uv add maily-client</code>:
                  </p>
                  <CodeBlock
                    language="python"
                    filename="test_verification.py"
                    code={`import asyncio
from maily_client import MailyClient

async def main():
    # Connects to your self-hosted Maily Gateway Server
    async with MailyClient(base_url="http://127.0.0.1:8477", api_key="your_secret_api_key") as client:
        # Create an ephemeral mailbox
        mailbox = await client.create_mailbox(provider="mail.tm")
        print(f"Inbox ready: {mailbox.address}")

        # Wait for the verification email and extract 6-digit OTP code
        message = await client.wait_for_message(mailbox.id, timeout=30)
        otp = client.extract_otp(message.text)
        print(f"Extracted OTP: {otp}")

asyncio.run(main())`}
                  />

                  <div className="pt-2 flex justify-end">
                    <a
                      href="https://github.com/stormsia/maily#standalone-python-client-sdk-maily-client"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 shadow-sm transition-all"
                    >
                      <GithubIcon className="w-3.5 h-3.5" />
                      <span>Python Quickstart in GitHub README ↗</span>
                    </a>
                  </div>
                </div>
              ),
            },
            {
              id: 'curl',
              label: '3. cURL / REST API',
              content: (
                <div className="space-y-4">
                  <div className="p-3.5 rounded-xl border border-amber-500/30 bg-amber-500/5 text-xs text-slate-700 dark:text-slate-300 flex items-start gap-2.5">
                    <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                    <div>
                      <strong className="text-amber-700 dark:text-amber-300 font-semibold">Maily Server Required:</strong> Direct HTTP calls must target your running Maily server instance on port 8477.
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-300">
                    Direct HTTP calls to the gateway API:
                  </p>
                  <CodeBlock
                    language="bash"
                    filename="terminal"
                    code={`# 1. Create temporary mailbox
curl -X POST http://127.0.0.1:8477/api/v1/mailboxes \\
  -H "X-API-Key: your_secret_api_key" \\
  -H "Content-Type: application/json" \\
  -d '{"provider": "mail.tm"}'

# 2. List incoming messages
curl -X GET http://127.0.0.1:8477/api/v1/mailboxes/{mailbox_id}/messages \\
  -H "X-API-Key: your_secret_api_key"

# 3. Read specific message with HTML & text body
curl -X GET http://127.0.0.1:8477/api/v1/messages/{message_id} \\
  -H "X-API-Key: your_secret_api_key"`}
                  />

                  <div className="pt-2 flex justify-end">
                    <a
                      href="https://github.com/stormsia/maily#quickstart--getting-started"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold border border-slate-300 dark:border-slate-700 shadow-sm transition-all"
                    >
                      <GithubIcon className="w-3.5 h-3.5" />
                      <span>cURL Guide in GitHub README ↗</span>
                    </a>
                  </div>
                </div>
              ),
            },
          ]}
        />

        {/* Global Quickstart Link to README */}
        <div className="mt-6 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/50 backdrop-blur-sm flex flex-col sm:flex-row items-center justify-between gap-3 text-xs shadow-sm">
          <div className="flex items-center gap-2.5 text-slate-700 dark:text-slate-300">
            <span className="flex h-2 w-2 rounded-full bg-cyan-500 animate-pulse" />
            <span>Looking for full architectural deep-dives, benchmark configs, and CLI flags?</span>
          </div>
          <a
            href="https://github.com/stormsia/maily#quickstart--getting-started"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100 font-semibold shadow-sm transition-all shrink-0 cursor-pointer"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Open Quickstart in GitHub README</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        </div>
      </section>

      {/* Provider Matrix Teaser */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full">
        <div className="p-8 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 mb-6">
            <div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white font-display">Provider Unified Ecosystem</h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 mt-1">
                Zero lock-in. Switch providers on the fly without changing a single line in your test fixtures.
              </p>
            </div>
            <Link
              to="/docs/providers"
              className="text-xs font-semibold text-cyan-600 dark:text-cyan-400 hover:text-cyan-700 dark:hover:text-cyan-300 inline-flex items-center gap-1"
            >
              <span>View Full Provider Matrix</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2.5">
            {REPO_PROVIDERS.map((p) => (
              <div key={p.id} className="p-3 rounded-xl bg-slate-50 dark:bg-slate-950/60 border border-slate-200 dark:border-slate-800 text-center">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200 block font-mono truncate">{p.name}</span>
                <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-mono font-medium capitalize">
                  {p.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Frequently Asked Questions */}
      <section className="px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto w-full pb-12" id="faq">
        <div className="text-center max-w-3xl mx-auto mb-10">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/10 dark:bg-cyan-950/60 border border-cyan-500/20 dark:border-cyan-800/60 text-cyan-600 dark:text-cyan-300 text-xs font-mono mb-3">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Questions & Answers</span>
          </div>
          <h2 className="text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display">
            Frequently Asked Questions
          </h2>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Everything you need to know about Maily temporary email gateway architecture, self-hosting, and licensing.
          </p>
        </div>

        <div className="max-w-4xl mx-auto space-y-4">
          {(ROUTES['/'].faqs || []).map((faq, idx) => (
            <details
              key={idx}
              className="group p-5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/40 shadow-sm transition-colors open:border-cyan-500/50"
            >
              <summary className="flex items-center justify-between cursor-pointer list-none text-sm font-semibold text-slate-900 dark:text-white select-none">
                <span className="pr-4">{faq.question}</span>
                <ChevronDown className="w-4 h-4 text-slate-400 transition-transform group-open:rotate-180 flex-shrink-0" />
              </summary>
              <p className="mt-3 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed pt-3 border-t border-slate-100 dark:border-slate-800/60">
                {faq.answer}
              </p>
            </details>
          ))}
        </div>
      </section>
    </div>
  );
};
