import React, { useState, useEffect } from 'react';
import {
  Search,
  Sun,
  Moon,
  Menu,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';
import { GithubIcon } from '../common/Icons';
import { Link, useRouter } from '../../context/RouterContext';
import { useTheme } from '../../context/ThemeContext';
import { APP_VERSION_TAG } from '../../data/version';
import { MobileNav } from './MobileNav';
import { SearchModal } from './SearchModal';

export const Header: React.FC = () => {
  const { currentPath, assetUrl } = useRouter();
  const { theme, toggleTheme } = useTheme();
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isApiDropdownOpen, setIsApiDropdownOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setIsSearchOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <>
      <header className="sticky top-0 z-40 w-full border-b border-slate-200/90 dark:border-slate-800/80 bg-white/80 dark:bg-[#070b12]/80 backdrop-blur-md transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Logo & Brand */}
          <div className="flex items-center gap-6">
            <Link to="/" className="flex items-center gap-3 group">
              <img
                src={assetUrl('/assets/logo.png')}
                alt="Maily Logo"
                className="w-9 h-9 rounded-xl object-contain shadow-sm group-hover:scale-105 transition-transform"
                width={36}
                height={36}
              />
              <div className="flex flex-col">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-lg tracking-tight text-slate-900 dark:text-white font-display">Maily</span>
                  <span className="px-1.5 py-0.5 text-[10px] font-mono font-semibold rounded bg-cyan-50 dark:bg-cyan-500/10 text-cyan-700 dark:text-cyan-400 border border-cyan-200 dark:border-cyan-500/30">
                    {APP_VERSION_TAG}
                  </span>
                </div>
                <span className="text-[10px] text-slate-500 dark:text-slate-400 hidden sm:block tracking-wide">Universal Temp-Mail Gateway</span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex items-center gap-1 pl-4 border-l border-slate-200 dark:border-slate-800">
              <Link
                to="/"
                exact
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  currentPath === '/'
                    ? 'text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                Overview
              </Link>
              <Link
                to="/docs"
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  currentPath.startsWith('/docs') && currentPath !== '/docs/providers'
                    ? 'text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                Docs
              </Link>
              <Link
                to="/docs/providers"
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  currentPath === '/docs/providers'
                    ? 'text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                Providers
              </Link>
              <Link
                to="/analytics"
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  currentPath === '/analytics'
                    ? 'text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 font-semibold'
                    : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                Health & Telemetry
              </Link>

              {/* API Reference Dropdown */}
              <div
                className="relative"
                onMouseEnter={() => setIsApiDropdownOpen(true)}
                onMouseLeave={() => setIsApiDropdownOpen(false)}
              >
                <button
                  onClick={() => setIsApiDropdownOpen((prev) => !prev)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60 transition-colors"
                >
                  <span>API Specs</span>
                  <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${isApiDropdownOpen ? 'rotate-180 text-cyan-500' : ''}`} />
                </button>

                {isApiDropdownOpen && (
                  <div className="absolute top-full left-0 pt-2 w-56 z-50">
                    <div className="rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-700/80 shadow-2xl p-1.5 backdrop-blur-lg">
                      <a
                        href={assetUrl('/scalar.html')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-cyan-600 dark:hover:text-cyan-300 transition-colors"
                      >
                        <span>Scalar API Reference</span>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      </a>
                      <a
                        href={assetUrl('/swagger.html')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-cyan-600 dark:hover:text-cyan-300 transition-colors"
                      >
                        <span>Swagger UI Cyberpunk</span>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      </a>
                      <a
                        href={assetUrl('/redoc.html')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 hover:text-cyan-600 dark:hover:text-cyan-300 transition-colors"
                      >
                        <span>ReDoc Clean Spec</span>
                        <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
                      </a>
                      <div className="my-1 border-t border-slate-100 dark:border-slate-800"></div>
                      <a
                        href={assetUrl('/openapi.json')}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center justify-between px-3 py-2 rounded-lg text-xs font-mono text-cyan-600 dark:text-cyan-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                      >
                        <span>openapi.json</span>
                        <span className="text-[10px] text-slate-400">3.1</span>
                      </a>
                    </div>
                  </div>
                )}
              </div>
            </nav>
          </div>

          {/* Right Action Icons & Controls */}
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Search Trigger Button */}
            <button
              onClick={() => setIsSearchOpen(true)}
              className="flex items-center gap-2 px-3 py-1.5 text-xs text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-slate-900/90 hover:bg-slate-200 dark:hover:bg-slate-800/90 border border-slate-200 dark:border-slate-700/60 rounded-xl transition-all shadow-sm"
              title="Search documentation (⌘K)"
            >
              <Search className="w-3.5 h-3.5 text-slate-400" />
              <span className="hidden sm:inline">Search docs...</span>
              <kbd className="hidden sm:inline-flex items-center px-1.5 py-0.2 text-[10px] bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded font-mono text-slate-500 dark:text-slate-400">
                ⌘K
              </kbd>
            </button>

            {/* GitHub Repo Button */}
            <a
              href="https://github.com/stormsia/maily"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-3 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-200 bg-slate-100 dark:bg-slate-900/80 hover:bg-slate-200 dark:hover:bg-slate-800 border border-slate-200 dark:border-slate-700/60 rounded-xl transition-all shadow-sm"
              aria-label="GitHub Repository"
            >
              <GithubIcon className="w-4 h-4 text-slate-700 dark:text-slate-300" />
              <span className="hidden sm:inline">GitHub</span>
            </a>

            {/* Theme Toggle */}
            <button
              onClick={toggleTheme}
              className="p-2 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/80 border border-transparent hover:border-slate-200 dark:hover:border-slate-700/60 transition-all"
              aria-label="Toggle dark/light theme"
              title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-700" />}
            </button>

            {/* Mobile Hamburger */}
            <button
              onClick={() => setIsMobileNavOpen(true)}
              className="md:hidden p-2 rounded-xl text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
              aria-label="Open mobile navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
          </div>
        </div>
      </header>

      {/* Global Modals */}
      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <MobileNav
        isOpen={isMobileNavOpen}
        onClose={() => setIsMobileNavOpen(false)}
        onOpenSearch={() => setIsSearchOpen(true)}
      />
    </>
  );
};
