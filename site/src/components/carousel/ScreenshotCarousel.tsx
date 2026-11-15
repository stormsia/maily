import React, { useState, useEffect, useRef } from 'react';
import {
  ChevronLeft,
  ChevronRight,
  Maximize2,
  Play,
  Pause,
  Activity,
  Inbox,
  Zap,
  Database,
  Server,
  Key,
  ExternalLink,
  Layers,
  X
} from 'lucide-react';
import { useRouter } from '../../context/RouterContext';

interface WorkstationSlide {
  id: string;
  num: string;
  title: string;
  shortTitle: string;
  description: string;
  features: string[];
  imageWebp: string;
  imageAvif: string;
  icon: React.ElementType;
  urlMock: string;
}

const WORKSTATIONS: WorkstationSlide[] = [
  {
    id: 'overview',
    num: '01',
    title: 'Live Telemetry & Traffic Dynamics',
    shortTitle: 'Live Overview',
    description: 'Real-time monitoring dashboard showing active disposable inboxes, incoming message rates, 10-day activity trends, and multi-provider traffic distribution.',
    features: ['Active inbox gauge', 'Live message ingestion graph', 'Provider SLA status', 'Event streaming'],
    imageWebp: '/screenshots/01_overview.webp',
    imageAvif: '/screenshots/01_overview.avif',
    icon: Activity,
    urlMock: 'http://localhost:8477/dashboard/overview',
  },
  {
    id: 'mailboxes',
    num: '02',
    title: 'Multi-Provider Mailboxes Fleet',
    shortTitle: 'Mailboxes Fleet',
    description: 'Instant search, filter, and management across disposable inboxes. View upstream provider assignments, creation timestamps, and unread counts.',
    features: ['Instant fulltext search', 'Provider filtering (Mail.tm, 1secmail, etc.)', 'Manual purge & export', 'Domain allocation matrix'],
    imageWebp: '/screenshots/02_mailboxes.webp',
    imageAvif: '/screenshots/02_mailboxes.avif',
    icon: Inbox,
    urlMock: 'http://localhost:8477/dashboard/mailboxes',
  },
  {
    id: 'detail-otp',
    num: '03',
    title: 'Real-Time Email & Instant OTP Extraction',
    shortTitle: 'OTP & Message Inspector',
    description: 'Live message inspector for QA workflows. Automatically extracts 4-8 digit verification codes and magic login links with one-click copy and raw payload view.',
    features: ['Automatic OTP regex extraction', 'Magic link detector', 'Raw MIME & HTML renderers', 'Attachment download'],
    imageWebp: '/screenshots/03_mailbox_detail_email.webp',
    imageAvif: '/screenshots/03_mailbox_detail_email.avif',
    icon: Zap,
    urlMock: 'http://localhost:8477/dashboard/mailboxes/mbx_9f82/messages',
  },
  {
    id: 'retention',
    num: '04',
    title: 'Automated Retention & Storage Sweeper',
    shortTitle: 'Retention Sweeper',
    description: 'Automated background storage engine sweeper. Configurable TTL policies, automated message expiration, and hermetic SQLite WAL vacuuming metrics.',
    features: ['Configurable TTL policies', 'Background sweep daemon', 'SQLite WAL fragmentation gauge', 'Zero disk bloat'],
    imageWebp: '/screenshots/04_retention.webp',
    imageAvif: '/screenshots/04_retention.avif',
    icon: Database,
    urlMock: 'http://localhost:8477/dashboard/retention',
  },
  {
    id: 'domain-cache',
    num: '05',
    title: 'Domain Cache, Quotas & Failover Matrix',
    shortTitle: 'Domain Cache & Quotas',
    description: 'Real-time upstream domain pool across all providers. Automatic rotation avoids anti-tempmail blocklists with automated health probes and latency meters.',
    features: ['40+ rotating domains', 'Automated upstream circuit breaker', 'Latency & probe monitors', 'Custom domain mapping'],
    imageWebp: '/screenshots/05_domain_cache.webp',
    imageAvif: '/screenshots/05_domain_cache.avif',
    icon: Server,
    urlMock: 'http://localhost:8477/dashboard/domains',
  },
  {
    id: 'api-keys',
    num: '06',
    title: 'Granular Scoped API Tokens',
    shortTitle: 'Scoped API Keys',
    description: 'Create and revoke scoped API keys with granular permissions (read-only, write-only, domain restrictions) and rate limits for isolated CI/CD runners.',
    features: ['Granular RBAC scopes', 'Per-runner rate limits', 'Automated token expiration', 'Audit log telemetry'],
    imageWebp: '/screenshots/06_api_keys.webp',
    imageAvif: '/screenshots/06_api_keys.avif',
    icon: Key,
    urlMock: 'http://localhost:8477/dashboard/security/keys',
  },
];

export const ScreenshotCarousel: React.FC = () => {
  const { assetUrl } = useRouter();
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const timerRef = useRef<number | null>(null);

  const activeSlide = WORKSTATIONS[activeIndex];

  // Auto-play timer
  useEffect(() => {
    if (!isPlaying) {
      if (timerRef.current) clearInterval(timerRef.current);
      return;
    }

    timerRef.current = window.setInterval(() => {
      setActiveIndex((prev) => (prev + 1) % WORKSTATIONS.length);
    }, 6000);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying]);

  const handleNext = () => {
    setActiveIndex((prev) => (prev + 1) % WORKSTATIONS.length);
  };

  const handlePrev = () => {
    setActiveIndex((prev) => (prev - 1 + WORKSTATIONS.length) % WORKSTATIONS.length);
  };

  // Keyboard controls for fullscreen & carousel navigation
  useEffect(() => {
    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (isFullscreen) {
        if (e.key === 'Escape') {
          e.preventDefault();
          setIsFullscreen(false);
        } else if (e.key === 'ArrowRight') {
          e.preventDefault();
          handleNext();
          setIsPlaying(false);
        } else if (e.key === 'ArrowLeft') {
          e.preventDefault();
          handlePrev();
          setIsPlaying(false);
        }
      }
    };

    window.addEventListener('keydown', handleGlobalKeyDown);
    return () => window.removeEventListener('keydown', handleGlobalKeyDown);
  }, [isFullscreen]);

  return (
    <div className="w-full space-y-6">
      {/* Category Navigation Pills */}
      <div className="flex items-center justify-start sm:justify-center gap-2 overflow-x-auto pb-2 scrollbar-none">
        {WORKSTATIONS.map((slide, idx) => {
          const Icon = slide.icon;
          const isActive = idx === activeIndex;
          return (
            <button
              key={slide.id}
              onClick={() => {
                setActiveIndex(idx);
                setIsPlaying(false);
              }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-medium transition-all shrink-0 ${
                isActive
                  ? 'bg-cyan-600 text-white shadow-md shadow-cyan-600/20 scale-[1.02]'
                  : 'bg-white dark:bg-slate-900/80 text-slate-600 dark:text-slate-400 border border-slate-200 dark:border-slate-800 hover:text-slate-900 dark:hover:text-white hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-cyan-600 dark:text-cyan-400'}`} />
              <span>{slide.shortTitle}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono ${isActive ? 'bg-cyan-700/60 text-cyan-100' : 'bg-slate-100 dark:bg-slate-800 text-slate-500'}`}>
                {slide.num}
              </span>
            </button>
          );
        })}
      </div>

      {/* Main Workstation Chrome Box */}
      <div
        tabIndex={0}
        role="region"
        aria-label="Workstation Screenshots Carousel"
        aria-roledescription="carousel"
        className="relative rounded-2xl border border-slate-200 dark:border-slate-800 bg-slate-900 shadow-2xl overflow-hidden group focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
        onMouseEnter={() => setIsPlaying(false)}
        onMouseLeave={() => setIsPlaying(true)}
        onKeyDown={(e) => {
          if (e.key === 'ArrowLeft') {
            e.preventDefault();
            handlePrev();
            setIsPlaying(false);
          } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            handleNext();
            setIsPlaying(false);
          }
        }}
      >
        {/* Browser Top Chrome Header */}
        <div className="px-4 py-3 bg-slate-950/90 border-b border-slate-800/80 flex items-center justify-between gap-4 text-xs">
          {/* Traffic lights & Workstation Counter */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
            </div>
            <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-mono text-slate-400">
              <span className="text-cyan-400 font-bold">Maily Admin Console</span>
              <span>·</span>
              <span>Screen {activeSlide.num} of 06</span>
            </div>
          </div>

          {/* URL Bar Mock */}
          <div className="flex-1 max-w-md mx-auto hidden md:flex items-center gap-2 px-3 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-400 justify-center">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span className="truncate">{activeSlide.urlMock}</span>
          </div>

          {/* Controls: Fullscreen Inspection */}
          <div className="flex items-center gap-1 text-slate-400">
            <button
              onClick={() => setIsFullscreen(true)}
              className="p-1.5 rounded-lg hover:bg-slate-800 hover:text-white transition-colors flex items-center gap-1.5 text-xs font-mono"
              title="Expand High-Resolution Inspection"
            >
              <Maximize2 className="w-4 h-4 text-cyan-400" />
              <span className="hidden sm:inline">Inspect High-Res</span>
            </button>
          </div>
        </div>

        {/* Screenshot Viewport with Navigation Arrows */}
        <div className="relative w-full aspect-[32/19] bg-slate-950 overflow-hidden cursor-pointer" onClick={() => setIsFullscreen(true)}>
          <picture>
            <source srcSet={assetUrl(activeSlide.imageAvif)} type="image/avif" />
            <source srcSet={assetUrl(activeSlide.imageWebp)} type="image/webp" />
            <img
              src={assetUrl(activeSlide.imageWebp)}
              alt={activeSlide.title}
              className="w-full h-full object-contain object-left-top transition-all duration-300"
              loading="lazy"
              width={3200}
              height={1900}
            />
          </picture>

          {/* Left Arrow Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handlePrev();
              setIsPlaying(false);
            }}
            className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-slate-950/80 hover:bg-cyan-600 text-white border border-slate-700/80 shadow-lg backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
            aria-label="Previous workstation"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          {/* Right Arrow Button */}
          <button
            onClick={(e) => {
              e.stopPropagation();
              handleNext();
              setIsPlaying(false);
            }}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-slate-950/80 hover:bg-cyan-600 text-white border border-slate-700/80 shadow-lg backdrop-blur-sm transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
            aria-label="Next workstation"
          >
            <ChevronRight className="w-5 h-5" />
          </button>

          {/* Progress Indicator Dots */}
          <div className="absolute bottom-3 left-1/2 -translate-x-1/2 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-950/80 backdrop-blur-md border border-slate-800">
            {WORKSTATIONS.map((_, idx) => (
              <button
                key={idx}
                onClick={(e) => {
                  e.stopPropagation();
                  setActiveIndex(idx);
                  setIsPlaying(false);
                }}
                className={`transition-all rounded-full ${
                  idx === activeIndex
                    ? 'w-6 h-1.5 bg-cyan-400'
                    : 'w-1.5 h-1.5 bg-slate-600 hover:bg-slate-400'
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Informative Slide Detail Footer */}
        <div className="p-5 sm:p-6 bg-slate-950 border-t border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
                Workstation {activeSlide.num}
              </span>
              <h3 className="text-base sm:text-lg font-bold text-white font-display">
                {activeSlide.title}
              </h3>
            </div>
            <p className="text-xs sm:text-sm text-slate-400 max-w-3xl leading-relaxed">
              {activeSlide.description}
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-2 md:pt-0">
            {activeSlide.features.map((feat) => (
              <span
                key={feat}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 text-[11px] font-mono text-slate-300"
              >
                ✓ {feat}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* High-Resolution Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="fixed inset-0 z-50 bg-slate-950/95 backdrop-blur-md p-4 sm:p-8 flex flex-col items-center justify-center animate-fade-in"
          onClick={() => setIsFullscreen(false)}
        >
          <div className="w-full max-w-6xl space-y-3" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between text-white">
              <div className="flex items-center gap-3">
                <span className="text-sm font-mono text-cyan-400 font-bold">
                  Screen {activeSlide.num}: {activeSlide.title}
                </span>
              </div>
              <button
                onClick={() => setIsFullscreen(false)}
                className="p-2 rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white transition-colors border border-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="relative rounded-2xl overflow-hidden border border-slate-800 bg-slate-900 shadow-2xl">
              <picture>
                <source srcSet={assetUrl(activeSlide.imageAvif)} type="image/avif" />
                <source srcSet={assetUrl(activeSlide.imageWebp)} type="image/webp" />
                <img
                  src={assetUrl(activeSlide.imageWebp)}
                  alt={activeSlide.title}
                  className="w-full h-auto max-h-[82vh] object-contain mx-auto"
                />
              </picture>

              {/* Modal Prev / Next buttons */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handlePrev();
                }}
                className="absolute left-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-slate-950/80 hover:bg-cyan-600 text-white border border-slate-700/80 shadow-xl transition-all"
                aria-label="Previous workstation screenshot"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleNext();
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-2.5 rounded-full bg-slate-950/80 hover:bg-cyan-600 text-white border border-slate-700/80 shadow-xl transition-all"
                aria-label="Next workstation screenshot"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            <div className="flex items-center justify-between text-xs font-mono text-slate-400 pt-1">
              <span>{activeSlide.description}</span>
              <span className="hidden sm:inline">Press ESC to close · ← / → to navigate</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
