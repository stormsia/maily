import React from 'react';
import { Terminal, ShieldCheck, Heart, Sparkles, BookOpen } from 'lucide-react';
import { GithubIcon } from '../common/Icons';
import { Link, useRouter } from '../../context/RouterContext';

export const Footer: React.FC = () => {
  const { assetUrl } = useRouter();
  return (
    <footer className="w-full border-t border-slate-200 dark:border-slate-800/80 bg-white dark:bg-[#080d17] text-slate-600 dark:text-slate-400 py-12 px-4 sm:px-6 lg:px-8 mt-auto transition-colors">
      <div className="max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-8">
        {/* Brand & Mission */}
        <div className="space-y-4 md:col-span-1">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center font-bold text-white font-mono shadow-md shadow-cyan-500/20">
              M
            </div>
            <span className="font-extrabold text-lg text-slate-900 dark:text-white tracking-tight font-display">Maily</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
            High-performance, self-hosted temporary email gateway aggregating 8+ disposable mail providers into one unified REST API and async Python SDK.
          </p>
          <div className="flex items-center gap-2 pt-2 text-xs text-slate-500 dark:text-slate-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>All upstream systems operational</span>
          </div>
        </div>

        {/* Documentation Columns */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3 font-mono">Documentation</h4>
          <ul className="space-y-2 text-xs">
            <li>
              <Link to="/docs" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Getting Started</Link>
            </li>
            <li>
              <Link to="/docs/python" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Python SDK (maily)</Link>
            </li>
            <li>
              <Link to="/docs/curl" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">cURL & REST API</Link>
            </li>
            <li>
              <Link to="/docs/docker" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Docker Self-Hosting</Link>
            </li>
            <li>
              <Link to="/docs/recipes" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Testing Recipes & OTP</Link>
            </li>
            <li>
              <Link to="/docs/architecture" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Architecture & Resilience</Link>
            </li>
          </ul>
        </div>

        {/* Providers & Analytics */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3 font-mono">Capabilities</h4>
          <ul className="space-y-2 text-xs">
            <li>
              <Link to="/docs/providers" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Provider Matrix & SLAs</Link>
            </li>
            <li>
              <Link to="/docs/adding-providers" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Adding Custom Providers</Link>
            </li>
            <li>
              <Link to="/analytics" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">Live Health Analytics</Link>
            </li>
            <li>
              <a href={assetUrl('/dev/bench/')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                Performance Benchmarks ↗
              </a>
            </li>
            <li>
              <a href={assetUrl('/scalar.html')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                Scalar API Reference ↗
              </a>
            </li>
            <li>
              <a href={assetUrl('/swagger.html')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                Swagger UI Cyberpunk ↗
              </a>
            </li>
          </ul>
        </div>

        {/* AI Discovery & Community */}
        <div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-900 dark:text-slate-200 mb-3 font-mono">AI & Standards</h4>
          <ul className="space-y-2 text-xs font-mono">
            <li>
              <a href={assetUrl('/openapi.json')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                openapi.json
              </a>
            </li>
            <li>
              <a href={assetUrl('/llms.txt')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                llms.txt
              </a>
            </li>
            <li>
              <a href={assetUrl('/llms-full.txt')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                llms-full.txt
              </a>
            </li>
            <li>
              <a href={assetUrl('/ai-catalog.json')} target="_blank" rel="noopener noreferrer" className="hover:text-cyan-600 dark:hover:text-cyan-400 transition-colors">
                ai-catalog.json
              </a>
            </li>
            <li className="pt-2">
              <a href="https://github.com/stormsia/maily" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1.5 text-slate-700 dark:text-slate-300 hover:text-black dark:hover:text-white font-sans text-xs">
                <GithubIcon className="w-3.5 h-3.5" />
                <span>GitHub Repository</span>
              </a>
            </li>
          </ul>
        </div>
      </div>

      <div className="max-w-7xl mx-auto pt-8 mt-8 border-t border-slate-200 dark:border-slate-800/80 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 dark:text-slate-400 gap-4">
        <div>
          <span>© {new Date().getFullYear()} Maily. Released under the MIT License. Built for developers & QA engineers.</span>
        </div>
        <div className="flex items-center gap-4">
          <a href="https://pypi.org/project/maily/" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 dark:hover:text-slate-300">
            PyPI (maily)
          </a>
          <span>·</span>
          <a href="https://ghcr.io/stormsia/maily" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 dark:hover:text-slate-300">
            GHCR Container
          </a>
          <span>·</span>
          <a href="https://github.com/stormsia/maily/blob/main/SECURITY.md" target="_blank" rel="noopener noreferrer" className="hover:text-slate-900 dark:hover:text-slate-300">
            Security Policy
          </a>
        </div>
      </div>
    </footer>
  );
};
