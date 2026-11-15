import React, { useState, useEffect } from 'react';
import { ChevronRight, ChevronLeft, BookOpen, ExternalLink, Menu, X, Hash } from 'lucide-react';
import { Link, useRouter } from '../../context/RouterContext';
import { DOCS_NAV_SECTIONS, ROUTES } from '../../data/routes';

interface TocItem {
  id: string;
  title: string;
  level: number;
}

interface DocsLayoutProps {
  children: React.ReactNode;
  toc?: TocItem[];
  title: string;
  description: string;
}

export const DocsLayout: React.FC<DocsLayoutProps> = ({
  children,
  toc = [],
  title,
  description,
}) => {
  const { currentPath, assetUrl } = useRouter();
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [activeHeadingId, setActiveHeadingId] = useState<string>('');

  // Active anchor scroll-spy
  useEffect(() => {
    if (typeof window === 'undefined' || toc.length === 0) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveHeadingId(entry.target.id);
          }
        });
      },
      { rootMargin: '-80px 0px -70% 0px' }
    );

    toc.forEach((item) => {
      const el = document.getElementById(item.id);
      if (el) observer.observe(el);
    });

    return () => observer.disconnect();
  }, [toc]);

  // Flatten all navigable doc items for prev/next calculation
  const allDocItems = DOCS_NAV_SECTIONS.flatMap((sec) =>
    sec.items.filter((item) => !item.external)
  );
  const currentIndex = allDocItems.findIndex((item) => item.path === currentPath);
  const prevDoc = currentIndex > 0 ? allDocItems[currentIndex - 1] : null;
  const nextDoc = currentIndex >= 0 && currentIndex < allDocItems.length - 1 ? allDocItems[currentIndex + 1] : null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex gap-8">
      {/* Mobile Backdrop Overlay */}
      {isSidebarOpen && (
        <div
          className="fixed inset-0 z-20 bg-slate-950/60 backdrop-blur-sm lg:hidden transition-opacity"
          onClick={() => setIsSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Sidebar Toggle Button */}
      <div className="lg:hidden fixed bottom-6 right-6 z-40">
        <button
          onClick={() => setIsSidebarOpen((prev) => !prev)}
          className="p-3 bg-cyan-600 text-white rounded-full shadow-lg shadow-cyan-600/30 hover:bg-cyan-500 transition-colors flex items-center justify-center"
          aria-label="Toggle docs navigation"
        >
          {isSidebarOpen ? <X className="w-5 h-5" /> : <BookOpen className="w-5 h-5" />}
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-72 bg-white/95 dark:bg-slate-900/95 lg:bg-transparent dark:lg:bg-transparent backdrop-blur-md lg:backdrop-blur-none border-r border-slate-200 dark:border-slate-800 p-6 lg:p-0 lg:static lg:block shrink-0 transition-transform lg:translate-x-0 ${
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="sticky top-24 space-y-6 max-h-[calc(100vh-8rem)] overflow-y-auto pr-3">
          <div className="flex items-center justify-between lg:hidden pb-3 border-b border-slate-200 dark:border-slate-800">
            <span className="font-semibold text-slate-900 dark:text-slate-200">Documentation</span>
            <button onClick={() => setIsSidebarOpen(false)} className="text-slate-400">
              <X className="w-5 h-5" />
            </button>
          </div>

          {DOCS_NAV_SECTIONS.map((section) => (
            <div key={section.title} className="space-y-2">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 px-2 font-mono">
                {section.title}
              </h3>
              <ul className="space-y-1">
                {section.items.map((item) => {
                  const isActive = currentPath === item.path;
                  return (
                    <li key={item.path}>
                      {item.external ? (
                        <a
                          href={assetUrl(item.path)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center justify-between px-3 py-1.5 text-xs text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/50 rounded-lg transition-colors"
                        >
                          <span>{item.title.replace(' ↗', '')}</span>
                          <ExternalLink className="w-3 h-3 text-slate-400" />
                        </a>
                      ) : (
                        <Link
                          to={item.path}
                          onClick={() => setIsSidebarOpen(false)}
                          className={`block px-3 py-1.5 text-xs rounded-lg transition-colors ${
                            isActive
                              ? 'bg-cyan-50 dark:bg-cyan-500/15 text-cyan-700 dark:text-cyan-400 font-semibold border-l-2 border-cyan-500 pl-2.5'
                              : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800/40'
                          }`}
                        >
                          {item.title}
                        </Link>
                      )}
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Documentation Article Content */}
      <main className="flex-1 min-w-0 max-w-4xl py-2">
        {/* Breadcrumbs */}
        <nav className="flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400 mb-6 font-mono">
          <Link to="/" className="hover:text-cyan-600 dark:hover:text-cyan-400">Home</Link>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <Link to="/docs" className="hover:text-cyan-600 dark:hover:text-cyan-400">Docs</Link>
          <ChevronRight className="w-3 h-3 text-slate-400" />
          <span className="text-slate-800 dark:text-slate-300 font-medium truncate">{title}</span>
        </nav>

        {/* Header Title & Intro */}
        <div className="mb-8 pb-6 border-b border-slate-200 dark:border-slate-800">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 dark:text-white tracking-tight font-display mb-3">
            {title}
          </h1>
          <p className="text-base text-slate-600 dark:text-slate-400 leading-relaxed">
            {description}
          </p>
        </div>

        {/* Content Body */}
        <article className="prose prose-slate dark:prose-invert max-w-none space-y-6 text-slate-700 dark:text-slate-300">
          {children}
        </article>

        {/* Next / Previous Pagination */}
        <div className="mt-12 pt-6 border-t border-slate-200 dark:border-slate-800 grid grid-cols-1 sm:grid-cols-2 gap-4">
          {prevDoc ? (
            <Link
              to={prevDoc.path}
              className="group p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900/40 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all flex flex-col items-start gap-1 shadow-sm"
            >
              <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 font-mono">
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </div>
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-white">
                {prevDoc.title}
              </span>
            </Link>
          ) : (
            <div />
          )}

          {nextDoc && (
            <Link
              to={nextDoc.path}
              className="group p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-slate-300 dark:hover:border-slate-700 bg-white dark:bg-slate-900/40 hover:bg-slate-50 dark:hover:bg-slate-900 transition-all flex flex-col items-end gap-1 text-right sm:col-start-2 shadow-sm"
            >
              <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 font-mono">
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </div>
              <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 group-hover:text-slate-900 dark:group-hover:text-white">
                {nextDoc.title}
              </span>
            </Link>
          )}
        </div>
      </main>

      {/* Right Table of Contents (TOC) with Active Anchor Highlighting */}
      {toc.length > 0 && (
        <aside className="hidden xl:block w-56 shrink-0">
          <div className="sticky top-24 space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-mono">
              On This Page
            </h4>
            <ul className="space-y-1.5 text-xs">
              {toc.map((item) => {
                const isActive = activeHeadingId === item.id;
                return (
                  <li key={item.id} style={{ paddingLeft: `${(item.level - 2) * 12}px` }}>
                    <a
                      href={`#${item.id}`}
                      className={`line-clamp-1 block py-0.5 transition-colors ${
                        isActive
                          ? 'text-cyan-600 dark:text-cyan-400 font-semibold pl-1.5 border-l border-cyan-500'
                          : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                      }`}
                    >
                      {item.title}
                    </a>
                  </li>
                );
              })}
            </ul>
          </div>
        </aside>
      )}
    </div>
  );
};
