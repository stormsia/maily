import React from 'react';
import { X, ExternalLink, BookOpen, Activity, Terminal, Shield, Cpu, Box } from 'lucide-react';
import { Link, useRouter } from '../../context/RouterContext';
import { DOCS_NAV_SECTIONS } from '../../data/routes';
import { APP_VERSION_TAG } from '../../data/version';

interface MobileNavProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenSearch: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({ isOpen, onClose, onOpenSearch }) => {
  const { currentPath, assetUrl } = useRouter();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over panel */}
      <div className="fixed inset-y-0 right-0 w-full max-w-xs bg-white dark:bg-slate-900 border-l border-slate-200 dark:border-slate-800 p-6 shadow-2xl flex flex-col justify-between overflow-y-auto">
        <div className="space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-slate-800">
            <div className="flex items-center gap-2.5">
              <img
                src={assetUrl('/assets/logo.png')}
                alt="Maily Logo"
                className="w-8 h-8 rounded-lg object-contain"
                width={32}
                height={32}
              />
              <span className="font-semibold text-lg text-slate-900 dark:text-slate-100 tracking-tight">Maily</span>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-lg text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Close menu"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={() => {
              onClose();
              onOpenSearch();
            }}
            className="w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl bg-slate-100 dark:bg-slate-800/80 border border-slate-200 dark:border-slate-700/80 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200 transition-colors"
          >
            <span>Search documentation...</span>
            <kbd className="px-1.5 py-0.5 text-xs bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded font-mono text-slate-500 dark:text-slate-400">⌘K</kbd>
          </button>

          {/* Quick Links */}
          <div className="space-y-1">
            <Link
              to="/"
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentPath === '/' ? 'bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Box className="w-4 h-4 text-cyan-600 dark:text-cyan-400" />
              Overview
            </Link>
            <Link
              to="/docs"
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentPath.startsWith('/docs') ? 'bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <BookOpen className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
              Documentation
            </Link>
            <Link
              to="/analytics"
              onClick={onClose}
              className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                currentPath === '/analytics' ? 'bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 font-semibold' : 'text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800'
              }`}
            >
              <Activity className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              Live Health & Analytics
            </Link>
          </div>

          {/* Documentation Sections */}
          <div className="pt-4 border-t border-slate-200 dark:border-slate-800 space-y-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">Documentation</h4>
            {DOCS_NAV_SECTIONS.map((sec) => (
              <div key={sec.title} className="space-y-1">
                <div className="text-[11px] font-mono font-medium text-slate-500 dark:text-slate-400 px-3">{sec.title}</div>
                {sec.items.map((item) =>
                  item.external ? (
                    <a
                      key={item.path}
                      href={assetUrl(item.path)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-between px-3 py-1.5 rounded-lg text-xs text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                    >
                      <span>{item.title.replace(' ↗', '')}</span>
                      <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                    </a>
                  ) : (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={onClose}
                      className={`block px-3 py-1.5 rounded-lg text-xs transition-colors ${
                        currentPath === item.path
                          ? 'bg-cyan-50 dark:bg-cyan-500/15 text-cyan-700 dark:text-cyan-300 font-semibold'
                          : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                      }`}
                    >
                      {item.title}
                    </Link>
                  )
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Footer info in drawer */}
        <div className="pt-6 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>{APP_VERSION_TAG} · MIT License</span>
          <a
            href="https://github.com/stormsia/maily"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-cyan-600 dark:hover:text-cyan-400 font-mono"
          >
            GitHub ↗
          </a>
        </div>
      </div>
    </div>
  );
};
