import React, { useState, useEffect, useRef } from 'react';
import { Search, X, FileText, ArrowRight, CornerDownLeft } from 'lucide-react';
import { useRouter } from '../../context/RouterContext';

interface SearchItem {
  title: string;
  path: string;
  category: string;
  description: string;
  keywords?: string[];
}

const SEARCH_DATABASE: SearchItem[] = [
  {
    title: 'Overview & Getting Started',
    path: '/docs',
    category: 'Documentation',
    description: 'Quick introduction to Maily, quickstarts, and architectural philosophy.',
    keywords: ['quickstart', 'install', 'introduction', 'start'],
  },
  {
    title: 'Python SDK (maily-client)',
    path: '/docs/python',
    category: 'Guides',
    description: 'Official async Python client, Pydantic v2 schemas, OTP extraction helpers.',
    keywords: ['python', 'pydantic', 'pytest', 'asyncio', 'client', 'sdk', 'pip'],
  },
  {
    title: 'cURL & Universal REST API',
    path: '/docs/curl',
    category: 'Guides',
    description: 'REST endpoints for mailboxes, messages, attachments, and SSE events via curl.',
    keywords: ['curl', 'rest', 'http', 'api', 'endpoints', 'postman'],
  },
  {
    title: 'Docker & Self-Hosting in 60s',
    path: '/docs/docker',
    category: 'Guides',
    description: 'Zero-config Docker Compose, Portainer, and Kubernetes deployment guides.',
    keywords: ['docker', 'compose', 'container', 'self-host', 'portainer', 'sqlite'],
  },
  {
    title: 'Provider Matrix & Capabilities',
    path: '/docs/providers',
    category: 'Providers',
    description: 'Comparison of Mail.tm, Mail.gw, 1secmail, GuerrillaMail, and TempMail features.',
    keywords: ['providers', 'mailtm', '1secmail', 'guerrillamail', 'matrix', 'domains'],
  },
  {
    title: 'Adding Custom Providers',
    path: '/docs/adding-providers',
    category: 'Advanced',
    description: 'Step-by-step tutorial to implement and register new email provider drivers.',
    keywords: ['custom', 'driver', 'extend', 'plugin', 'provider', 'interface'],
  },
  {
    title: 'Production Testing Recipes',
    path: '/docs/recipes',
    category: 'Recipes',
    description: 'Playwright, Cypress, and Pytest email verification and OTP parsing examples.',
    keywords: ['recipes', 'playwright', 'cypress', 'otp', 'verification', 'testing'],
  },
  {
    title: 'Architecture & System Resilience',
    path: '/docs/architecture',
    category: 'Advanced',
    description: 'SQLite WAL storage, AES-256 encryption at rest, circuit breaker failover.',
    keywords: ['architecture', 'sqlite', 'wal', 'encryption', 'circuit breaker', 'security'],
  },
  {
    title: 'Live Security & Health Analytics',
    path: '/analytics',
    category: 'Analytics',
    description: 'Live provider uptime, latency benchmarks, test coverage, and security telemetry.',
    keywords: ['analytics', 'benchmarks', 'latency', 'health', 'metrics', 'telemetry'],
  },
  {
    title: 'Scalar API Reference',
    path: '/scalar.html',
    category: 'API Explorer',
    description: 'Interactive modern Scalar documentation with live request testing.',
    keywords: ['scalar', 'api reference', 'swagger', 'interactive'],
  },
  {
    title: 'Swagger UI Cyberpunk',
    path: '/swagger.html',
    category: 'API Explorer',
    description: 'Dark-themed Swagger UI with complete endpoint schema execution.',
    keywords: ['swagger', 'openapi', 'docs'],
  },
];

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({ isOpen, onClose }) => {
  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const { navigate, assetUrl } = useRouter();

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      setSelectedIndex(0);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  const filtered = SEARCH_DATABASE.filter((item) => {
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return (
      item.title.toLowerCase().includes(q) ||
      item.description.toLowerCase().includes(q) ||
      item.category.toLowerCase().includes(q) ||
      item.keywords?.some((k) => k.toLowerCase().includes(q))
    );
  });

  const handleSelect = (path: string) => {
    onClose();
    if (path.startsWith('http://') || path.startsWith('https://')) {
      window.location.href = path;
    } else if (path.endsWith('.html') || path.endsWith('.json')) {
      window.location.href = assetUrl(path);
    } else {
      navigate(path);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1 < filtered.length ? prev + 1 : 0));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : filtered.length - 1));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filtered[selectedIndex]) {
        handleSelect(filtered[selectedIndex].path);
      }
    } else if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center pt-16 sm:pt-24 px-4 bg-slate-950/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden text-slate-800 dark:text-slate-100 transition-all"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={handleKeyDown}
      >
        <div className="flex items-center px-4 py-3 border-b border-slate-200 dark:border-slate-800 gap-3">
          <Search className="w-5 h-5 text-cyan-600 dark:text-cyan-400 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            className="w-full bg-transparent text-slate-900 dark:text-slate-100 placeholder-slate-400 text-sm sm:text-base focus:outline-none"
            placeholder="Search documentation, guides, and API endpoints..."
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setSelectedIndex(0);
            }}
          />
          {query && (
            <button
              onClick={() => setQuery('')}
              className="p-1 hover:bg-slate-100 dark:hover:bg-slate-800 rounded text-slate-400 hover:text-slate-600 dark:hover:text-slate-200"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs text-slate-400 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded font-mono">
            ESC
          </kbd>
        </div>

        <div className="max-h-96 overflow-y-auto p-2 divide-y divide-slate-100 dark:divide-slate-800/40">
          {filtered.length === 0 ? (
            <div className="py-12 text-center text-slate-400 text-sm">
              No results found for &ldquo;<span className="text-slate-800 dark:text-slate-200 font-semibold">{query}</span>&rdquo;
            </div>
          ) : (
            filtered.map((item, idx) => {
              const isSelected = idx === selectedIndex;
              return (
                <div
                  key={item.path}
                  onClick={() => handleSelect(item.path)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`flex items-start gap-3 p-3 rounded-xl cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-cyan-50 dark:bg-cyan-950/40 border border-cyan-300 dark:border-cyan-500/40 text-slate-900 dark:text-white'
                      : 'hover:bg-slate-50 dark:hover:bg-slate-800/50 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <div className={`mt-0.5 p-2 rounded-lg ${isSelected ? 'bg-cyan-100 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300' : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'}`}>
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-900 dark:text-slate-100 text-sm">{item.title}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-700/60 font-mono">
                        {item.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-1 truncate">{item.description}</p>
                  </div>
                  <div className="flex items-center self-center text-slate-400">
                    {isSelected ? <CornerDownLeft className="w-4 h-4 text-cyan-600 dark:text-cyan-400" /> : <ArrowRight className="w-4 h-4" />}
                  </div>
                </div>
              );
            })
          )}
        </div>

        <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 dark:bg-slate-950/60 border-t border-slate-200 dark:border-slate-800 text-xs text-slate-500">
          <div className="flex items-center gap-3">
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px]">↑↓</kbd> navigate</span>
            <span><kbd className="px-1.5 py-0.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded text-[10px]">↵</kbd> select</span>
          </div>
          <span className="font-mono text-[11px] text-cyan-600 dark:text-cyan-400">Maily Hub Search</span>
        </div>
      </div>
    </div>
  );
};
