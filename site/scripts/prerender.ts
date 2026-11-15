import fs from 'fs';
import path from 'path';
import { fileURLToPath, pathToFileURL } from 'url';
import { ROUTES, RouteItem, SITE_URL } from '../src/data/routes';
import { APP_VERSION } from '../src/data/version';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const SITE_ROOT = path.resolve(__dirname, '..');
const REPO_ROOT = path.resolve(SITE_ROOT, '..');
const CLIENT_DIST = path.resolve(SITE_ROOT, 'dist/client');
const SERVER_DIST = path.resolve(SITE_ROOT, 'dist/server');
const PUBLIC_DIR = path.resolve(REPO_ROOT, 'public');

function copyDirRecursive(src: string, dest: string) {
  if (!fs.existsSync(src)) return;
  if (!fs.existsSync(dest)) fs.mkdirSync(dest, { recursive: true });

  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirRecursive(srcPath, destPath);
    } else {
      try {
        if (fs.existsSync(destPath)) {
          const sStat = fs.statSync(srcPath);
          const dStat = fs.statSync(destPath);
          if (sStat.size === dStat.size) {
            continue;
          }
        }
        fs.copyFileSync(srcPath, destPath);
      } catch (err) {
        if (!fs.existsSync(destPath)) {
          throw err;
        }
      }
    }
  }
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function generateJsonLd(route: RouteItem): any {
  const website = {
    '@type': 'WebSite',
    '@id': `${SITE_URL}/#website`,
    url: `${SITE_URL}/`,
    name: 'Maily',
    alternateName: 'Maily Temp-Mail Gateway Portal',
    description: 'Developer Portal and Documentation Hub for Maily: Universal Temporary Email Gateway & Async Python SDK',
    inLanguage: 'en',
    publisher: { '@id': `${SITE_URL}/#organization` },
  };

  const org = {
    '@type': 'Organization',
    '@id': `${SITE_URL}/#organization`,
    name: 'Maily Project',
    url: `${SITE_URL}/`,
    logo: {
      '@type': 'ImageObject',
      '@id': `${SITE_URL}/#logo`,
      url: `${SITE_URL}/assets/logo.png`,
      contentUrl: `${SITE_URL}/assets/logo.png`,
      width: 474,
      height: 432,
      caption: 'Maily Project Logo',
    },
    sameAs: ['https://github.com/stormsia/maily'],
  };

  const software = {
    '@type': 'SoftwareApplication',
    '@id': `${SITE_URL}/#software`,
    name: 'Maily',
    alternateName: [
      'Maily Gateway',
      'Universal Temp-Mail Gateway',
      'maily-server',
      'maily-client',
    ],
    headline: 'Universal Temporary Email Gateway & Developer Hub',
    description: 'Universal temporary email gateway aggregating 8+ disposable mail providers into one unified REST API and async Python SDK with sub-second OTP extraction for Playwright and QA bots.',
    url: `${SITE_URL}/`,
    applicationCategory: 'DeveloperApplication',
    operatingSystem: 'Docker, Linux, macOS, Windows, Python 3.10+',
    softwareVersion: APP_VERSION,
    license: 'https://opensource.org/licenses/MIT',
    image: `${SITE_URL}/assets/hero_banner.png`,
    screenshot: `${SITE_URL}/screenshots/01_overview.webp`,
    releaseNotes: 'https://github.com/stormsia/maily/releases',
    softwareHelp: `${SITE_URL}/docs`,
    downloadUrl: 'https://pypi.org/project/maily-client/',
    installUrl: 'https://github.com/stormsia/maily#quick-start',
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
      availability: 'https://schema.org/OnlineOnly',
    },
    featureList: [
      'Aggregates 8+ disposable email providers (Mail.tm, TempMail.Plus, NoopMail, GuerrillaMail, etc.)',
      'Sub-millisecond hermetic SQLite WAL storage (< 2.5 ms latencies)',
      'Automatic 1-line OTP verification code extraction (wait_for_code)',
      '40+ rotating domains across networks to bypass anti-tempmail blocklists',
      '100% typed async Python SDK (maily-client) with strict Pydantic schemas',
      'Zero outbound SMTP (inbound-only architecture prevents spam relay risks)',
      'Hermetic self-hosted Docker container (ghcr.io/stormsia/maily)',
    ],
    isPartOf: { '@id': `${SITE_URL}/#website` },
    author: { '@id': `${SITE_URL}/#organization` },
    publisher: { '@id': `${SITE_URL}/#organization` },
  };

  const webApi = {
    '@type': 'WebAPI',
    '@id': `${SITE_URL}/#webapi`,
    name: 'Maily Gateway REST API',
    description: 'Normalized REST API aggregating multiple disposable email providers with mailbox lifecycle management and OTP polling.',
    documentation: `${SITE_URL}/scalar.html`,
    serviceUrl: 'http://127.0.0.1:8477',
    termsOfService: 'https://github.com/stormsia/maily/blob/main/LICENSE',
    about: { '@id': `${SITE_URL}/#software` },
    provider: { '@id': `${SITE_URL}/#organization` },
  };

  const graph: any[] = [website, org, software, webApi];

  // Breadcrumbs
  if (route.path !== '/' && route.path !== '/404') {
    const breadcrumbItems = [
      {
        '@type': 'ListItem',
        position: 1,
        name: 'Home',
        item: `${SITE_URL}/`,
      },
    ];

    if (route.path.startsWith('/docs')) {
      breadcrumbItems.push({
        '@type': 'ListItem',
        position: 2,
        name: 'Documentation',
        item: `${SITE_URL}/docs`,
      });
      if (route.path !== '/docs') {
        breadcrumbItems.push({
          '@type': 'ListItem',
          position: 3,
          name: route.navTitle || route.title,
          item: route.canonical,
        });
      }
    } else {
      breadcrumbItems.push({
        '@type': 'ListItem',
        position: 2,
        name: route.navTitle || route.title,
        item: route.canonical,
      });
    }

    graph.push({
      '@type': 'BreadcrumbList',
      '@id': `${route.canonical}#breadcrumb`,
      itemListElement: breadcrumbItems,
    });
  }

  // TechArticle for guides and advanced documentation
  if (route.category === 'guide' || route.category === 'advanced') {
    graph.push({
      '@type': 'TechArticle',
      '@id': `${route.canonical}#article`,
      headline: route.title,
      description: route.description,
      url: route.canonical,
      inLanguage: 'en',
      datePublished: '2026-11-06T00:00:00Z',
      dateModified: '2026-11-15T00:00:00Z',
      isPartOf: { '@id': `${SITE_URL}/#website` },
      author: { '@id': `${SITE_URL}/#organization` },
      publisher: { '@id': `${SITE_URL}/#organization` },
      about: { '@id': `${SITE_URL}/#software` },
    });
  }

  // FAQPage if route has FAQs defined
  if (route.faqs && route.faqs.length > 0) {
    graph.push({
      '@type': 'FAQPage',
      '@id': `${route.canonical}#faq`,
      mainEntityOfPage: { '@id': route.canonical },
      about: { '@id': `${SITE_URL}/#software` },
      mainEntity: route.faqs.map((f) => ({
        '@type': 'Question',
        name: f.question,
        acceptedAnswer: {
          '@type': 'Answer',
          text: f.answer,
        },
      })),
    });
  }

  return {
    '@context': 'https://schema.org',
    '@graph': graph,
  };
}

function generateSitemapXml(routes: RouteItem[]): string {
  const today = new Date().toISOString().split('T')[0];
  const urlEntries = routes
    .filter((r) => r.path !== '/404')
    .map((r) => {
      const priority = r.path === '/' ? '1.0' : r.path === '/docs' ? '0.9' : '0.8';
      const changefreq = r.path === '/' || r.path === '/analytics' ? 'daily' : 'weekly';
      return `  <url>
    <loc>${r.canonical}</loc>
    <lastmod>${today}</lastmod>
    <changefreq>${changefreq}</changefreq>
    <priority>${priority}</priority>
  </url>`;
    });

  // Also include API references and benchmarks in sitemap
  urlEntries.push(`  <url>
    <loc>${SITE_URL}/scalar.html</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`);
  urlEntries.push(`  <url>
    <loc>${SITE_URL}/swagger.html</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`);
  urlEntries.push(`  <url>
    <loc>${SITE_URL}/redoc.html</loc>
    <lastmod>${today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>`);
  urlEntries.push(`  <url>
    <loc>${SITE_URL}/dev/bench/</loc>
    <lastmod>${today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>`);

  return `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${urlEntries.join('\n')}
</urlset>`;
}

function generateArdManifestJson(): object {
  const entries = [
    {
      identifier: 'urn:air:stormsia.github.io:maily:openapi',
      displayName: 'OpenAPI 3.1 REST API Specification',
      type: 'application/vnd.oai.openapi+json',
      url: `${SITE_URL}/openapi.json`,
      description: 'Full machine-readable OpenAPI 3.1 REST API specification for temporary email management and OTP code polling.',
      representativeQueries: [
        'OpenAPI specification for temporary email',
        'Maily REST API schema 3.1',
        'Disposable email swagger openapi json'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:skill',
      displayName: 'Agent Testing Skill Manifest',
      type: 'text/markdown',
      url: `${SITE_URL}/SKILL.md`,
      description: 'Agent skill for automated Playwright and Pytest OTP verification with Maily.',
      representativeQueries: [
        'Agent skill for temporary email testing',
        'Playwright disposable mailbox fixtures',
        'Pytest email OTP verification skill'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:llms-full',
      displayName: 'Consolidated Agent Documentation (llms-full.txt)',
      type: 'text/plain',
      url: `${SITE_URL}/llms-full.txt`,
      description: 'Complete consolidated documentation for single-request ingestion and LLM grounding.',
      representativeQueries: [
        'Complete Maily documentation in single text file',
        'Full llms-full.txt for temporary email API',
        'LLM context ingestion for Maily'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:llms',
      displayName: 'Curated Machine Index (llms.txt)',
      type: 'text/plain',
      url: `${SITE_URL}/llms.txt`,
      description: 'Curated machine-readable overview of Maily architecture, features, and endpoints.',
      representativeQueries: [
        'llms.txt for disposable email gateway',
        'Machine index of Maily temporary email'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:pricing',
      displayName: 'Pricing & Licensing Declaration',
      type: 'text/markdown',
      url: `${SITE_URL}/pricing.md`,
      description: '$0 FOSS MIT license declaration and unlimited self-hosted usage limits.',
      representativeQueries: [
        'Maily pricing and licensing',
        'Is Maily temporary email free and open source?',
        'Self-hosted temporary mail gateway license'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:docs',
      displayName: 'Developer Documentation Hub',
      type: 'text/html',
      url: `${SITE_URL}/docs`,
      description: 'Comprehensive developer documentation, architecture overview, and quickstarts.',
      representativeQueries: [
        'Maily developer documentation hub',
        'Quickstart guide for temporary email gateway'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:python-sdk',
      displayName: 'Python Async SDK Guide',
      type: 'text/html',
      url: `${SITE_URL}/docs/python`,
      description: 'Developer guide for maily-client: Pydantic v2 schemas, async context managers, and OTP helpers.',
      representativeQueries: [
        'Python async SDK for temporary email',
        'maily-client guide and Pydantic models',
        'Extract verification code in Python async'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:curl',
      displayName: 'cURL & Universal REST API',
      type: 'text/html',
      url: `${SITE_URL}/docs/curl`,
      description: 'HTTP/1.1 REST endpoints, authentication headers, SSE message streaming, and examples.',
      representativeQueries: [
        'cURL commands for disposable email API',
        'REST endpoints for creating temporary mailbox'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:docker',
      displayName: 'Docker & Self-Hosting Guide',
      type: 'text/html',
      url: `${SITE_URL}/docs/docker`,
      description: 'Hermetic self-hosted Docker deployment, Compose specification, and SQLite WAL volumes.',
      representativeQueries: [
        'Docker compose self-hosted temporary email',
        'Run disposable email gateway in docker'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:providers',
      displayName: 'Provider Capabilities Matrix',
      type: 'text/html',
      url: `${SITE_URL}/docs/providers`,
      description: 'Unified provider fleet matrix, domain rotation pool, and attachment capabilities.',
      representativeQueries: [
        'Disposable email provider capability matrix',
        'Mailtm and tempmail alternative comparison'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:recipes',
      displayName: 'Playwright & Pytest Testing Recipes',
      type: 'text/html',
      url: `${SITE_URL}/docs/recipes`,
      description: 'Complete Playwright, Cypress, and Pytest automation fixtures and OTP extraction recipes.',
      representativeQueries: [
        'Playwright email verification testing recipe',
        'Pytest fixture for OTP code extraction'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:architecture',
      displayName: 'Security Architecture & Threat Model',
      type: 'text/html',
      url: `${SITE_URL}/docs/architecture`,
      description: 'Inbound-only architecture, Fernet-256 token cryptography, and SQLite WAL design.',
      representativeQueries: [
        'Maily security architecture and threat model',
        'Inbound-only email gateway security'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:analytics',
      displayName: 'Security & Provider Health Telemetry',
      type: 'text/html',
      url: `${SITE_URL}/analytics`,
      description: 'Live SLA and availability monitoring for upstream disposable email providers.',
      representativeQueries: [
        'Provider health and SLA monitoring',
        'Disposable email service uptime telemetry'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:benchmarks',
      displayName: 'Continuous Performance Benchmarks Portal',
      type: 'text/html',
      url: `${SITE_URL}/dev/bench/`,
      description: 'Microsecond SQLite WAL and cryptographic execution benchmarks history.',
      representativeQueries: [
        'Maily SQLite WAL write latency benchmarks',
        'Performance benchmarks for temp mail API'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:scalar',
      displayName: 'Scalar Interactive API Reference',
      type: 'text/html',
      url: `${SITE_URL}/scalar.html`,
      description: 'Canonical interactive API reference and OpenAPI playground.',
      representativeQueries: [
        'Scalar interactive API reference Maily',
        'Test temporary email API in browser'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:swagger',
      displayName: 'Swagger UI Cyberpunk Explorer',
      type: 'text/html',
      url: `${SITE_URL}/swagger.html`,
      description: 'Interactive Swagger UI documentation sandbox.',
      representativeQueries: [
        'Swagger UI Maily API explorer'
      ]
    },
    {
      identifier: 'urn:air:stormsia.github.io:maily:redoc',
      displayName: 'ReDoc Clean API Specification',
      type: 'text/html',
      url: `${SITE_URL}/redoc.html`,
      description: 'Responsive clean ReDoc API specification.',
      representativeQueries: [
        'ReDoc documentation for Maily'
      ]
    }
  ];

  return {
    $schema: 'https://agenticresourcediscovery.org/schemas/v1/manifest.json',
    name: 'Maily',
    version: APP_VERSION,
    description: 'Universal temporary email gateway aggregating 8+ disposable mail providers into one unified REST API and async Python SDK with sub-second OTP extraction.',
    homepage: `${SITE_URL}/`,
    documentation: `${SITE_URL}/llms-full.txt`,
    entries,
    resources: entries.map((e) => ({
      name: e.displayName,
      type: e.type,
      url: e.url,
      description: e.description
    }))
  };
}

async function prerender() {
  console.log('[SSG] Starting Static Site Generation Prerender...');

  const templatePath = path.resolve(CLIENT_DIST, 'index.html');
  if (!fs.existsSync(templatePath)) {
    throw new Error(`Client build template not found at ${templatePath}`);
  }
  const rawTemplate = fs.readFileSync(templatePath, 'utf-8');

  // Load server entry
  const serverEntryPath = path.resolve(SERVER_DIST, 'entry-server.js');
  if (!fs.existsSync(serverEntryPath)) {
    throw new Error(`Server build entry not found at ${serverEntryPath}`);
  }
  const { render } = await import(pathToFileURL(serverEntryPath).href);

  // Determine base path
  const basePath = process.env.VITE_BASE || (process.env.NODE_ENV === 'development' ? '' : '/maily');
  const cleanBase = basePath.endsWith('/') ? basePath.slice(0, -1) : basePath;

  // Ensure public directory exists
  if (!fs.existsSync(PUBLIC_DIR)) {
    fs.mkdirSync(PUBLIC_DIR, { recursive: true });
  }

  // Prerender each route
  const routesList = Object.values(ROUTES);
  console.log(`[SSG] Prerendering ${routesList.length} routes...`);

  for (const route of routesList) {
    console.log(`[SSG]   Rendering: ${route.path} -> ${route.title}`);
    const { html: appHtml } = render(route.path, cleanBase);

    const jsonLd = generateJsonLd(route);
    const jsonLdScript = `\n    <script type="application/ld+json">\n${JSON.stringify(jsonLd, null, 2)}\n    </script>`;

    const keywordsTag = route.keywords && route.keywords.length > 0
      ? `\n    <meta name="keywords" content="${escapeHtml(route.keywords.join(', '))}" />`
      : '';

    const robotsDirective = route.path === '/404'
      ? 'noindex, nofollow'
      : 'index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1';

    const headTags = [
      `<title>${escapeHtml(route.title)}</title>`,
      `<meta name="description" content="${escapeHtml(route.description)}" />${keywordsTag}`,
      `<meta name="robots" content="${robotsDirective}" />`,
      `<link rel="canonical" href="${route.canonical}" />`,
      `<meta property="og:title" content="${escapeHtml(route.title)}" />`,
      `<meta property="og:description" content="${escapeHtml(route.description)}" />`,
      `<meta property="og:url" content="${route.canonical}" />`,
      `<meta property="og:image" content="${SITE_URL}/assets/hero_banner.png" />`,
      `<meta property="og:image:width" content="1200" />`,
      `<meta property="og:image:height" content="630" />`,
      `<meta property="og:type" content="${route.ogType || 'website'}" />`,
      `<meta property="og:site_name" content="Maily" />`,
      `<meta property="og:locale" content="en_US" />`,
      `<meta name="twitter:card" content="summary_large_image" />`,
      `<meta name="twitter:title" content="${escapeHtml(route.title)}" />`,
      `<meta name="twitter:description" content="${escapeHtml(route.description)}" />`,
      `<meta name="twitter:image" content="${SITE_URL}/assets/hero_banner.png" />`,
      `<meta name="twitter:site" content="@stormsia" />`,
      `<meta name="twitter:creator" content="@stormsia" />`,
      `<link rel="service-desc" type="application/vnd.oai.openapi+json" href="${cleanBase}/openapi.json" />`,
      `<link rel="alternate" type="text/plain" href="${cleanBase}/llms.txt" title="LLMs.txt" />`,
      `<link rel="alternate" type="text/plain" href="${cleanBase}/llms-full.txt" title="LLMs-full.txt" />`,
      `<link rel="ard" type="application/json" href="${cleanBase}/.well-known/ard.json" title="Agentic Resource Discovery" />`,
      `<link rel="ard" type="application/json" href="${cleanBase}/ard.json" title="Agentic Resource Discovery" />`,
      `<link rel="ai-catalog" type="application/json" href="${cleanBase}/.well-known/ai-catalog.json" />`,
      `<link rel="ai-catalog" type="application/json" href="${cleanBase}/ai-catalog.json" />`,
      `<link rel="help" type="text/markdown" href="${cleanBase}/SKILL.md" title="Agent Testing Skill" />`,
      `<link rel="agent-skill" type="text/markdown" href="${cleanBase}/SKILL.md" title="Agent Testing Skill" />`,
      `<link rel="sitemap" type="application/xml" href="${SITE_URL}/sitemap.xml" />`,
      jsonLdScript,
    ].join('\n    ');

    let outputHtml = rawTemplate;

    // Inject Head
    if (outputHtml.includes('<!-- INJECT_HEAD -->')) {
      outputHtml = outputHtml.replace('<!-- INJECT_HEAD -->', headTags);
    } else {
      outputHtml = outputHtml.replace('</head>', `    ${headTags}\n  </head>`);
    }

    // Inject App HTML
    if (outputHtml.includes('<!-- INJECT_APP -->')) {
      outputHtml = outputHtml.replace('<!-- INJECT_APP -->', appHtml);
    } else if (outputHtml.includes('<div id="root"></div>')) {
      outputHtml = outputHtml.replace('<div id="root"></div>', `<div id="root">${appHtml}</div>`);
    }

    // Determine output file paths
    if (route.path === '/') {
      fs.writeFileSync(path.resolve(PUBLIC_DIR, 'index.html'), outputHtml, 'utf-8');
    } else if (route.path === '/404') {
      fs.writeFileSync(path.resolve(PUBLIC_DIR, '404.html'), outputHtml, 'utf-8');
    } else {
      const relPath = route.path.startsWith('/') ? route.path.slice(1) : route.path;

      // 1. Direct html file: public/analytics.html or public/docs/python.html
      const directHtmlPath = path.resolve(PUBLIC_DIR, `${relPath}.html`);
      fs.mkdirSync(path.dirname(directHtmlPath), { recursive: true });
      fs.writeFileSync(directHtmlPath, outputHtml, 'utf-8');

      // 2. Directory index file: public/analytics/index.html or public/docs/python/index.html
      const dirIndexPath = path.resolve(PUBLIC_DIR, relPath, 'index.html');
      fs.mkdirSync(path.dirname(dirIndexPath), { recursive: true });
      fs.writeFileSync(dirIndexPath, outputHtml, 'utf-8');
    }
  }

  // Copy static files from site/public to public/
  const sitePublicDir = path.resolve(SITE_ROOT, 'public');
  if (fs.existsSync(sitePublicDir)) {
    console.log('[SSG] Syncing site/public to public/...');
    copyDirRecursive(sitePublicDir, PUBLIC_DIR);
  }

  // Copy built client assets (JS/CSS) to public/assets
  const clientAssetsDir = path.resolve(CLIENT_DIST, 'assets');
  const publicAssetsDir = path.resolve(PUBLIC_DIR, 'assets');
  if (fs.existsSync(clientAssetsDir)) {
    console.log('[SSG] Copying built assets to public/assets/...');
    copyDirRecursive(clientAssetsDir, publicAssetsDir);
  }

  // Copy docs/assets/* to public/assets/*
  const docsAssetsDir = path.resolve(REPO_ROOT, 'docs/assets');
  if (fs.existsSync(docsAssetsDir)) {
    console.log('[SSG] Syncing docs/assets to public/assets/...');
    copyDirRecursive(docsAssetsDir, publicAssetsDir);
  }

  // Copy docs/screenshots/* to public/screenshots/*
  const docsScreenshotsDir = path.resolve(REPO_ROOT, 'docs/screenshots');
  const publicScreenshotsDir = path.resolve(PUBLIC_DIR, 'screenshots');
  if (fs.existsSync(docsScreenshotsDir)) {
    console.log('[SSG] Syncing docs/screenshots to public/screenshots/...');
    copyDirRecursive(docsScreenshotsDir, publicScreenshotsDir);
  }

  // Copy provider_health_state.json
  const providerStateSrc = path.resolve(REPO_ROOT, '.github/provider_health_state.json');
  if (fs.existsSync(providerStateSrc)) {
    fs.copyFileSync(providerStateSrc, path.resolve(PUBLIC_DIR, 'provider_health_state.json'));
    fs.copyFileSync(providerStateSrc, path.resolve(PUBLIC_DIR, 'assets/provider_health.json'));
    console.log('[SSG] Copied provider_health_state.json');
  }

  // Ensure .nojekyll exists
  fs.writeFileSync(path.resolve(PUBLIC_DIR, '.nojekyll'), '', 'utf-8');

  // Generate clean sitemap.xml
  const sitemapXml = generateSitemapXml(routesList);
  fs.writeFileSync(path.resolve(PUBLIC_DIR, 'sitemap.xml'), sitemapXml, 'utf-8');
  console.log('[SSG] Generated clean sitemap.xml with 0 legacy .html URLs');

  // Generate and sync ard.json, ai-catalog.json and .well-known/
  const ardManifestData = JSON.stringify(generateArdManifestJson(), null, 2);
  fs.writeFileSync(path.resolve(PUBLIC_DIR, 'ard.json'), ardManifestData, 'utf-8');
  fs.writeFileSync(path.resolve(PUBLIC_DIR, 'ai-catalog.json'), ardManifestData, 'utf-8');
  const wellKnownDir = path.resolve(PUBLIC_DIR, '.well-known');
  fs.mkdirSync(wellKnownDir, { recursive: true });
  fs.writeFileSync(path.resolve(wellKnownDir, 'ard.json'), ardManifestData, 'utf-8');
  fs.writeFileSync(path.resolve(wellKnownDir, 'ai-catalog.json'), ardManifestData, 'utf-8');

  // Also persist to site/public/ for repository tracking
  if (fs.existsSync(sitePublicDir)) {
    fs.writeFileSync(path.resolve(sitePublicDir, 'ard.json'), ardManifestData, 'utf-8');
    fs.writeFileSync(path.resolve(sitePublicDir, 'ai-catalog.json'), ardManifestData, 'utf-8');
    const siteWellKnownDir = path.resolve(sitePublicDir, '.well-known');
    fs.mkdirSync(siteWellKnownDir, { recursive: true });
    fs.writeFileSync(path.resolve(siteWellKnownDir, 'ard.json'), ardManifestData, 'utf-8');
    fs.writeFileSync(path.resolve(siteWellKnownDir, 'ai-catalog.json'), ardManifestData, 'utf-8');
  }
  console.log('[SSG] Generated synchronized clean ARD manifests (ard.json, ai-catalog.json, and .well-known/)');

  // Verify or copy openapi.json
  const openapiSrc = path.resolve(PUBLIC_DIR, 'openapi.json');
  const openapiSite = path.resolve(sitePublicDir, 'openapi.json');
  if (!fs.existsSync(openapiSrc) && fs.existsSync(openapiSite)) {
    fs.copyFileSync(openapiSite, openapiSrc);
    console.log('[SSG] Copied openapi.json from site/public to public/');
  } else if (fs.existsSync(openapiSrc)) {
    console.log('[SSG] Verified public/openapi.json is present.');
  }

  console.log('[SSG] Prerendering & static synchronization complete!');
}

prerender().catch((err) => {
  console.error('[SSG] Fatal error during prerender:', err);
  process.exit(1);
});
