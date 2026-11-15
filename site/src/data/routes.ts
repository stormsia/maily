export interface FaqItem {
  question: string;
  answer: string;
}

export interface RouteItem {
  path: string;
  title: string;
  navTitle?: string;
  description: string;
  keywords?: string[];
  category?: 'main' | 'guide' | 'advanced' | 'api';
  canonical: string;
  ogType?: 'website' | 'article';
  faqs?: FaqItem[];
}

export const SITE_URL = 'https://stormsia.github.io/maily';

export const ROUTES: Record<string, RouteItem> = {
  '/': {
    path: '/',
    title: 'Maily · Self-Hosted Temporary Email Gateway & Developer Hub',
    navTitle: 'Overview',
    description: 'Self-hosted universal temporary email gateway aggregating 8+ disposable mail providers into one REST API & async Python SDK. Built for Playwright & Pytest OTP verification with sub-second extraction.',
    keywords: [
      'temporary email api',
      'disposable email gateway',
      'temp mail api',
      '1secmail alternative',
      'mailtm api',
      'playwright email verification',
      'pytest email testing',
      'otp code extraction',
      'self-hosted email gateway',
      'sqlite wal mail server',
      'ephemeral inboxes',
      'e2e email testing'
    ],
    category: 'main',
    canonical: `${SITE_URL}/`,
    ogType: 'website',
    faqs: [
      {
        question: 'How does Maily differ from single-provider libraries like mailtm or tempmail?',
        answer: 'Single-provider libraries break whenever that specific upstream service experiences downtime, alters its API schema, or gets added to spam blocklists. Maily unifies 8+ providers under a single normalized OpenAPI 3.1 REST API and async Python SDK with automatic circuit breakers, domain fallback across 40+ rotating domains, and sub-millisecond SQLite WAL storage.'
      },
      {
        question: 'How fast is OTP verification code extraction in automated test suites?',
        answer: 'Incoming emails are processed within sub-second latency of arrival upstream. Using await api.wait_for_code(box, timeout=30.0), Maily continuously polls and extracts 4–8 digit verification codes or confirmation links with zero flaky polling overhead.'
      },
      {
        question: 'How does Maily prevent domain blacklisting in E2E tests?',
        answer: 'Many SaaS sign-up forms block known disposable email domains like @mailtm.com. Maily mitigates this by maintaining a live pool of 40+ rotating domains across multiple provider networks, plus support for custom domains and Gmail alias tags (username+tag@gmail.com).'
      },
      {
        question: 'Can I run Maily completely self-hosted with Docker?',
        answer: 'Yes. Maily is packaged as an optimized, unprivileged non-root Docker container (ghcr.io/stormsia/maily:latest). It stores state in embedded SQLite with Write-Ahead Logging (WAL) and automatic defragmentation, requiring zero external databases or Redis caches.'
      },
      {
        question: 'What is the licensing and pricing model for Maily?',
        answer: 'Maily is 100% Free Open Source Software (FOSS) released under the permissive MIT license. There are no paid tiers, no usage meters, no credit card requirements, and no vendor lock-in for self-hosted instances.'
      }
    ],
  },
  '/analytics': {
    path: '/analytics',
    title: 'Live Security, Quality & Provider Health Analytics | Maily',
    navTitle: 'Analytics & Health',
    description: 'Real-time telemetry, test coverage, provider operational health matrix, and continuous performance benchmarks for Maily.',
    keywords: [
      'temp mail provider health',
      'disposable mail status',
      'email gateway telemetry',
      'sqlite wal benchmark',
      'mail provider latency',
      'sla monitoring'
    ],
    category: 'main',
    canonical: `${SITE_URL}/analytics`,
    ogType: 'website',
    faqs: [
      {
        question: 'How often is the provider health state updated?',
        answer: 'Provider health checks run continuously via automated GitHub Actions synthetic probes, verifying mailbox provisioning and inbound delivery latency across every supported upstream provider.'
      },
      {
        question: 'What happens when an upstream provider goes down?',
        answer: 'Maily circuit breaker detects consecutive failure rates exceeding threshold limits and automatically reroutes mailbox provisioning requests to healthy fallback providers.'
      }
    ],
  },
  '/docs': {
    path: '/docs',
    title: 'Developer Documentation Hub & Getting Started | Maily',
    navTitle: 'Getting Started',
    description: 'Complete developer documentation for Maily temporary email gateway: architecture overview, 60-second quickstarts, integration tutorials, and production testing patterns.',
    keywords: [
      'maily documentation',
      'temp email quickstart',
      'disposable mail integration',
      'playwright email testing',
      'pytest temp mail',
      'developer hub'
    ],
    category: 'guide',
    canonical: `${SITE_URL}/docs`,
    ogType: 'article',
    faqs: [
      {
        question: 'What is the fastest way to get started with Maily?',
        answer: 'Run docker run -d -p 8477:8477 -e MAILY_API_KEY=your_secret_api_key -v maily_data:/data ghcr.io/stormsia/maily:latest, then install the Python SDK via pip install maily-client and create your first ephemeral inbox in 3 lines of code.'
      },
      {
        question: 'Does Maily require an external database like PostgreSQL or MySQL?',
        answer: 'No. Maily runs with zero external infrastructure dependencies. It utilizes an embedded SQLite engine configured with Write-Ahead Logging (WAL) and automatic VACUUM compaction, yielding > 10,000 ops/sec.'
      }
    ],
  },
  '/docs/python': {
    path: '/docs/python',
    title: 'Python Async SDK Guide & Pydantic Schemas | Maily Documentation',
    navTitle: 'Python SDK',
    description: 'Developer guide for the official maily-client Python library: async context managers, Pydantic v2 schemas, OTP extraction helpers, and exception hierarchy.',
    keywords: [
      'maily-client',
      'python temp mail sdk',
      'async email client',
      'pydantic email schemas',
      'pytest email fixture',
      'wait_for_code python'
    ],
    category: 'guide',
    canonical: `${SITE_URL}/docs/python`,
    ogType: 'article',
    faqs: [
      {
        question: 'Does maily-client support synchronous execution?',
        answer: 'Yes. In addition to the primary async Maily client, maily-client includes a transparent SyncMaily facade for traditional blocking frameworks like unittest, Celery, or standard scripts.'
      },
      {
        question: 'How does wait_for_code extract verification codes?',
        answer: 'wait_for_code polls the mailbox using exponential backoff and applies strict regex extractors to identify 4–8 digit verification codes and magic links, returning as soon as the email arrives.'
      }
    ],
  },
  '/docs/curl': {
    path: '/docs/curl',
    title: 'cURL & Universal REST API Guide | Maily Documentation',
    navTitle: 'cURL & REST API',
    description: 'Command-line recipes and HTTP endpoints for interacting directly with the Maily temporary email gateway using cURL, HTTPie, or any HTTP client.',
    keywords: [
      'curl temp mail',
      'temp email rest api',
      'disposable email curl',
      'openapi 3.1 mail gateway',
      'http mailboxes api',
      'server-sent events email'
    ],
    category: 'guide',
    canonical: `${SITE_URL}/docs/curl`,
    ogType: 'article',
    faqs: [
      {
        question: 'How do I authenticate REST API requests?',
        answer: 'Include the X-API-Key HTTP header in your requests. If MAILY_API_KEY is not configured on the server, requests are treated as public or authenticated via scoped tokens.'
      },
      {
        question: 'Can I stream new messages in real-time with cURL?',
        answer: 'Yes. Connect to GET /v1/mailboxes/{id}/events with curl -N to receive Server-Sent Events (SSE) as incoming emails arrive.'
      }
    ],
  },
  '/docs/docker': {
    path: '/docs/docker',
    title: 'Docker & Self-Hosting in 60 Seconds | Maily Documentation',
    navTitle: 'Docker & Deployment',
    description: 'Step-by-step instructions for deploying Maily with Docker Compose, Portainer, or Kubernetes Helm charts with zero external database dependencies.',
    keywords: [
      'docker temp mail',
      'self-hosted email gateway docker',
      'docker-compose temp mail',
      'portainer email template',
      'kubernetes mail gateway',
      'sqlite wal docker volume'
    ],
    category: 'guide',
    canonical: `${SITE_URL}/docs/docker`,
    ogType: 'article',
    faqs: [
      {
        question: 'How is data persisted across container updates?',
        answer: 'Mount a host volume or named Docker volume to /data. The embedded SQLite database and encryption keys are stored inside this directory.'
      },
      {
        question: 'Does the container run as root?',
        answer: 'No. The official Maily container is security-hardened and executes as unprivileged user 65534:65534 (nobody:nogroup) with a read-only root filesystem.'
      }
    ],
  },
  '/docs/providers': {
    path: '/docs/providers',
    title: 'Supported Disposable Mail Providers & Matrix | Maily Documentation',
    navTitle: 'Provider Matrix',
    description: 'Detailed capabilities, domains, rate limits, and features of the 8+ temporary mail providers unified under Maily.',
    keywords: [
      'temp mail providers list',
      'disposable email matrix',
      'mailtm alternative',
      '1secmail api',
      'guerrillamail api',
      'tempmail plus',
      'rotating email domains'
    ],
    category: 'guide',
    canonical: `${SITE_URL}/docs/providers`,
    ogType: 'article',
    faqs: [
      {
        question: 'Can I use Maily in air-gapped CI without internet?',
        answer: 'Yes. Use the built-in noopmail provider, which runs entirely in-memory and allows injecting synthetic test emails via local API calls.'
      },
      {
        question: 'How many active domains are available across providers?',
        answer: 'Maily maintains a pool of 40+ active domains across provider networks, rotating them to bypass anti-disposable blocklists.'
      }
    ],
  },
  '/docs/adding-providers': {
    path: '/docs/adding-providers',
    title: 'Custom Provider Implementation Guide | Maily Documentation',
    navTitle: 'Adding Providers',
    description: 'Step-by-step architectural guide to implementing, registering, and testing a custom disposable email provider in Maily.',
    keywords: [
      'custom email provider',
      'maily provider plugin',
      'baseprovider python',
      'temp mail adapter',
      'extensible mail gateway'
    ],
    category: 'advanced',
    canonical: `${SITE_URL}/docs/adding-providers`,
    ogType: 'article',
    faqs: [
      {
        question: 'What interface must a custom provider implement?',
        answer: 'Every provider extends the BaseProvider abstract base class and implements get_domains(), create_mailbox(), get_messages(), get_message(), and delete_mailbox().'
      }
    ],
  },
  '/docs/recipes': {
    path: '/docs/recipes',
    title: 'Production Testing Recipes & Verification Patterns | Maily Documentation',
    navTitle: 'Production Recipes',
    description: 'End-to-end integration patterns, Playwright/Cypress email verification, OTP extraction regexes, and Pytest test fixtures.',
    keywords: [
      'playwright email test',
      'pytest temp email fixture',
      'cypress email verification',
      'selenium otp extraction',
      'e2e test automation recipes',
      'magic link verification'
    ],
    category: 'advanced',
    canonical: `${SITE_URL}/docs/recipes`,
    ogType: 'article',
    faqs: [
      {
        question: 'Can Maily handle magic link confirmations with query tokens?',
        answer: 'Yes. The wait_for_link method extracts HTTP/HTTPS URLs matching custom regex patterns from incoming email HTML and plaintext bodies.'
      }
    ],
  },
  '/docs/architecture': {
    path: '/docs/architecture',
    title: 'Architecture & System Resilience | Maily Documentation',
    navTitle: 'Architecture & Resilience',
    description: 'Deep dive into Maily internal architecture: SQLite WAL storage, Fernet AES-128-CBC encryption at rest, zero outbound SMTP, provider failover routing, and SSE delivery.',
    keywords: [
      'maily architecture',
      'inbound only email gateway',
      'sqlite wal performance',
      'fernet encryption at rest',
      'originguard middleware',
      'threat model disposable mail'
    ],
    category: 'advanced',
    canonical: `${SITE_URL}/docs/architecture`,
    ogType: 'article',
    faqs: [
      {
        question: 'Why does Maily have zero outbound SMTP capabilities?',
        answer: 'By deliberately omitting outbound SMTP sending code, Maily completely prevents attackers or malicious containers from using your infrastructure as a spam relay or phishing proxy.'
      },
      {
        question: 'How are sensitive provider tokens encrypted?',
        answer: 'Tokens and credentials are encrypted using Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) with keys derived from a 256-bit cryptographically secure secret.'
      }
    ],
  },
  '/404': {
    path: '/404',
    title: '404 - Page Not Found | Maily',
    navTitle: 'Not Found',
    description: 'The requested resource was not found on Maily Developer Portal.',
    keywords: ['404', 'not found', 'maily'],
    category: 'main',
    canonical: `${SITE_URL}/404`,
    ogType: 'website',
  },
};

export interface DocNavItem {
  path: string;
  title: string;
  external?: boolean;
}

export interface DocNavSection {
  title: string;
  items: DocNavItem[];
}

export const DOCS_NAV_SECTIONS: DocNavSection[] = [
  {
    title: 'Overview',
    items: [
      { path: '/docs', title: 'Getting Started' },
      { path: '/docs/architecture', title: 'Architecture & Design' },
    ],
  },
  {
    title: 'Integration Guides',
    items: [
      { path: '/docs/python', title: 'Python SDK (`maily`)' },
      { path: '/docs/curl', title: 'cURL & REST API' },
      { path: '/docs/docker', title: 'Docker Self-Hosting' },
    ],
  },
  {
    title: 'Providers & Capabilities',
    items: [
      { path: '/docs/providers', title: 'Provider Matrix' },
      { path: '/docs/adding-providers', title: 'Adding Custom Providers' },
    ],
  },
  {
    title: 'Production & Recipes',
    items: [
      { path: '/docs/recipes', title: 'Testing Recipes & OTP' },
    ],
  },
  {
    title: 'Interactive API Explorer',
    items: [
      { path: '/scalar.html', title: 'Scalar API Reference ↗', external: true },
      { path: '/swagger.html', title: 'Swagger UI ↗', external: true },
      { path: '/redoc.html', title: 'ReDoc UI ↗', external: true },
      { path: '/openapi.json', title: 'Raw OpenAPI JSON ↗', external: true },
    ],
  },
];
