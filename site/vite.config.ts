import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import path from 'path';
import fs from 'fs';

function serveRootPublicPlugin() {
  const handler = (req: any, res: any, next: any) => {
    if (!req.url) return next();
    const rawUrl = req.url.split('?')[0].split('#')[0];
    const urlPath = rawUrl.replace(/^\/maily/, '');

    // Skip Vite internals and root index
    if (
      urlPath.startsWith('/@') ||
      urlPath.startsWith('/src/') ||
      urlPath.startsWith('/node_modules/') ||
      urlPath === '/' ||
      urlPath === '/index.html'
    ) {
      return next();
    }

    const publicDir = path.resolve(__dirname, '../public');
    let candidate = path.join(publicDir, urlPath.replace(/^\//, ''));

    // If directory, serve its index.html (e.g. /dev/bench/ -> /dev/bench/index.html)
    if (fs.existsSync(candidate) && fs.statSync(candidate).isDirectory()) {
      const idx = path.join(candidate, 'index.html');
      if (fs.existsSync(idx)) {
        candidate = idx;
      }
    }

    if (fs.existsSync(candidate) && fs.statSync(candidate).isFile()) {
      const ext = path.extname(candidate).toLowerCase();
      const mimeTypes: Record<string, string> = {
        '.html': 'text/html; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.json': 'application/json; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.txt': 'text/plain; charset=utf-8',
        '.xml': 'application/xml; charset=utf-8',
      };
      res.setHeader('Content-Type', mimeTypes[ext] || 'application/octet-stream');
      fs.createReadStream(candidate).pipe(res);
      return;
    }

    next();
  };

  return {
    name: 'serve-root-public',
    configureServer(server: any) {
      server.middlewares.use(handler);
    },
    configurePreviewServer(server: any) {
      server.middlewares.use(handler);
    },
  };
}

export default defineConfig({
  base: process.env.VITE_BASE || (process.env.NODE_ENV === 'development' ? '/' : '/maily/'),
  plugins: [
    react(),
    tailwindcss(),
    serveRootPublicPlugin(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
  },
});
