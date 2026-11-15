import React, { createContext, useContext, useEffect, useState, useMemo } from 'react';

interface RouterContextType {
  currentPath: string;
  basePath: string;
  navigate: (to: string) => void;
  fullPath: (to: string) => string;
  assetUrl: (to: string) => string;
}

const RouterContext = createContext<RouterContextType>({
  currentPath: '/',
  basePath: '',
  navigate: () => {},
  fullPath: (to: string) => to,
  assetUrl: (to: string) => to,
});

function normalizePath(rawPath: string, basePath: string): string {
  let path = rawPath || '/';

  // Strip trailing hash/query for route matching
  if (path.includes('?')) path = path.split('?')[0];
  if (path.includes('#')) path = path.split('#')[0];

  // Strip basePath if present
  if (basePath && basePath !== '/' && path.startsWith(basePath)) {
    path = path.slice(basePath.length);
  }

  // Strip .html extension if present (e.g. /docs/python.html -> /docs/python)
  if (path.endsWith('.html')) {
    path = path.slice(0, -5);
  }

  // Normalize slashes
  if (!path.startsWith('/')) path = '/' + path;
  if (path.length > 1 && path.endsWith('/')) path = path.slice(0, -1);

  return path || '/';
}

export function cleanBasePath(base: string): string {
  let b = base || '';
  if (b.endsWith('/')) b = b.slice(0, -1);
  return b;
}

interface RouterProviderProps {
  children: React.ReactNode;
  initialPath?: string;
  basePath?: string;
}

export const RouterProvider: React.FC<RouterProviderProps> = ({
  children,
  initialPath,
  basePath: explicitBasePath,
}) => {
  const envBase = typeof import.meta !== 'undefined' && import.meta.env?.BASE_URL ? import.meta.env.BASE_URL : '';
  const basePath = cleanBasePath(explicitBasePath !== undefined ? explicitBasePath : envBase);

  const [currentPath, setCurrentPath] = useState<string>(() => {
    if (initialPath) {
      return normalizePath(initialPath, basePath);
    }
    if (typeof window !== 'undefined') {
      return normalizePath(window.location.pathname, basePath);
    }
    return '/';
  });

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const onPopState = () => {
      setCurrentPath(normalizePath(window.location.pathname, basePath));
    };

    window.addEventListener('popstate', onPopState);
    return () => window.removeEventListener('popstate', onPopState);
  }, [basePath]);

  const navigate = (to: string) => {
    if (typeof window === 'undefined') return;
    const normalized = normalizePath(to, basePath);
    setCurrentPath(normalized);

    const targetUrl = basePath ? `${basePath}${normalized}` : normalized;
    window.history.pushState({}, '', targetUrl);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const assetUrl = (to: string): string => {
    if (!to) return '';
    if (to.startsWith('http://') || to.startsWith('https://') || to.startsWith('mailto:') || to.startsWith('#')) {
      return to;
    }
    const clean = to.startsWith('/') ? to : `/${to}`;
    return basePath ? `${basePath}${clean}` : clean;
  };

  const fullPath = (to: string): string => {
    if (to.startsWith('http://') || to.startsWith('https://') || to.startsWith('#')) {
      return to;
    }
    if (to.endsWith('.html') || to.endsWith('.json') || to.endsWith('.txt') || to.includes('/bench/')) {
      return assetUrl(to);
    }
    const normalized = normalizePath(to, basePath);
    return basePath ? `${basePath}${normalized}` : normalized;
  };

  return (
    <RouterContext.Provider value={{ currentPath, basePath, navigate, fullPath, assetUrl }}>
      {children}
    </RouterContext.Provider>
  );
};

export const useRouter = () => useContext(RouterContext);

interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  to: string;
  activeClassName?: string;
  exact?: boolean;
}

export const Link: React.FC<LinkProps> = ({
  to,
  className = '',
  activeClassName = '',
  exact = false,
  children,
  onClick,
  ...rest
}) => {
  const { currentPath, basePath, navigate, fullPath } = useRouter();

  const isExternal = to.startsWith('http://') || to.startsWith('https://') || to.startsWith('//');
  const isHash = to.startsWith('#');

  const normalizedTarget = isExternal || isHash ? to : normalizePath(to, basePath);
  const isActive = !isExternal && !isHash && (exact ? currentPath === normalizedTarget : currentPath === normalizedTarget || (normalizedTarget !== '/' && currentPath.startsWith(normalizedTarget)));

  const computedClassName = `${className} ${isActive && activeClassName ? activeClassName : ''}`.trim();
  const href = isExternal || isHash ? to : fullPath(to);

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) onClick(e);

    if (
      !isExternal &&
      !isHash &&
      !e.defaultPrevented &&
      e.button === 0 &&
      !e.metaKey &&
      !e.altKey &&
      !e.ctrlKey &&
      !e.shiftKey
    ) {
      e.preventDefault();
      navigate(to);
    }
  };

  return (
    <a href={href} className={computedClassName} onClick={handleClick} {...rest}>
      {children}
    </a>
  );
};
