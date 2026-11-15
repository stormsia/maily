import React from 'react';
import { CodeBlock } from '../../components/common/CodeBlock';
import { Callout } from '../../components/common/Callout';
import { Link } from '../../context/RouterContext';
import { ArrowRight, ShieldCheck, Database, Zap, Lock, RefreshCw, Cpu, Layers } from 'lucide-react';
import { GithubIcon } from '../../components/common/Icons';

export const DocsArchitecture: React.FC = () => {
  return (
    <div className="space-y-10">
      {/* Header */}
      <section>
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 text-xs font-mono mb-4">
          <span>Security Architecture & Threat Model</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white font-display" id="system-architecture">
            System Architecture & Resilience
          </h2>
          <a
            href="https://github.com/stormsia/maily#architecture--data-flow"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-xs font-semibold border border-slate-700 shadow-sm transition-all self-start sm:self-auto"
          >
            <GithubIcon className="w-3.5 h-3.5" />
            <span>Architecture in GitHub README ↗</span>
          </a>
        </div>
        <p className="text-base leading-relaxed text-slate-300">
          Maily is engineered from first principles for zero spam relay risk, strict cryptographic isolation, sub-millisecond SQLite WAL persistence, and unprivileged container execution.
        </p>
      </section>

      {/* Core Architectural Pillars */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-4" id="core-pillars">
          Core Architectural Pillars
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-cyan-400 text-sm mb-1.5 flex items-center gap-2">
              <Lock className="w-4 h-4" />
              Fernet-256 Cryptographic Storage
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Private credentials (such as Gmail OAuth refresh tokens, secrets, and raw email bodies) are encrypted with Fernet AES-128-CBC + HMAC-SHA256 before persisting to disk. Tokens never leak in plaintext.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-emerald-400 text-sm mb-1.5 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4" />
              Zero Outbound Spam Relays
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Maily is strictly an inbound email gateway. The codebase contains zero outbound SMTP relay capabilities, completely preventing misuse by attackers attempting to send spam from your servers.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-indigo-400 text-sm mb-1.5 flex items-center gap-2">
              <Database className="w-4 h-4" />
              Sub-Millisecond SQLite WAL Engine
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Persistence is powered by embedded SQLite in Write-Ahead Logging (WAL) mode with background compaction, benchmarking at &lt; 2.5 ms latency without Redis or PostgreSQL overhead.
            </p>
          </div>

          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40">
            <h4 className="font-semibold text-fuchsia-400 text-sm mb-1.5 flex items-center gap-2">
              <RefreshCw className="w-4 h-4" />
              Circuit Breaker & Provider Failover
            </h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Continuous synthetic health probes monitor upstream providers. When failure thresholds are exceeded, the circuit breaker transparently routes mailbox requests to healthy providers.
            </p>
          </div>
        </div>
      </section>

      {/* Threat Model & Mitigations Matrix */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-4" id="threat-model">
          Threat Model & Mitigations Matrix
        </h3>
        <div className="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/40">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-mono bg-slate-950/60">
                <th className="py-3 px-4">Threat Vector</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">Maily Architectural Mitigation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300 font-mono">
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-semibold text-white">Outbound Spam Abuse</td>
                <td className="py-3 px-4 text-rose-400">Critical</td>
                <td className="py-3 px-4 text-slate-300">
                  <strong>Zero Outbound SMTP:</strong> The gateway possesses no outbound mail transmission code.
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-semibold text-white">Credential Leakage</td>
                <td className="py-3 px-4 text-amber-400">High</td>
                <td className="py-3 px-4 text-slate-300">
                  <strong>Fernet-256 Vault:</strong> Sensitive tokens and OAuth credentials encrypted at rest.
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-semibold text-white">DNS Rebinding & CSRF</td>
                <td className="py-3 px-4 text-amber-400">High</td>
                <td className="py-3 px-4 text-slate-300">
                  <strong>OriginGuard Middleware:</strong> Enforces strict Origin and Host validation on mutating routes.
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-semibold text-white">Upstream Downtime</td>
                <td className="py-3 px-4 text-cyan-400">Medium</td>
                <td className="py-3 px-4 text-slate-300">
                  <strong>Multi-Provider Failover:</strong> Automatic circuit breaker and domain fallback across 8+ fleets.
                </td>
              </tr>
              <tr className="hover:bg-slate-800/30">
                <td className="py-3 px-4 font-semibold text-white">Database Lock Contention</td>
                <td className="py-3 px-4 text-cyan-400">Medium</td>
                <td className="py-3 px-4 text-slate-300">
                  <strong>SQLite WAL Mode:</strong> Non-blocking concurrent reads with serialized atomic writes.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Sizing & Performance Model */}
      <section>
        <h3 className="text-xl font-bold text-white font-display mb-3" id="performance-model">
          Sizing & Concurrency Model
        </h3>
        <p className="text-sm text-slate-400 mb-4">
          Engineered for minimal footprint and maximum throughput:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
            <div className="text-2xl font-bold font-mono text-cyan-400">&gt; 2,500/s</div>
            <div className="text-xs text-slate-400 mt-1">Webhook Deliveries / Sec</div>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
            <div className="text-2xl font-bold font-mono text-emerald-400">&gt; 420</div>
            <div className="text-xs text-slate-400 mt-1">Concurrent Polling Queries</div>
          </div>
          <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/40 text-center">
            <div className="text-2xl font-bold font-mono text-indigo-400">&lt; 15 µs</div>
            <div className="text-xs text-slate-400 mt-1">Regex OTP Extraction Time</div>
          </div>
        </div>
      </section>

      {/* CI Security Gates */}
      <Callout type="note" title="6 Automated Security Gates">
        Every commit to the Maily repository passes 6 automated security pipelines: Gitleaks secret detection, Aquasecurity Trivy container scanning, Pip-Audit vulnerability scans, CodeQL SAST, and Zizmor workflow static analysis.
      </Callout>

      {/* Navigation */}
      <div className="pt-6 border-t border-slate-800 flex justify-between items-center text-xs">
        <Link to="/docs/recipes" className="text-slate-400 hover:text-white">
          ← Production Recipes
        </Link>
        <Link
          to="/docs"
          className="inline-flex items-center gap-1 text-cyan-400 hover:text-cyan-300 font-semibold"
        >
          <span>Return to Documentation Hub</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
