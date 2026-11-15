import React from 'react';
import { RouterProvider, useRouter } from './context/RouterContext';
import { ThemeProvider } from './context/ThemeContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { HomePage } from './pages/HomePage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { DocsPage } from './pages/DocsPage';
import { NotFoundPage } from './pages/NotFoundPage';

const AppContent: React.FC = () => {
  const { currentPath } = useRouter();

  const renderPage = () => {
    if (currentPath === '/') {
      return <HomePage />;
    }
    if (currentPath === '/analytics') {
      return <AnalyticsPage />;
    }
    if (currentPath === '/docs' || currentPath.startsWith('/docs/')) {
      return <DocsPage />;
    }
    if (currentPath === '/404') {
      return <NotFoundPage />;
    }
    return <NotFoundPage />;
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-50 text-slate-900 dark:bg-[#070b12] dark:text-slate-100 font-sans selection:bg-cyan-500 selection:text-white transition-colors duration-200">
      <Header />
      <div className="flex-1">
        {renderPage()}
      </div>
      <Footer />
    </div>
  );
};

export interface AppProps {
  initialPath?: string;
  basePath?: string;
}

export const App: React.FC<AppProps> = ({ initialPath, basePath }) => {
  return (
    <ThemeProvider>
      <RouterProvider initialPath={initialPath} basePath={basePath}>
        <AppContent />
      </RouterProvider>
    </ThemeProvider>
  );
};

export default App;
