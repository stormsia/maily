import React from 'react';
import { renderToString } from 'react-dom/server';
import App from './App';

export interface RenderResult {
  html: string;
}

export function render(url: string, basePath?: string): RenderResult {
  const html = renderToString(<App initialPath={url} basePath={basePath} />);
  return { html };
}
