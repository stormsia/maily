import React from 'react';
import { useRouter } from '../context/RouterContext';
import { DocsLayout } from '../components/layout/DocsLayout';
import { ROUTES } from '../data/routes';
import { DocsGettingStarted } from './docs/DocsGettingStarted';
import { DocsPython } from './docs/DocsPython';
import { DocsCurl } from './docs/DocsCurl';
import { DocsDocker } from './docs/DocsDocker';
import { DocsProviders } from './docs/DocsProviders';
import { DocsAddingProviders } from './docs/DocsAddingProviders';
import { DocsRecipes } from './docs/DocsRecipes';
import { DocsArchitecture } from './docs/DocsArchitecture';

export const DocsPage: React.FC = () => {
  const { currentPath } = useRouter();

  const routeInfo = ROUTES[currentPath] || ROUTES['/docs'];

  const renderContent = () => {
    switch (currentPath) {
      case '/docs/python':
        return <DocsPython />;
      case '/docs/curl':
        return <DocsCurl />;
      case '/docs/docker':
        return <DocsDocker />;
      case '/docs/providers':
        return <DocsProviders />;
      case '/docs/adding-providers':
        return <DocsAddingProviders />;
      case '/docs/recipes':
        return <DocsRecipes />;
      case '/docs/architecture':
        return <DocsArchitecture />;
      case '/docs':
      default:
        return <DocsGettingStarted />;
    }
  };

  return (
    <DocsLayout
      title={routeInfo.navTitle || routeInfo.title}
      description={routeInfo.description}
    >
      {renderContent()}
    </DocsLayout>
  );
};
