import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, Check, X, Shield, Zap, RefreshCw, ExternalLink, Activity } from 'lucide-react';
import { ProviderMatrix } from '../../components/matrix/ProviderMatrix';
import { GithubIcon } from '../../components/common/Icons';

export const DocsProviders: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Provider Fleet Matrix</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="provider-matrix">
            Supported Disposable Mail Providers
          </h2>
          <a
            href="https://github.com/stormsia/maily#supported-providers--capabilities"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Providers in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          Maily aggregates public temporary email networks and private parent accounts into one normalized REST API. The gateway dynamically provisions inboxes, translates payloads, downloads attachments, and coordinates circuit breaker failover.
        </p>
      </section>

      {/* Interactive Provider Capabilities Matrix */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-4" id="capabilities-table">
          Interactive Capabilities Matrix & Telemetry
        </h3>
        <ProviderMatrix />
      </section>

      {/* Domain Rotation & Anti-Spam Blocklist Bypass */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="domain-rotation">
          40+ Rotating Domains Pool & Anti-Blocklist Resistance
        </h3>
        <p className="text-sm text-slate-300 leading-relaxed">
          Many modern SaaS registration forms block common disposable email domains like <code className="text-slate-200 font-mono">@mailtm.net</code> or <code className="text-slate-200 font-mono">@tempmail.plus</code>. Maily prevents test failures through several mechanisms:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="text-sm font-semibold text-cyan-400 mb-1">Fleet Domain Pool</h4>
            <p className="text-xs text-slate-400">
              Maintains an active pool of 40+ distinct rotating domain suffixes across different TLDs (.net, .plus, .im, .me).
            </p>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="text-sm font-semibold text-emerald-400 mb-1">Gmail Alias Tags</h4>
            <p className="text-xs text-slate-400">
              Supports real Gmail parent inboxes via OAuth2, routing <code className="font-mono text-slate-300">username+tag@gmail.com</code> which bypasses all anti-tempmail lists.
            </p>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="text-sm font-semibold text-indigo-400 mb-1">Automatic Failover</h4>
            <p className="text-xs text-slate-400">
              When a provider encounters HTTP 502/504 errors, the circuit breaker redirects to an operational fallback provider.
            </p>
          </div>
        </div>
      </section>

      {/* Offline & Hermetic Testing with NoopMail */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="noopmail">
          Offline & Air-Gapped CI Testing with <code className="font-mono text-cyan-400">noopmail</code>
        </h3>
        <p className="text-sm text-slate-400 mb-3">
          For hermetic unit tests or air-gapped CI environments with zero internet access, use the built-in <code className="text-cyan-400 font-mono">noopmail</code> provider. It provisions virtual inboxes in memory and allows injecting mock incoming emails via local API:
        </p>
        <CodeBlock
          language="python"
          code={`# Create mock mailbox without outbound internet access
box = await client.create_temp_mailbox(provider="noopmail")
print(box.address)  # -> "test-user@noopmail.org"`}
        />
      </section>



      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/docker" className="text-slate-400 hover:text-white">
          ← Docker & Deployment
        </Link>
        <Link
          to="/docs/adding-providers"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Adding Custom Providers</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
