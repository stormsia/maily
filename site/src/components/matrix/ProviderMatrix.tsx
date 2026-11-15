import React, { useState, useEffect } from 'react';
import {
  Check,
  X,
  Zap,
  ShieldCheck,
  Lock,
  Layers,
  Search,
  ExternalLink,
  Copy,
  Code2,
  Table,
  Grid,
  Radio,
  Server,
  Terminal
} from 'lucide-react';
import { useRouter } from '../../context/RouterContext';
import { REPO_PROVIDERS, RepoProviderInfo } from '../../data/repoProviders';

export const ProviderMatrix: React.FC = () => {
  const { assetUrl } = useRouter();
  const [filter, setFilter] = useState<string>('all');
  const [search, setSearch] = useState<string>('');
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [providerHealth, setProviderHealth] = useState<Record<string, string>>({});

  useEffect(() => {
    fetch(assetUrl('/provider_health_state.json'))
      .then((res) => res.json())
      .then((data) => {
        if (data && data.providers) {
          const map: Record<string, string> = {};
          for (const [k, v] of Object.entries(data.providers) as [string, any][]) {
            map[k] = v.last_status || 'operational';
          }
          setProviderHealth(map);
        }
      })
      .catch(() => {});
  }, [assetUrl]);

  const filteredProviders = REPO_PROVIDERS.filter((p) => {
    const matchesSearch =
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.description.toLowerCase().includes(search.toLowerCase()) ||
      p.domains.toLowerCase().includes(search.toLowerCase());

    if (!matchesSearch) return false;

    if (filter === 'parent') return p.targetKind === 'parent';
    if (filter === 'domain') return p.targetKind === 'domain';
    if (filter === 'security') return p.passwordOrPin;
    if (filter === 'attachments') return p.attachments;
    if (filter === 'custom-domain') return p.customDomain;
    return true;
  });

  const handleCopySnippet = (id: string, snippet: string) => {
    try {
      navigator.clipboard.writeText(snippet);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch {}
  };

  return (
    <div className="space-y-6">
      {/* Control Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search provider, domain, or capability..."
            className="w-full pl-9 pr-4 py-2 bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 rounded-lg text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-cyan-500 font-mono"
          />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-1.5">
          {[
            { id: 'all', label: 'All 8 Providers' },
            { id: 'domain', label: 'Domain Adapters' },
            { id: 'parent', label: 'Parent Router (Gmail)' },
            { id: 'security', label: 'Password / PIN' },
            { id: 'attachments', label: 'Attachments' },
            { id: 'custom-domain', label: 'Custom Domain' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
                filter === tab.id
                  ? 'bg-cyan-600 text-white font-semibold'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* View Mode Toggle */}
        <div className="hidden sm:flex items-center gap-1 border-l border-slate-200 dark:border-slate-800 pl-3">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'grid'
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white'
                : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
            title="Card Grid View"
          >
            <Grid className="w-4 h-4" />
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`p-1.5 rounded-lg transition-colors ${
              viewMode === 'table'
                ? 'bg-slate-200 dark:bg-slate-800 text-slate-900 dark:text-white'
                : 'text-slate-400 hover:text-slate-600 dark:hover:text-slate-200'
            }`}
            title="Comparison Table View"
          >
            <Table className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Provider Matrix Body */}
      {filteredProviders.length === 0 ? (
        <div className="p-12 text-center rounded-2xl border border-dashed border-slate-300 dark:border-slate-800 bg-white dark:bg-slate-900/30 space-y-3">
          <Server className="w-8 h-8 mx-auto text-slate-400 opacity-60" />
          <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
            No providers found matching &ldquo;<span className="text-cyan-600 dark:text-cyan-400 font-mono">{search}</span>&rdquo;
          </p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Try clearing the search query or selecting &ldquo;All 8 Providers&rdquo;.
          </p>
          <button
            onClick={() => {
              setSearch('');
              setFilter('all');
            }}
            className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-mono transition-colors"
          >
            Reset Filters
          </button>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProviders.map((p) => {
            const liveStatus = providerHealth[p.name] || 'operational';
            const isOp = liveStatus === 'operational';

            return (
              <div
                key={p.id}
                className="p-5 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 shadow-sm flex flex-col justify-between space-y-4 hover:border-cyan-500/50 transition-colors"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-base text-slate-900 dark:text-white font-mono">
                        {p.name}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold uppercase ${
                        p.targetKind === 'parent'
                          ? 'bg-indigo-50 dark:bg-indigo-500/10 text-indigo-700 dark:text-indigo-400 border border-indigo-200 dark:border-indigo-500/30'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300'
                      }`}>
                        {p.targetKind}
                      </span>
                    </div>

                    <div className={`flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium border ${
                      isOp
                        ? 'bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30'
                        : 'bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-400 border-amber-200 dark:border-amber-500/30'
                    }`}>
                      <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse"></span>
                      <span className="capitalize">{liveStatus}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                    {p.description}
                  </p>

                  <div className="text-[11px] font-mono text-slate-500 dark:text-slate-400">
                    <span className="text-slate-400">Domains: </span>
                    <span className="text-cyan-600 dark:text-cyan-400">{p.domains}</span>
                  </div>

                  {/* Capability Matrix Badges */}
                  <div className="grid grid-cols-2 gap-1.5 pt-2 border-t border-slate-100 dark:border-slate-800/80 text-[11px] font-mono">
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.customUsername ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                      <span>Custom Name</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.customDomain ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                      <span>Custom Domain</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.passwordOrPin ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                      <span>Password / PIN</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.attachments ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                      <span>Attachments</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.rawMimeSource ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <X className="w-3.5 h-3.5 text-slate-400 shrink-0" />}
                      <span>Raw MIME Source</span>
                    </div>
                    <div className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
                      {p.markRead ? <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" /> : <span className="text-slate-400 text-xs">⚪</span>}
                      <span>Read Tracking</span>
                    </div>
                  </div>
                </div>

                {/* Python snippet box */}
                <div className="pt-2">
                  <div className="flex items-center justify-between p-2 rounded-lg bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 text-[11px] font-mono text-slate-700 dark:text-slate-300">
                    <span className="truncate pr-2">{p.pythonSnippet}</span>
                    <button
                      onClick={() => handleCopySnippet(p.id, p.pythonSnippet)}
                      className="p-1 hover:bg-slate-200 dark:hover:bg-slate-800 rounded transition-colors text-slate-400 hover:text-slate-900 dark:hover:text-white"
                      title="Copy Python snippet"
                    >
                      {copiedId === p.id ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* Table View matching docs/PROVIDERS.md */
        <div className="rounded-xl border border-slate-200 dark:border-slate-800 overflow-x-auto shadow-sm">
          <table className="w-full text-left border-collapse text-xs font-mono">
            <thead>
              <tr className="bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300">
                <th className="p-3">Provider Slug</th>
                <th className="p-3">Target Kind</th>
                <th className="p-3">Custom Username</th>
                <th className="p-3">Custom Domain</th>
                <th className="p-3">Passwords / PIN</th>
                <th className="p-3">Raw Source</th>
                <th className="p-3">Attachments</th>
                <th className="p-3">Read Tracking</th>
                <th className="p-3">Health Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80 bg-white dark:bg-slate-950">
              {filteredProviders.map((p) => {
                const liveStatus = providerHealth[p.name] || 'operational';
                return (
                  <tr key={p.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/40">
                    <td className="p-3 font-bold text-slate-900 dark:text-white">{p.name}</td>
                    <td className="p-3 capitalize text-slate-500">{p.targetKind}</td>
                    <td className="p-3">{p.customUsername ? '✅ Supported' : '❌ No'}</td>
                    <td className="p-3">{p.customDomain ? '✅ Supported' : p.targetKind === 'parent' ? '❌ Own Account' : '❌ No'}</td>
                    <td className="p-3">{p.passwordOrPin ? (p.name === 'tempmail.plus' ? '✅ PIN Code' : '✅ Password') : (p.targetKind === 'parent' ? '❌ OAuth2' : '❌ No')}</td>
                    <td className="p-3">{p.rawMimeSource ? '✅ Supported' : '❌ No'}</td>
                    <td className="p-3">{p.attachments ? '✅ Supported' : '❌ No'}</td>
                    <td className="p-3">{p.markRead ? '✅ Supported' : '⚪ No-op'}</td>
                    <td className="p-3">
                      <span className="text-emerald-600 dark:text-emerald-400 font-semibold capitalize">{liveStatus}</span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
