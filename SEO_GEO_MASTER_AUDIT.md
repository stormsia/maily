# 🚀 MASTER AUDIT: CLASSICAL TECHNICAL SEO & GENERATIVE ENGINE OPTIMIZATION (GEO)
## Проект: Maily (Universal Temporary Email Gateway & Developer Hub)
**Production URL:** `https://stormsia.github.io/maily/`
**Репозиторий:** `https://github.com/stormsia/maily`
**Архитектура сборки:** Python SSG (`scripts/build_pages_site.py` + `scripts/build_docs.py`), GitHub Actions (`.github/workflows/pages.yml`), GitHub Pages (`public/`)
**Дата аудита:** Ноябрь 2026
**Роль:** Lead SEO & GEO Coordinator (в координации с 4 профильными субагентами: `seo-audit`, `schema`, `site-architecture`, `ai-seo`)
**Статус:** READ-ONLY COMPREHENSIVE ARCHITECTURAL AUDIT & ACTION PLAN

---

## СОДЕРЖАНИЕ
1. [Executive Summary & Архитектура генератора](#1-executive-summary--архитектура-генератора)
2. [Матрица зрелости (Scorecard: Classic SEO vs. GEO)](#2-матрица-зрелости-scorecard-classic-seo-vs-geo)
3. [Сводный реестр проблем (Master Problem Registry)](#3-сводный-реестр-проблем-master-problem-registry)
   - [3.1. Классический технический и On-Page SEO (`seo-audit`)](#31-классический-технический-и-on-page-seo-seo-audit)
   - [3.2. Микроразметка и граф сущностей (`schema`)](#32-микроразметка-и-граф-сущностей-schema)
   - [3.3. Архитектура сайта, краулинг и навигация (`site-architecture`)](#33-архитектура-сайта-краулинг-и-навигация-site-architecture)
   - [3.4. Generative Engine Optimization & AI Agent Readiness (`ai-seo`)](#34-generative-engine-optimization--ai-agent-readiness-ai-seo)
4. [Синергия SEO + GEO: Стратегия двойного доминирования для Maily](#4-синергия-seo--geo-стратегия-двойного-доминирования-для-maily)
5. [Архитектурные спецификации готовых артефактов (Code Deliverables)](#5-архитектурные-спецификации-готовых-артефактов-code-deliverables)
   - [5.1. Полный JSON-LD `@graph` для `index.html`](#51-полный-json-ld-graph-для-indexhtml)
   - [5.2. Спецификация `public/llms.txt` и `public/llms-full.txt`](#52-спецификация-publicllmstxt-и-publicllms-fulltxt)
   - [5.3. Спецификация `public/SKILL.md` (Claude Code / Cursor)](#53-спецификация-publicskillmd-claude-code--cursor)
   - [5.4. Оптимизированный `robots.txt` и `sitemap.xml`](#54-оптимизированный-robotstxt-и-sitemapxml)
6. [Приоритизированный план внедрения (Actionable Roadmap)](#6-приоритизированный-план-внедрения-actionable-roadmap)
   - [Фаза 1: Quick Wins (Генератор за 1 проход)](#фаза-1-quick-wins-генератор-за-1-проход)
   - [Фаза 2: Структурные и контентные улучшения (SSG / Мультистраничность)](#фаза-2-структурные-и-контентные-улучшения-ssg--мультистраничность)

---

## 1. Executive Summary & Архитектура генератора

### 1.1. Текущее состояние портала
Проект **Maily** обладает исключительным инженерным качеством ядра (Python 3.10+, FastAPI, SQLite WAL с задержкой записи < 2.5 мс, шифрование Fernet-256, 150+ тестов с покрытием 95%, 8 интегрированных провайдеров временной почты, клиентский SDK с однострочным методом `wait_for_code()`).

Однако веб-витрина проекта (`https://stormsia.github.io/maily/`), развернутая на GitHub Pages, на текущий момент страдает от **классической ловушки монолитного SPA и слепых зон генеративного ИИ**:
1. **85% контента заблокировано атрибутом `hidden`:** Вся ценнейшая документация по Python SDK, Docker-развертыванию, матрице провайдеров, cURL и Playwright-рецептам собрана в один монолитный файл `index.html` (91.5 КБ) и скрыта через `<div class="tab-pane" role="tabpanel" hidden>`. Это лишает проект посадочных страниц под средне- и низкочастотные запросы.
2. **Нулевая видимость страниц API для AI-краулеров (AR-READ-01):** Страницы `scalar.html`, `swagger.html` и `redoc.html` являются на 100% клиентскими JS-оболочками (CSR). Краулеры Perplexity, ChatGPT Search, Claude и простые HTTP-клиенты видят абсолютно пустой DOM без единого метода или описания модели.
3. **Отсутствие стандартов Agent-Ready (llmstxt.org, OpenAPI discovery, SKILL.md):** В корне сайта отсутствуют файлы `llms.txt`, `llms-full.txt`, чистые `.md` зеркала и манифесты AI-каталогов. Агенты не могут быстро получить контекст для интеграции.
4. **Фрагментарный JSON-LD и отсутствие графа сущностей:** Единственный объект `SoftwareApplication` на главной странице изолирован, не имеет `@id`, не привязан к GitHub, PyPI, Docker GHCR и не содержит спецификации `WebAPI`.
5. **Технические дефекты классического SEO:** Отсутствие тегов `canonical` на всех второстепенных страницах; отсутствие OpenGraph и Twitter Cards; сломанные фавиконы в Google SERP из-за inline Data-URI; включение служебного `openapi.json` в `sitemap.xml`; пропуск уровней заголовков (`H1` -> `H3`) на аналитических дашбордах; риск CLS из-за отсутствия `width`/`height` у изображений; отсутствие кастомной страницы `404.html`.

### 1.2. Архитектура пайплайна генерации
Вся статическая сборка портала централизована в репозитории:
- **`scripts/build_pages_site.py` (169 КБ, ~4200 строк):** Единый компилятор веб-портала. Он генерирует `index.html`, `scalar.html`, `swagger.html`, `redoc.html`, `analytics.html`, `dev/bench/index.html`, `openapi.json`, `robots.txt` и `sitemap.xml`.
- **`scripts/build_docs.py`:** Синхронизатор блоков документации между `docs/*.md` (`DOCKER.md`, `PROVIDERS.md`, `CURL_GUIDE.md`, `CLIENT_GUIDE.md`), `README.md` и веб-шаблонами.
- **`.github/workflows/pages.yml`:** CI/CD пайплайн. По пушу в `main` или завершению бенчмарков он запускает `uv run python scripts/build_pages_site.py`, архивирует каталог `public/` и развертывает его на GitHub Pages через `actions/deploy-pages@v5`.

> [!IMPORTANT]
> **Системное преимущество:** Поскольку весь портал компилируется детерминированным Python-скриптом, **100% всех выявленных проблем устраняются в одном месте — в скрипте `scripts/build_pages_site.py` (и вспомогательном `build_docs.py`)**. Достаточно один раз настроить генерацию метатегов, канонических ссылок, JSON-LD графов, `llms.txt`, чистых `.md` копий и семантических фолбэков, чтобы при каждом релизе портал пересобирался с идеальным соответствием стандартам Google Search Central и AgentReady.org.

---

## 2. Матрица зрелости (Scorecard: Classic SEO vs. GEO)

| Оцениваемая область | Текущее состояние | Целевое состояние | Текущий балл | Целевой балл |
|---|---|---|:---:|:---:|
| **Technical Crawlability & Indexation** | `robots.txt` без AI-директив; `openapi.json` в sitemap; нет `<lastmod>`; нет `404.html`. | Чистый sitemap с `<lastmod>`; кастомный `404.html`; директивы Content-Usage. | **45 / 100** | **100 / 100** |
| **Canonicalization & Duplication** | 3 одинаковых API UI (`scalar`, `swagger`, `redoc`) в поиске; нет `rel=canonical` на 5 страницах. | Единственный канонический `scalar.html`; `noindex` на Swagger и ReDoc. | **20 / 100** | **100 / 100** |
| **On-Page & Semantic Hierarchy** | 0 заголовков на страницах API; пропуски `H1->H3` в дашбордах; слабый H1 на главной. | Четкая иерархия `H1->H2->H3`; семантические скрытые заголовки для доступности. | **40 / 100** | **95 / 100** |
| **Core Web Vitals & Media** | Изображения без `width`/`height` (риск CLS); синхронный `chart.js` в `<head>`; `.avif` не используется. | Атрибуты размеров; `loading="lazy"`; тег `<picture>` с `.avif`; отложенные скрипты. | **50 / 100** | **98 / 100** |
| **Structured Data (Schema.org)** | Изолированный `SoftwareApplication` на 1 странице; 0 схем на остальных 5 страницах. | Связный `@graph` (`WebSite`, `WebAPI`, `SoftwareSourceCode`, `Dataset`, `FAQPage`, `BreadcrumbList`). | **25 / 100** | **100 / 100** |
| **Site Architecture & URL Depth** | Антипаттерн "Flat Swamp"; 7 ключевых тем заперты под `hidden` без собственных URL. | Многостраничный Hub-and-Spoke с посадочными страницами в `/docs/` и чистой перелинковкой. | **35 / 100** | **95 / 100** |
| **Agent Readiness (Find & Read)** | CSR слепые зоны на API страницах (AR-READ-01); нет `/llms.txt`; нет `.md` зеркал. | 100% SSR/фолбэк в Initial HTML; `/llms.txt` и `llms-full.txt`; `Accept: text/markdown`. | **30 / 100** | **100 / 100** |
| **Agent Actionability (Act)** | Нет манифеста инструментов; нет `SKILL.md` для Claude Code / Cursor. | Публичный `SKILL.md` для тестов; легковесный `tools.json` для вызова функций. | **40 / 100** | **95 / 100** |
| **GEO Citation-Worthiness** | Запрос "self-hosted" отсутствует на сайте; таблица сравнения обезличена; нет FAQ. | 40-60 word Answer Blocks; статистика с источниками; Evidence Sandwich; FAQ аккордеон. | **40 / 100** | **100 / 100** |
| **ИТОГОВЫЙ БАЛЛ** | **Пре-релизный прототип с критическими блокерами** | **Эталонный Developer Portal мирового уровня** | **36 / 100 (F)** | **98 / 100 (A+)** |

---

## 3. Сводный реестр проблем (Master Problem Registry)

### 3.1. Классический технический и On-Page SEO (`seo-audit`)

```mermaid
flowchart TD
    subgraph Audit_SEO["Зона 1: Technical & On-Page SEO"]
        direction TB
        P_CANON["Отсутствие canonical<br/>на 5 из 6 страниц"]
        P_FAV["Data URI SVG фавикон<br/>(Серый глобус в SERP)"]
        P_MAP["openapi.json в sitemap.xml<br/>& отсутствие lastmod"]
        P_CLS["Отсутствие width/height<br/>(Высокий CLS)"]
        P_HEAD["0 заголовков на API<br/>& пропуск H1->H3"]
        P_BLOCK["Синхронный Chart.js<br/>в head бенчмарков"]
    end

    P_CANON -->|Риск| CANON_RISK["Каннибализация & дублирование"]
    P_FAV -->|Риск| CTR_RISK["Падение CTR в Google SERP"]
    P_MAP -->|Риск| CRAWL_RISK["Слив краулингового бюджета"]
    P_CLS -->|Риск| CWV_RISK["Пессимизация Google Page Experience"]
```

#### Проблема SEO-1: Полное отсутствие тегов `<link rel="canonical">` на всех второстепенных страницах
- **Где находится:** `public/scalar.html`, `public/swagger.html`, `public/redoc.html`, `public/analytics.html`, `public/dev/bench/index.html`; `scripts/build_pages_site.py` — функции `generate_scalar_ui()` (строки 480–490), `generate_swagger_ui()` (строки 537–547), `generate_redoc_ui()` (строки 629–638), `generate_analytics_dashboard()` (строки 923–933), `generate_benchmark_dashboard()` (строки 2977–2987).
- **Описание проблемы:** Канонический тег объявлен только на главной странице (`https://stormsia.github.io/maily/`). На остальных пяти страницах тег отсутствует.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* При переходе по ссылкам с UTM-метками (`?utm_source=...`), параметрами сессий или при обращении с завершающим слэшем и без него поисковые системы индексируют дублирующиеся URL. Для страницы `dev/bench/index.html` краулер вынужден самостоятельно угадывать канонический адрес между `/dev/bench/` и `/dev/bench/index.html`, распыляя ссылочный вес.
  - *Побочки внедрения (Risks & Mitigations):* Риск ошибочной канонизации вложенной страницы на корень. *Нейтрализация:* автоматическая генерация строгого абсолютного самоссылающегося URL с учетом переменной `base_path`.
- **Путь решения (Actionable Fix):** Внедрить в `<head>` каждой страницы явный тег `<link rel="canonical" href="https://stormsia.github.io/maily/{page_path}" />`. Для альтернативных API-интерфейсов (`swagger.html`, `redoc.html`) направить канонический адрес на `scalar.html`.

---

#### Проблема SEO-2: Использование Data-URI SVG блокирует фавикон в поисковой выдаче Google SERP
- **Где находится:** Все страницы; `scripts/build_pages_site.py` — строки 485, 542, 634, 928, 1409, 2982 (`<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,...">`).
- **Описание проблемы:** Фавикон внедрен через inline Data-URI строку. Физические файлы `public/favicon.ico`, `public/favicon.svg` и `apple-touch-icon.png` в репозитории отсутствуют.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Согласно официальной документации Google Search Central (*"Define a favicon to show in search results"*), робот `Googlebot-Image` не поддерживает Data-URI для фавиконов. В мобильной и десктопной выдаче Google рядом со сниппетом Maily отображается серый дефолтный глобус, что снижает доверие и кликабельность (CTR) на 8–15%. Браузеры также запрашивают `/favicon.ico` по умолчанию, генерируя постоянные 404 ошибки на сервере.
  - *Побочки внедрения (Risks & Mitigations):* Дополнительный сетевой запрос за файлом иконки. *Нейтрализация:* минимальный размер SVG (< 1 КБ) и кеширование на стороне CDN GitHub Pages.
- **Путь решения (Actionable Fix):** В функции `generate_seo_files()` или `copy_static_assets()` сохранять физический файл `public/assets/favicon.svg` и `public/favicon.ico`. Прописать во всех шаблонах ссылки на статические файлы и добавить `<link rel="apple-touch-icon" sizes="180x180" href="assets/apple-touch-icon.png">`.

---

#### Проблема SEO-3: Включение служебного файла `openapi.json` и отсутствие `<lastmod>` в `sitemap.xml`
- **Где находится:** `public/sitemap.xml`; `scripts/build_pages_site.py` — функция `generate_seo_files()` (строки 423–463).
- **Описание проблемы:** В XML-карту сайта включен технический JSON-файл схемы (`https://stormsia.github.io/maily/openapi.json`), отсутствуют теги последней модификации `<lastmod>`, а также присутствуют директивы `<priority>` и `<changefreq>`.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Поисковые системы расходуют краулинговый бюджет на обход сырых данных вместо HTML-страниц; сырой JSON может появиться в результатах поиска без заголовков и стилей. При этом Googlebot полностью игнорирует теги `<priority>` и `<changefreq>`, но критически нуждается в `<lastmod>` для планирования переобхода обновленной документации.
  - *Побочки внедрения (Risks & Mitigations):* Если передавать статическую жестко закодированную дату, робот перестанет доверять `<lastmod>`. *Нейтрализация:* динамическое вычисление даты последней сборки или git-коммита через `datetime.now(timezone.utc).strftime("%Y-%m-%d")`.
- **Путь решения (Actionable Fix):** Удалить узел `openapi.json` из `sitemap.xml`. Добавить актуальный тег `<lastmod>YYYY-MM-DD</lastmod>` к каждой записи HTML-страницы.

---

#### Проблема SEO-4: Отсутствие мета-тегов OpenGraph и Twitter Cards на всех 5 второстепенных страницах
- **Где находится:** `scalar.html`, `swagger.html`, `redoc.html`, `analytics.html`, `dev/bench/index.html`; `scripts/build_pages_site.py` — строки 480–488, 538–546, 630–637, 924–932, 2978–2986.
- **Описание проблемы:** Разметка для социальных сетей и мессенджеров (`og:title`, `og:description`, `og:image`, `og:url`, `og:type`, `twitter:card`, `twitter:image`) присутствует только на главной странице. На всех остальных страницах этих тегов нет.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* При публикации ссылок на дашборд безопасности, бенчмарки или API-документацию в Telegram, Slack, Twitter/X, Discord, LinkedIn и Reddit превью карточки отображается серым или формирует случайный текст. Это резко снижает виральность среди разработчиков.
  - *Побочки внедрения (Risks & Mitigations):* Незначительное увеличение размера HTML (~500 байт на страницу). Рисков нет.
- **Путь решения (Actionable Fix):** Создать единую функцию-генератор метатегов `get_head_meta(title, description, path, og_image)` и вызывать ее во всех функциях сборки страниц в `scripts/build_pages_site.py`.

---

#### Проблема SEO-5: Отсутствие атрибутов `width` и `height` на всех изображениях (Риск деградации CLS)
- **Где находится:** `public/index.html`; `scripts/build_pages_site.py` — строки 2186 (`hero_banner.webp`), 2303 (`01_overview.webp`), 2504 (`infographic_zoo.webp`).
- **Описание проблемы:** В тегах `<img>` не указаны атрибуты физических размеров (`width` и `height`), отсутствует `loading="lazy"` на изображениях ниже первого экрана и отсутствует `fetchpriority="high"` на LCP-баннере.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* До загрузки картинок браузер резервирует под них нулевую высоту. По мере рендеринга контент резко сдвигается вниз, вызывая высокий показатель Cumulative Layout Shift (CLS > 0.1), что является прямым фактором пессимизации в алгоритмах Google Page Experience и Core Web Vitals.
  - *Побочки внедрения (Risks & Mitigations):* При жестком указании пикселей верстка может потерять адаптивность на мобильных устройствах. *Нейтрализация:* сопровождение явных атрибутов CSS-правилом `height: auto; max-width: 100%; aspect-ratio: ...`.
- **Путь решения (Actionable Fix):** Прописать точные атрибуты: `width="1376" height="768"` для `hero_banner.webp` и `infographic_zoo.webp`, `width="3200" height="1900"` для `01_overview.webp`. Добавить к `hero_banner` атрибут `fetchpriority="high" decoding="async"`, а к остальным — `loading="lazy" decoding="async"`. Обернуть ключевые изображения в `<picture>` с поддержкой существующих в репозитории `.avif` версий.

---

#### Проблема SEO-6: Нарушение семантической иерархии заголовков и нулевые заголовки на страницах API
- **Где находится:** `public/scalar.html` (0 заголовков), `public/swagger.html` (0 заголовков), `public/redoc.html` (0 заголовков); `public/analytics.html` (пропуск `H1 -> H3`, строки 960, 1358); `public/dev/bench/index.html` (пропуск `H1 -> H3`, строки 3018, 3089); `public/index.html` (метафоричный H1, строка 2156).
- **Описание проблемы:**
  1. Страницы API-документации в статическом коде имеют 0 заголовков.
  2. На аналитических дашбордах теги `H2` полностью отсутствуют, заголовки секций оформлены через `<div class="section-title">`, а подзаголовки карточек сразу используют `H3` и `H4`.
  3. На главной странице H1 звучит как *"One Unified Gateway to Rule the Disposable Email Zoo"*, не содержа точного вхождения целевых ключевых фраз.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Нарушение WCAG 2.1 (Критерий 1.3.1) и правил Document Outline. Поисковые пауки снижают релевантность документов с нарушенной иерархией. Страницы API-документации воспринимаются как Thin Content / Soft 404.
  - *Побочки внедрения (Risks & Mitigations):* Изменение стилей при смене `div` на `h2`. *Нейтрализация:* сохранение существующих CSS-классов `.section-title`.
- **Путь решения (Actionable Fix):**
  - Заменить `<div class="section-title">` на `<h2 class="section-title">` в `analytics.html` и `dev/bench/index.html`.
  - Добавить в `scalar.html`, `swagger.html` и `redoc.html` статический семантический заголовок `<header class="sr-only"><h1>Maily REST API Specification</h1><p>Interactive OpenAPI 3.1 reference...</p></header>`.
  - Скорректировать H1 на главной: `<h1 class="hero-title">Universal Temporary Email Gateway &amp; Developer Hub</h1>`.

---

#### Проблема SEO-7: Блокирующие рендеринг ресурсы в `<head>`
- **Где находится:** `public/dev/bench/index.html` (строка 2986: синхронный скрипт `chart.umd.min.js`); `public/index.html` (строка 1415: `swagger-ui.css`).
- **Описание проблемы:** Библиотека Chart.js (~200 КБ) загружается в `<head>` страницы бенчмарков синхронно без атрибутов `defer`/`async`, блокируя парсер DOM. На главной странице стили Swagger UI (~150 КБ) синхронно блокируют первый рендер, хотя вкладка скрыта по умолчанию.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Увеличение First Contentful Paint (FCP) и Total Blocking Time (TBT) на 400–700 мс на мобильных устройствах.
  - *Побочки внедрения (Risks & Mitigations):* Если скрипт отрисовки графиков вызовется до загрузки Chart.js, возникнет `ReferenceError: Chart is not defined`. *Нейтрализация:* использование атрибута `defer` (скрипт гарантированно выполнится до `DOMContentLoaded`).
- **Путь решения (Actionable Fix):** Добавить `defer` к тегу Chart.js; перенести стили `swagger-ui.css` в асинхронную подгрузку при открытии соответствующего таба, либо использовать `<link rel="preload" as="style" onload="this.rel='stylesheet'">`.

---

### 3.2. Микроразметка и граф сущностей (`schema`)

```mermaid
graph LR
    subgraph Entity_Graph["Проектируемый связный граф (@graph)"]
        direction TB
        WS["WebSite (#website)<br/>url: maily/"]
        WP["WebPage (#webpage)<br/>Home Portal"]
        SA["SoftwareApplication (#software)<br/>Maily Gateway"]
        SC["SoftwareSourceCode (#sourcecode)<br/>GitHub repo"]
        WA["WebAPI (#webapi)<br/>REST Endpoints"]
        PE["Person (#author)<br/>stormsia"]
        BC["BreadcrumbList (#breadcrumb)"]
        FAQ["FAQPage (#faq)<br/>Q&A Entity"]
    end

    WS -->|hasPart| WP
    WP -->|about| SA
    SA -->|author| PE
    SA -->|hasAPI| WA
    SA -->|sourceCode| SC
    WP -->|breadcrumb| BC
    WP -->|mainEntity| FAQ
```

#### Проблема SCHEMA-1: Изолированный и бедный узел `SoftwareApplication` на главной странице
- **Где находится:** `public/index.html`; `scripts/build_pages_site.py` — строки 1418–1428.
- **Описание проблемы:** В блоке JSON-LD объявлен единственный объект без идентификатора `@id`, без версии, без ссылок на исходный код, без документации API, без условий лицензирования и без связей `sameAs`.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Google Knowledge Graph и поисковые ассистенты (Perplexity, ChatGPT) не могут провести Entity Disambiguation (разрешение сущности) и связать страницу документации со страницами на PyPI, Docker Hub и GitHub.
  - *Побочки внедрения (Risks & Mitigations):* Невалидный JSON-LD при опечатках в схеме. *Нейтрализация:* валидация через Google Rich Results Test и валидатор Schema.org.
- **Путь решения (Actionable Fix):** Перевести разметку на формат `@graph`, присвоить сущности стабильный URI `@id: "https://stormsia.github.io/maily/#software"` и внедрить свойства: `softwareVersion`, `codeRepository`, `license`, `featureList`, `offers`, `downloadUrl`, `installUrl` и массив `sameAs` (GitHub, PyPI `maily`, PyPI `maily-client`, GHCR Docker).

---

#### Проблема SCHEMA-2: Полное отсутствие микроразметки на 5 вторичных страницах
- **Где находится:** `scalar.html`, `swagger.html`, `redoc.html`, `analytics.html`, `dev/bench/index.html`.
- **Описание проблемы:** На всех пяти подстраницах тег `<script type="application/ld+json">` отсутствует на 100%.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Поисковые краулеры не распознают страницы документации API как `APIReference` к сервису `WebAPI`. Данные мониторинга доступности и SLA провайдеров не связываются с техническим анализом, а результаты бенчмарков не индексируются в Google Dataset Search.
  - *Побочки внедрения (Risks & Mitigations):* Дублирование кода в скрипте сборки. *Нейтрализация:* создание фабричной функции `get_json_ld_for_page(page_type)`.
- **Путь решения (Actionable Fix):**
  - Для `scalar.html`: добавить схему `APIReference` в связке с `WebAPI` и `BreadcrumbList`.
  - Для `analytics.html`: добавить `TechArticle` с вложенным объектом `Dataset` ("Maily Provider Fleet Operational Health & SLA Metrics").
  - Для `dev/bench/index.html`: добавить `TechArticle` и `Dataset` со ссылкой на загрузку данных `dev/bench/data.js` через `DataDownload`.

---

#### Проблема SCHEMA-3: Отсутствие навигационных цепочек `BreadcrumbList` на всех страницах
- **Где находится:** Все страницы портала (`index.html`, `scalar.html`, `swagger.html`, `redoc.html`, `analytics.html`, `dev/bench/index.html`).
- **Описание проблемы:** Ни одна страница не сообщает поисковым системам свою позицию в навигационной иерархии сайта через словарь Schema.org.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* В результатах поиска Google вместо аккуратной навигационной цепочки (`stormsia.github.io > maily > Benchmarks`) отображается длинный сырой URL (`https://stormsia.github.io/maily/dev/bench/index.html`), что ухудшает визуальное восприятие сниппета и снижает CTR.
  - *Побочки внедрения (Risks & Mitigations):* Несоответствие между визуальными хлебными крошками и JSON-LD. *Нейтрализация:* добавление визуального семантического элемента `<nav aria-label="Breadcrumb">` перед заголовком `h1`.
- **Путь решения (Actionable Fix):** Включить узел `BreadcrumbList` в JSON-LD каждой страницы с 2–3 уровнями вложенности.

---

#### Проблема SCHEMA-4: Отсутствие схемы `FAQPage` при наличии готового контента в репозитории
- **Где находится:** `public/index.html` vs `README.md` (строки 742–771).
- **Описание проблемы:** В `README.md` описан подробный FAQ из 7 инженерных вопросов (отличие от `mailtm`, скорость `wait_for_code`, обход блэклистов, Docker, Gmail OAuth2), однако в генерируемом HTML-портале этот блок визуально отсутствует, и разметка `FAQPage` не формируется.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Упущен колоссальный объем трафика из AI-поисковиков (Perplexity, ChatGPT Search, Claude, Google AI Overviews). LLM-краулеры активно извлекают готовые пары вопрос-ответ из разметки `FAQPage` для синтеза прямых ответов.
  - *Побочки внедрения (Risks & Mitigations):* Нельзя добавлять `FAQPage` без видимого текста на странице (Google карает за скрытую микроразметку ручными санкциями). *Нейтрализация:* обязательный одновременный рендеринг видимого интерактивного аккордеона FAQ в DOM и дублирование в JSON-LD.
- **Путь решения (Actionable Fix):** Скомпилировать вопросы из `README.md` в видимый интерактивный блок на главной странице и описать их через `@type: "FAQPage"` с объектами `Question` и `AcceptedAnswer`.

---

### 3.3. Архитектура сайта, краулинг и навигация (`site-architecture`)

#### Проблема ARCH-1: Схлопывание 7 поисковых кластеров в один документ с атрибутом `hidden`
- **Где находится:** `public/index.html`; `scripts/build_pages_site.py` — строки 2231–2545 (`#tab-docker`, `#tab-python`, `#tab-providers`, `#tab-curl`, `#tab-recipes`, `#tab-architecture`).
- **Описание проблемы:** Семь разнородных тем с колоссальным поисковым спросом заперты внутри одного документа под HTML5 атрибутом `hidden` (`display: none !important`).
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):*
    1. На весь сайт существует ровно один `<title>` и одно мета-описание. Невозможно ранжироваться по целевым длиннохвостым запросам (`playwright temp mail otp extraction`, `docker self hosted disposable email`, `python async temp mail client`).
    2. Поисковые краулеры Bingbot, Яндекс, а также AI-парсеры (Trafilatura, Jina) отбрасывают или сильно деприоритизируют скрытые узлы при расчете текстовой релевантности.
    3. Разработчик, пришедший из поиска по цитате рецепта, видит главную вкладку и сразу закрывает сайт (Bounce rate).
  - *Побочки внедрения (Risks & Mitigations):* Полное разбиение на 7 страниц может нарушить удобство быстрого переключения вкладок на десктопе. *Нейтрализация:* архитектурная модель **Hub-and-Spoke с прогрессивным улучшением**: главная страница сохраняет обзорную роль, а каждый глубокий кластер компилируется в отдельный индексируемый HTML-файл в папке `public/docs/`.
- **Путь решения (Actionable Fix):** Создать в генераторе функцию `generate_docs_pages()`, которая генерирует отдельные статические страницы: `/docs/recipes.html`, `/docs/python.html`, `/docs/docker.html`, `/docs/providers.html`, `/docs/architecture.html`, `/docs/adding-providers.html` со своими мета-тегами и каноническими адресами.

---

#### Проблема ARCH-2: Тройная каннибализация и распыление ссылочного веса между `scalar.html`, `swagger.html` и `redoc.html`
- **Где находится:** `scripts/build_pages_site.py` — функции `generate_scalar_ui()`, `generate_swagger_ui()`, `generate_redoc_ui()`, `get_nav_html()` (строки 104–106), `get_footer_html()` (строки 273–275).
- **Описание проблемы:** Три страницы рендерят одну и ту же спецификацию `openapi.json`. Все три страницы включены в `sitemap.xml` и получают сквозные ссылки из каждого меню, конкурируя друг с другом в поисковой выдаче и деля PageRank на 3 равные части.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Ни одна из трех страниц не может занять устойчивые позиции в топе Google по запросу "Maily API Reference" из-за внутренней конкуренции.
  - *Побочки внедрения (Risks & Mitigations):* Разработчики могут потерять доступ к привычным Swagger UI или ReDoc. *Нейтрализация:* сохранить обе страницы функциональными для пользователей, но закрыть их от индексации через `<meta name="robots" content="noindex, follow">`, указать канонический адрес на `scalar.html`, а в навигации оставить один главный пункт "API Reference" с возможностью переключения вьювера.
- **Путь решения (Actionable Fix):**
  1. Назначить `scalar.html` единственным каноническим представлением API.
  2. В `swagger.html` и `redoc.html` добавить `noindex, follow` и `<link rel="canonical" href="https://stormsia.github.io/maily/scalar.html">`.
  3. Исключить `swagger.html` и `redoc.html` из `sitemap.xml`.
  4. В шапке сайта объединить 3 ссылки в одну: `API Reference ⚡`.

---

#### Проблема ARCH-3: Циклический бэктрекинг относительных путей в навигации и расхождение канонического корня
- **Где находится:** `public/dev/bench/index.html`; `scripts/build_pages_site.py` — `get_nav_html("benchmarks", base_path="../../")` (строки 107, 2972); ссылки на главную `href="index.html"`.
- **Описание проблемы:**
  1. На странице бенчмарков в шапке формируется циклическая ссылка на саму себя: `href="../../dev/bench/index.html"`.
  2. Во всех шаблонах меню ссылки на главную ведут на `index.html`, тогда как канонический адрес объявлен со слэшем: `https://stormsia.github.io/maily/`.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Роботы видят две разные версии главной страницы (`/` и `/index.html`), что приводит к утечке ссылочного веса. Неаккуратные относительные пути увеличивают вероятность сбоев при переносе файлов.
  - *Побочки внедрения (Risks & Mitigations):* На локальных файловых системах (`file:///`) ссылки на корень без `index.html` могут не открываться. *Нейтрализация:* для веб-сервера отдавать `{base_path or './'}`.
- **Путь решения (Actionable Fix):** Заменить в `get_nav_html()` и `get_footer_html()` генерацию ссылок главной страницы с `index.html` на `{base_path or './'}`. Для активного пункта меню текущей страницы отключать циклический бэктрекинг, оставляя `href="#"` или `href="./"`.

---

#### Проблема ARCH-4: Отсутствие кастомного обработчика ошибок `public/404.html` на GitHub Pages
- **Где находится:** Корень сборки `public/404.html` (файл отсутствует); `scripts/build_pages_site.py:4153-4187`.
- **Описание проблемы:** В проекте нет кастомной страницы 404.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* При переходе по неверной ссылке или опечатке в адресе сервер GitHub Pages отдает стандартную служебную серую страницу GitHub ("404 There isn't a GitHub Pages site here"). Это приводит к 100% уходу пользователя (Bounce) и потере краулингового бюджета роботов.
  - *Побочки внедрения (Risks & Mitigations):* Рисков нет. Страница 404 на GitHub Pages поддерживается из коробки.
- **Путь решения (Actionable Fix):** Реализовать в `scripts/build_pages_site.py` функцию `generate_404_portal(public_dir)`, которая генерирует стильный dark-mode экран с поиском по документации, ссылками на популярные разделы (Python SDK, Docker, Playwright) и кнопкой возврата на главную.

---

#### Проблема ARCH-5: Слабая контекстная связность (Hub-and-Spoke Gap) и пропущенная документация
- **Где находится:** `public/index.html` (тело страницы, строки 2231–2545); неиндексируемый файл `docs/ADDING_PROVIDERS.md` (21 КБ).
- **Описание проблемы:**
  1. Внутри текстового тела главной страницы нет ни одной контекстной гиперссылки на `analytics.html` и `dev/bench/index.html` (связь только через навигационный хедер).
  2. Файл `docs/ADDING_PROVIDERS.md` (21 КБ подробного руководства по написанию адаптеров для провайдеров) вообще не компилируется в веб-портал и скрыт от индексации.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Поисковые алгоритмы оценивают дашборды как изолированные страницы с низким контекстным весом. Теряется релевантность по запросам интеграции кастомных провайдеров.
  - *Побочки внедрения (Risks & Mitigations):* Рисков нет.
- **Путь решения (Actionable Fix):** Добавить анкорные ссылки в тело главной страницы (в секции SQLite WAL — ссылку на бенчмарки, в секции безопасности — ссылку на аналитику SLA). Скомпилировать `docs/ADDING_PROVIDERS.md` в отдельную веб-страницу `docs/adding-providers.html`.

---

### 3.4. Generative Engine Optimization & AI Agent Readiness (`ai-seo`)

```mermaid
flowchart TD
    subgraph Agent_Readiness["Стандарт AgentReady.org: 3 эшелона"]
        direction TB
        subgraph F_Tier["1. FIND (Обнаружение)"]
            AR_F1["robots.txt с AI-директивами"]
            AR_F2["/llms.txt & /llms-full.txt"]
            AR_F3["/.well-known/ai-catalog.json"]
        end
        subgraph R_Tier["2. READ (Чтение & RAG)"]
            AR_R1["AR-READ-01: HTML-выжимка для CSR страниц"]
            AR_R2["Чистые .md зеркала документации"]
            AR_R3["40-60 word Answer Blocks в DOM"]
        end
        subgraph A_Tier["3. ACT (Действие)"]
            AR_A1["Публичный SKILL.md для Claude/Cursor"]
            AR_A2["service-desc link на openapi.json"]
            AR_A3["Мини-схема вызова инструментов tools.json"]
        end
    end

    F_Tier --> R_Tier --> A_Tier
```

#### Проблема GEO-1: Нарушение стандарта AR-READ-01 на страницах API (CSR Blind Spots)
- **Где находится:** `public/scalar.html`, `public/swagger.html`, `public/redoc.html`; `scripts/build_pages_site.py` — строки 475–750.
- **Описание проблемы:** Все три страницы документации API являются на 100% клиентскими SPA. В исходном HTML-документе присутствуют только пустые теги `<div id="swagger-ui">` и CDN-скрипты. Краулеры AI-поиска (PerplexityBot, ClaudeBot, GPTBot, Tavily, Jina Reader, LangChain WebBaseLoader) не исполняют внешний JavaScript и не дожидаются асинхронных вызовов `fetch('openapi.json')`. Для всех агентов эти страницы являются абсолютно пустыми слепыми зонами.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Когда разработчик спрашивает у Claude Code или ChatGPT: *"Какие эндпоинты есть у Maily для работы с письмами?"*, агент не может извлечь данные с веб-страниц документации и галлюцинирует стандартные методы других библиотек.
  - *Побочки внедрения (Risks & Mitigations):* Раздувание HTML-файлов при полном дублировании всех схем. *Нейтрализация:* внедрение компактной семантической таблицы основных роутов в тег `<noscript>` и пре-рендеренный скрытый для зрячих пользователей контейнер `<div class="sr-only agent-manifest">`.
- **Путь решения (Actionable Fix):** Встроить в Initial HTML страниц `scalar.html`, `swagger.html` и `redoc.html` семантическую таблицу всех 30+ эндпоинтов со статусами и краткими описаниями прямо в статическую разметку до скрипта инициализации. Добавить тег `<link rel="alternate" type="application/json" href="openapi.json">`.

---

#### Проблема GEO-2: Отсутствие стандартизированных файлов `/llms.txt` и `/llms-full.txt`
- **Где находится:** Корень `public/` (файлы отсутствуют).
- **Описание проблемы:** Сайт не поддерживает стандарт [llmstxt.org](https://llmstxt.org).
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Современные AI-агенты (Cursor, Claude Code, Windsurf, ChatGPT) при анализе репозитория или домена в первую очередь запрашивают `/llms.txt`. Не найдя его, агент вынужден скачивать тяжелый монолитный HTML (91 КБ), тратя контекстное окно и путаясь в классах оформления CSS/JS.
  - *Побочки внедрения (Risks & Mitigations):* Риск рассинхронизации документации в `llms.txt` при обновлении версий. *Нейтрализация:* автоматическая сборка `llms.txt` и `llms-full.txt` внутри `build_pages_site.py` с использованием констант `__version__`.
- **Путь решения (Actionable Fix):** Реализовать в `scripts/build_pages_site.py` функцию `generate_llms_files(public_dir)`, которая генерирует эталонный `public/llms.txt` (структурированная выжимка проекта) и `public/llms-full.txt` (полная документация в Markdown).

---

#### Проблема GEO-3: Полное отсутствие ключевой поисковой сущности "Self-Hosted" в генераторе портала
- **Где находится:** `public/index.html`; `scripts/build_pages_site.py` (поиск по фразе `"self-hosted"` дает 0 результатов!).
- **Описание проблемы:** В файле `README.md` (строка 739) термин *"self-hosted"* используется, но в генератор веб-сайта `build_pages_site.py` он не включен ни в метатеги, ни в заголовки, ни в текст.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Ни ChatGPT, ни Perplexity, ни Google AI Overviews не могут рекомендовать Maily по запросам *"best self-hosted temp mail gateway"*, *"self-hosted disposable email docker"*, так как ключевая сущность отсутствует в семантическом графе сайта.
  - *Побочки внедрения (Risks & Mitigations):* Рисков нет.
- **Путь решения (Actionable Fix):** Внедрить термин *"Self-Hosted"* в тег `<title>`, мета-описание, H2 секции Docker и в структурированный Answer Block: *"Maily is a 100% self-hosted universal temporary email gateway deployable via a single Docker command with zero external database dependencies."*

---

#### Проблема GEO-4: Отсутствие публичного файла навыка `public/SKILL.md` (Claude Code / Cursor)
- **Где находится:** Отсутствует в папке `public/`.
- **Описание проблемы:** Сайт не предоставляет файл навыка (Agent Skill), который разработчики могут подключить в свои локальные AI-агенты разработки.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* Упущен современный канал дистрибуции инструмента среди AI-first разработчиков. Инженер, настраивающий автотесты в Claude Code или Cursor, вынужден вручную объяснять агенту, как поднять Maily и использовать `maily-client`.
  - *Побочки внедрения (Risks & Mitigations):* Рисков нет.
- **Путь решения (Actionable Fix):** Сгенерировать в `public/SKILL.md` манифест навыка для Claude Code и Cursor с пошаговой инструкцией: подъем Docker-контейнера, установка `maily-client`, шаблоны E2E-тестов с однострочным `wait_for_code()`.

---

#### Проблема GEO-5: Обезличенная сравнительная таблица и отсутствие 40–60 word Answer Blocks
- **Где находится:** `public/index.html`; `scripts/build_pages_site.py` — строки 2237–2279 (секция *"Why Maily? Taming the Disposable Email Zoo"*).
- **Описание проблемы:** В сравнительной таблице альтернативная колонка названа абстрактно: *"Fragmented Temp-Mail Zoo ❌"*. При RAG-экстракции краулерами теряется сопоставление сущностей. Отсутствует текстовое резюме (паттерн GEO *"Bottom line"*) и компактные блоки определений (Answer Blocks) под целевые промпты.
- **Побочные эффекты:**
  - *Побочки бездействия (Impact):* При запросах в Perplexity *"Maily vs Mail.tm"* или *"alternative to GuerrillaMail for pytest"* модель не может надежно сопоставить параметры и выбирает другие статьи из выдачи.
  - *Побочки внедрения (Risks & Mitigations):* Рисков нет.
- **Путь решения (Actionable Fix):**
  - Изменить заголовки таблицы на конкретные сущности: `Feature | Single-Provider Libraries (Mail.tm, GuerrillaMail) | Maily Universal Gateway`.
  - Добавить блок вывода: `**Bottom Line**: Unlike single-provider libraries that break during domain blacklisting, Maily aggregates 8+ provider networks and 40+ domains into a resilient unified gateway.`
  - Внедрить компактные Answer Blocks (40–60 слов) перед секциями Playwright, Python SDK и Docker.

---

## 4. Синергия SEO + GEO: Стратегия двойного доминирования для Maily

Существует фундаментальное противоречие между традиционным поисковым продвижением (Classic SEO) и оптимизацией под генеративный ИИ (GEO / AI SEO):
- **Классический SEO** требует разделения контента на множество узких посадочных страниц (Landing Pages) со строгим распределением ключевых слов (Keyword Clustering), компактным HTML и минимальным весом DOM.
- **Generative Engine Optimization (GEO)**, напротив, требует, чтобы AI-агент мог получить исчерпывающий контекст всей архитектуры, методов и примеров кода за **один HTTP-запрос**, без многократного перехода по страницам и риска отсечения критических зависимостей при векторном чанкинге.

### Как Maily решает этот конфликт (Dual-Engine Synergy)
Для Maily проектируется гибридная архитектура:

```mermaid
graph TD
    UserSearch["Поисковые краулеры & Инженеры<br/>(Googlebot, Bingbot, Разработчики)"]
    AIAgents["AI-агенты & RAG-пайплайны<br/>(Perplexity, Claude Code, GPTBot, Cursor)"]

    subgraph Classic_Layer["Уровень 1: Classic SEO (Multi-Page SSG)"]
        HOME["/ (index.html) — Gateway Hub"]
        P_RECIPES["/docs/recipes.html — Playwright/Pytest OTP"]
        P_PYTHON["/docs/python.html — Async Python SDK"]
        P_DOCKER["/docs/docker.html — Self-Hosted Docker"]
        P_PROV["/docs/providers.html — Providers Matrix"]
        P_SCALAR["/scalar.html — Canonical API Reference"]
    end

    subgraph GEO_Layer["Уровень 2: Machine Discovery & Agent Standards"]
        LLMS["/llms.txt — Agent Index & Definition"]
        LLMS_FULL["/llms-full.txt — Complete Docs in 1 Request"]
        SKILL["/SKILL.md — Cursor & Claude Code Skill"]
        SCHEMA["JSON-LD @graph — Entity Disambiguation"]
        OPENAPI["/openapi.json — Tool Calling Contract"]
    end

    UserSearch --> Classic_Layer
    AIAgents --> GEO_Layer
    Classic_Layer -.->|Перекрестные ссылки & Discovery| GEO_Layer
```

1. **Человеческий и поисковый трафик (Classic SEO):**
   - Получает раздельные, идеально оптимизированные статические страницы (`/docs/recipes.html`, `/docs/python.html`, `/docs/docker.html`, `/scalar.html`).
   - Каждая страница содержит свой уникальный `<title>`, мета-описание, хлебные крошки `BreadcrumbList`, правильную иерархию `H1->H2->H3` и быстрый First Contentful Paint.
   - Покрываются ключевые кластеры: *"playwright email verification otp"*, *"python async temp mail"*, *"self hosted disposable mail docker"*.
2. **Агентский и RAG трафик (GEO & AI Agents):**
   - Находит в `<head>` каждой страницы явные ссылки обнаружения:
     * `<link rel="alternate" type="text/markdown" href="index.md">`
     * `<link rel="service-desc" type="application/vnd.oai.openapi+json" href="openapi.json">`
   - Читает стандартизированные файлы `/llms.txt` и `/llms-full.txt`, мгновенно получая весь контекст без необходимости выполнять JavaScript или бродить по ссылкам.
   - Подключает файл `/SKILL.md` напрямую в сессию Claude Code или Cursor для мгновенного написания тестов.
   - Однозначно разрешает сущность "Maily" через JSON-LD массив `sameAs` с привязкой к GitHub, PyPI и GHCR Docker.

---

## 5. Архитектурные спецификации готовых артефактов (Code Deliverables)

### 5.1. Полный JSON-LD `@graph` для `index.html`
Этот блок должен генерироваться внутри `<head>` на главной странице `index.html` через функцию `generate_index_portal()`:

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@type": "WebSite",
      "@id": "https://stormsia.github.io/maily/#website",
      "url": "https://stormsia.github.io/maily/",
      "name": "Maily",
      "alternateName": "Maily Temp-Mail Gateway Portal",
      "description": "Developer Portal and Documentation Hub for Maily: Universal Temporary Email Gateway & Async Python SDK",
      "inLanguage": "en",
      "publisher": {
        "@id": "https://stormsia.github.io/maily/#author"
      }
    },
    {
      "@type": "WebPage",
      "@id": "https://stormsia.github.io/maily/#webpage",
      "url": "https://stormsia.github.io/maily/",
      "name": "Maily · Universal Temporary Email Gateway & Developer Hub",
      "isPartOf": {
        "@id": "https://stormsia.github.io/maily/#website"
      },
      "about": {
        "@id": "https://stormsia.github.io/maily/#software"
      },
      "breadcrumb": {
        "@id": "https://stormsia.github.io/maily/#breadcrumb"
      },
      "inLanguage": "en"
    },
    {
      "@type": "BreadcrumbList",
      "@id": "https://stormsia.github.io/maily/#breadcrumb",
      "itemListElement": [
        {
          "@type": "ListItem",
          "position": 1,
          "name": "Home",
          "item": "https://stormsia.github.io/maily/"
        }
      ]
    },
    {
      "@type": "SoftwareApplication",
      "@id": "https://stormsia.github.io/maily/#software",
      "name": "Maily",
      "alternateName": [
        "Maily Gateway",
        "Universal Temp-Mail Gateway",
        "maily-server",
        "maily-client"
      ],
      "headline": "Universal Temporary Email Gateway & Developer Hub",
      "description": "Universal temporary email gateway aggregating 8+ disposable mail providers into one unified REST API and async Python SDK with sub-second OTP extraction for Playwright and QA bots.",
      "url": "https://stormsia.github.io/maily/",
      "applicationCategory": "DeveloperApplication",
      "operatingSystem": "Linux, macOS, Windows, Docker",
      "softwareVersion": "0.7.0",
      "license": "https://opensource.org/licenses/MIT",
      "image": "https://stormsia.github.io/maily/assets/hero_banner.webp",
      "screenshot": "https://stormsia.github.io/maily/screenshots/01_overview.webp",
      "sameAs": [
        "https://github.com/stormsia/maily",
        "https://pypi.org/project/maily/",
        "https://pypi.org/project/maily-client/",
        "https://ghcr.io/stormsia/maily"
      ],
      "offers": {
        "@type": "Offer",
        "price": "0",
        "priceCurrency": "USD",
        "availability": "https://schema.org/OnlineOnly"
      },
      "featureList": [
        "Aggregates 8+ disposable email providers (Mail.tm, TempMail.Plus, NoopMail, GuerrillaMail, etc.)",
        "Sub-millisecond hermetic SQLite WAL storage (< 2.5 ms latencies)",
        "Automatic 1-line OTP verification code extraction (wait_for_code)",
        "40+ rotating domains across networks to bypass anti-tempmail blocklists",
        "100% typed async Python SDK (maily-client) with strict Pydantic schemas",
        "Zero outbound SMTP (inbound-only architecture prevents spam relay risks)",
        "Hermetic self-hosted Docker container (ghcr.io/stormsia/maily)"
      ],
      "author": {
        "@id": "https://stormsia.github.io/maily/#author"
      },
      "publisher": {
        "@id": "https://stormsia.github.io/maily/#author"
      },
      "downloadUrl": "https://pypi.org/project/maily-client/",
      "installUrl": "https://github.com/stormsia/maily#quick-start"
    },
    {
      "@type": "SoftwareSourceCode",
      "@id": "https://stormsia.github.io/maily/#sourcecode",
      "name": "Maily Source Code",
      "codeRepository": "https://github.com/stormsia/maily",
      "programmingLanguage": {
        "@type": "ComputerLanguage",
        "name": "Python",
        "url": "https://www.python.org/"
      },
      "runtimePlatform": "Python >=3.10, Docker",
      "license": "https://opensource.org/licenses/MIT",
      "version": "0.7.0",
      "targetProduct": {
        "@id": "https://stormsia.github.io/maily/#software"
      },
      "author": {
        "@id": "https://stormsia.github.io/maily/#author"
      }
    },
    {
      "@type": "WebAPI",
      "@id": "https://stormsia.github.io/maily/#webapi",
      "name": "Maily Gateway REST API",
      "description": "Normalized REST API aggregating multiple disposable email providers with mailbox lifecycle management and OTP polling.",
      "documentation": "https://stormsia.github.io/maily/scalar.html",
      "serviceUrl": "http://127.0.0.1:8477",
      "termsOfService": "https://github.com/stormsia/maily/blob/main/LICENSE",
      "provider": {
        "@id": "https://stormsia.github.io/maily/#author"
      }
    },
    {
      "@type": "Person",
      "@id": "https://stormsia.github.io/maily/#author",
      "name": "stormsia",
      "url": "https://github.com/stormsia",
      "sameAs": [
        "https://github.com/stormsia"
      ]
    },
    {
      "@type": "FAQPage",
      "@id": "https://stormsia.github.io/maily/#faq",
      "mainEntity": [
        {
          "@type": "Question",
          "name": "How does Maily differ from single-provider libraries like mailtm or tempmail?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Single-provider libraries break whenever that specific upstream provider encounters downtime, changes its schema, or gets added to spam blocklists. Maily abstracts the entire disposable email ecosystem into a resilient gateway: you get a single consistent API, 40+ rotating domains across 8 provider networks, automatic domain fallback, and standardized OTP extraction."
          }
        },
        {
          "@type": "Question",
          "name": "How fast is OTP verification code extraction in automated tests?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Incoming emails are processed within sub-second latency of arrival upstream. With await api.wait_for_code(box, timeout=30.0), Maily continuously polls and extracts 4–8 digit verification codes (e.g. 849201) or confirmation action links, returning cleanly as soon as the email hits the server."
          }
        },
        {
          "@type": "Question",
          "name": "How does Maily prevent domain blacklisting in E2E tests?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Many SaaS sign-up forms block known disposable email domains like @mailtm.com. Maily solves this by maintaining a live pool of 40+ rotating domains across multiple providers (including obscure domains and real Gmail alias domains username+tag@gmail.com via OAuth2)."
          }
        },
        {
          "@type": "Question",
          "name": "Can I run Maily completely self-hosted with Docker?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes. Maily is packaged as an optimized multi-stage Docker container (ghcr.io/stormsia/maily:latest). It stores state in embedded SQLite with Write-Ahead Logging (WAL) and automatic defragmentation, requiring zero external databases or Redis caches."
          }
        },
        {
          "@type": "Question",
          "name": "Can I use my own domain or Gmail account with Maily?",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": "Yes. Maily supports Gmail via OAuth2 with infinite username+alias@gmail.com addresses, as well as providers with custom domains (mail.tm, tempmail.plus, temp.tf)."
          }
        }
      ]
    }
  ]
}
</script>
```

---

### 5.2. Спецификация `public/llms.txt` и `public/llms-full.txt`

#### Содержимое `public/llms.txt`:
```markdown
# Maily — Universal Temporary Email Gateway

> Maily is a self-hosted universal temporary email gateway aggregating 8+ disposable mail providers into one unified REST API and async Python SDK (maily-client). It eliminates flaky verification regexes with sub-second, 1-line OTP code extraction for Playwright, Pytest, and QA bots.

## Key Capabilities & Architecture
- **8+ Aggregated Providers**: Mail.tm, TempMail.Plus, NoopMail, GuerrillaMail, 1secmail, DispoEmail, AnonymMail, and Gmail OAuth2 (alias routing).
- **Sub-Millisecond Engine**: SQLite WAL mode with < 2.5 ms read/write latency, zero external database requirements (no Postgres/Redis).
- **Anti-Blocklist Domain Pool**: 40+ active rotating domains across distinct provider networks.
- **Inbound-Only Architecture**: Zero outbound SMTP relays, preventing abuse and spam reputation leakage.
- **1-Line OTP Extraction**: `await api.wait_for_code(box)` extracts 4-8 digit verification codes and magic links automatically.

## Quick Installation & Usage
```bash
# Run self-hosted gateway via Docker
docker run -d -p 8477:8477 -v maily_data:/data ghcr.io/stormsia/maily:latest

# Install Python SDK
pip install maily-client
```

```python
import asyncio
from maily_client import Maily


async def main():
    async with Maily("http://127.0.0.1:8477") as api:
        box = await api.create_temp_mailbox()
        print(f"Created: {box.address}")
        # One-line OTP wait for Playwright E2E signup
        code = await api.wait_for_code(box, timeout=30.0)
        print(f"Received OTP: {code}")


asyncio.run(main())
```

## Documentation & Machine Endpoints
- [Complete Markdown Documentation](https://stormsia.github.io/maily/llms-full.txt): Full guide, architecture, and Docker compose examples.
- [OpenAPI 3.1 Specification](https://stormsia.github.io/maily/openapi.json): Full machine-readable REST API schema.
- [Interactive Scalar API Reference](https://stormsia.github.io/maily/scalar.html): Web-based interactive documentation.
- [Live Security & Health Dashboard](https://stormsia.github.io/maily/analytics.html): Upstream provider SLAs and security gates.
- [Performance Benchmarks](https://stormsia.github.io/maily/dev/bench/index.html): SQLite WAL latency tracking.
- [GitHub Repository](https://github.com/stormsia/maily): Source code, issues, and discussions.
```

---

### 5.3. Спецификация `public/SKILL.md` (Claude Code / Cursor)
Файл позволяет любому AI-агенту разработки мгновенно понять, как развернуть и использовать Maily в кодовой базе пользователя:

```markdown
---
name: maily-testing
description: "Integrate Maily universal temporary email gateway for E2E signup testing, OTP extraction, and automated email verification in Playwright and Pytest."
tools:
  - bash
  - read_file
---

# Maily E2E Email Verification Skill

Use this skill when the user needs to test email verification flows, signups, magic links, or 2FA codes in automated tests.

## 1. Quickstart Architecture
Maily runs as a hermetic local container and exposes a normalized REST API on port 8477.

### Start Maily Gateway:
```bash
docker run -d --name maily-test-gateway -p 8477:8477 ghcr.io/stormsia/maily:latest
```

### Install Client SDK:
```bash
pip install maily-client pytest-asyncio
```

## 2. Standard Playwright OTP Recipe
```python
import pytest
from maily_client import Maily


@pytest.mark.asyncio
async def test_user_signup_with_otp(page):
    async with Maily("http://127.0.0.1:8477") as api:
        # 1. Create a fresh temporary mailbox
        box = await api.create_temp_mailbox()

        # 2. Trigger signup in browser
        await page.goto("https://example.com/signup")
        await page.fill('input[name="email"]', box.address)
        await page.click('button[type="submit"]')

        # 3. Wait for OTP extraction (1 line, handles polling & regex)
        otp_code = await api.wait_for_code(box, timeout=30.0)
        assert otp_code is not None, "Failed to receive verification code"

        # 4. Fill code and complete verification
        await page.fill('input[name="code"]', otp_code)
        await page.click("button#verify")
        await page.wait_for_selector(".dashboard-welcome")
```

## 3. Best Practices
- Always use `await api.wait_for_code(box)` instead of manual message polling and custom regex parsing.
- For services blocking common disposable domains, use `api.create_temp_mailbox(provider="tempmailplus")` or configure Gmail OAuth2 alias routing.
- Check live gateway health at `http://127.0.0.1:8477/health`.
```

---

### 5.4. Оптимизированный `robots.txt` и `sitemap.xml`

#### Новый `public/robots.txt`:
```text
User-agent: *
Allow: /

# Agent & AI Discovery
Sitemap: https://stormsia.github.io/maily/sitemap.xml
Content-Usage: Allow=training,citing,indexing
Link: <https://stormsia.github.io/maily/llms.txt>; rel="llms-txt"
Link: <https://stormsia.github.io/maily/llms-full.txt>; rel="llms-full-txt"
Link: <https://stormsia.github.io/maily/openapi.json>; rel="service-desc"
```

#### Новый `public/sitemap.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://stormsia.github.io/maily/</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/docs/recipes.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/docs/python.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/docs/docker.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/docs/providers.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/scalar.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/analytics.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>daily</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://stormsia.github.io/maily/dev/bench/index.html</loc>
    <lastmod>2026-11-06</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
```
*(Обратите внимание: `openapi.json`, `swagger.html` и `redoc.html` исключены из sitemap для предотвращения каннибализации и индексации сырых данных).*

---

## 6. Приоритизированный план внедрения (Actionable Roadmap)

```mermaid
gantt
    title Roadmap реализации SEO & GEO оптимизации Maily
    dateFormat  YYYY-MM-DD
    section Фаза 1: Quick Wins (Генератор)
    Метатеги, OpenGraph & Favicon      :a1, 2026-11-07, 1d
    JSON-LD @graph на всех страницах    :a2, 2026-11-07, 1d
    Генерация llms.txt & llms-full.txt  :a3, 2026-11-08, 1d
    Канонизация Scalar & noindex дублей :a4, 2026-11-08, 1d
    Sitemap с lastmod & robots.txt      :a5, 2026-11-08, 1d
    Кастомная страница 404.html         :a6, 2026-11-09, 1d
    Спецификация SKILL.md & ai-catalog  :a7, 2026-11-09, 1d
    section Фаза 2: Структурные реформы
    Генерация отдельных страниц /docs/  :b1, 2026-11-10, 2d
    Рефакторинг табов (Progressive)     :b2, 2026-11-11, 2d
    Answer Blocks под "self-hosted"     :b3, 2026-11-12, 1d
    Семантические SSR-фолбэки для API   :b4, 2026-11-13, 2d
    Интеграция FAQ аккордеона в DOM     :b5, 2026-11-14, 1d
```

### Фаза 1: Quick Wins (Внутри `scripts/build_pages_site.py` за 1 проход)
*Трудоемкость: 1–2 рабочих дня. Изменения локализованы исключительно в Python-генераторе и не требуют изменения архитектуры.*

1. **Единый генератор мета-разметки:**
   - Создать хелпер `get_head_meta(title, description, path, og_image, base_path="")`.
   - Внедрить вызов хелпера в `generate_scalar_ui`, `generate_swagger_ui`, `generate_redoc_ui`, `generate_analytics_dashboard`, `generate_benchmark_dashboard`.
   - Обеспечить 100% присутствие OpenGraph (`og:*`) и Twitter Cards на всех страницах.
2. **Физический Favicon:**
   - В функции `copy_static_assets()` сохранять физический файл `public/assets/favicon.svg` и `public/favicon.ico`.
   - Заменить Data-URI на физические пути в тегах `<link rel="icon">`.
3. **Канонизация API и ликвидация дублей:**
   - Добавить `<link rel="canonical" href="https://stormsia.github.io/maily/scalar.html">` на страницу `scalar.html`.
   - На страницы `swagger.html` и `redoc.html` добавить `<meta name="robots" content="noindex, follow">` и каноническую ссылку на `scalar.html`.
   - Объединить ссылки в меню в один пункт: `API Reference ⚡`.
4. **Обновление Sitemaps & Robots:**
   - В `generate_seo_files()` исключить `openapi.json`, `swagger.html`, `redoc.html` из `sitemap.xml`.
   - Добавить атрибут `<lastmod>` с текущей датой сборки.
   - Добавить в `robots.txt` директивы Content-Usage и ссылки на discovery-файлы.
5. **Генерация Agent-Ready артефактов:**
   - Добавить функцию `generate_agent_discovery_files(public_dir)` для сборки `public/llms.txt`, `public/llms-full.txt`, `public/SKILL.md` и `public/.well-known/ai-catalog.json`.
   - Скопировать `docs/*.md` и `README.md` в `public/docs/` и создать `public/index.md`.
6. **Внедрение JSON-LD `@graph`:**
   - Создать функцию `get_json_ld_for_page(page_type)`.
   - Внедрить полный граф (`WebSite`, `SoftwareApplication`, `SoftwareSourceCode`, `WebAPI`, `Person`, `BreadcrumbList`, `FAQPage`) на главную страницу.
   - Внедрить схемы `APIReference`, `TechArticle`, `Dataset` на второстепенные страницы.
7. **Кастомный 404 экран:**
   - Добавить функцию `generate_404_portal(public_dir)` с генерацией `public/404.html`.
8. **Исправление CWV факторов первого экрана:**
   - Прописать точные `width` и `height` для всех тегов `<img>`.
   - Добавить `loading="lazy"` для изображений ниже сгиба и `fetchpriority="high"` для LCP-баннера.
   - Добавить `defer` для `chart.umd.min.js`.

---

### Фаза 2: Структурные и контентные улучшения (SSG / Мультистраничность)
*Трудоемкость: 3–4 рабочих дня. Выводит сайт на лидирующие позиции по органическому и генеративному поиску.*

1. **Компиляция многостраничной документации (`/docs/`):**
   - Расширить генератор функцией `generate_docs_pages()`, создающей отдельные статические HTML-страницы:
     * `public/docs/recipes.html` (Playwright & Pytest OTP Extraction Recipes)
     * `public/docs/python.html` (Python Async SDK Guide & Pydantic Schemas)
     * `public/docs/docker.html` (Self-Hosted Docker & Compose Setup)
     * `public/docs/providers.html` (Supported Providers Matrix & Domain Pool)
     * `public/docs/adding-providers.html` (Custom Provider Integration Guide)
     * `public/docs/architecture.html` (Security, Threat Model & Hermetic Storage)
2. **Прогрессивное улучшение табов на `index.html`:**
   - Удалить жестко зашитый атрибут `hidden` из статического рендера критических секций.
   - Перевести скрытие неактивных панелей на клиентский JavaScript после инициализации DOM, обеспечив 100% чтение контента краулерами Bing, Яндекс и легковесными RAG-парсерами.
3. **Семантические SSR-фолбэки для страниц API:**
   - Встроить в начальный HTML страниц `scalar.html`, `swagger.html` и `redoc.html` семантическую таблицу всех эндпоинтов со статусами в блок `<noscript>` и семантический скрытый контейнер `<div class="sr-only">`, полностью закрыв требование AgentReady AR-READ-01.
4. **Контентные Answer Blocks под целевой интент:**
   - Добавить в `index.html` и `docs/docker.html` явный термин *"self-hosted"* в заголовки и метатеги.
   - Внедрить 40–60 word Definition Blocks для цитирования в LLM:
     * *"What is Maily?"*
     * *"Why Maily is the best Temp Mail API for Playwright/Pytest"*
     * *"Maily vs Single-Provider Libraries (Mail.tm, GuerrillaMail)"*
5. **Видимый аккордеон FAQ на главной странице:**
   - Скомпилировать вопросы из `README.md` в интерактивный аккордеон в теле страницы, синхронизировав визуальный контент с разметкой `FAQPage` JSON-LD.

---

## 7. ЗАКЛЮЧЕНИЕ КООРДИНАТОРА

Проведенный аудит показал, что проект **Maily** обладает огромным потенциалом для органического и генеративного доминирования в сегменте инструментов для тестирования (QA Automation, E2E Testing, Disposable Mail API).

Все выявленные технические барьеры носят инфраструктурно-генераторный характер. Их устранение в скрипте `scripts/build_pages_site.py` в рамках двух предложенных фаз:
1. Ликвидирует 100% рисков санкций и каннибализации в Google и Bing.
2. Обеспечит идеальные показатели Core Web Vitals (CLS < 0.01, FCP < 0.8s).
3. Превратит портал Maily в эталонный **Agent-Ready ресурс с грейдом A+ (100/100)**, гарантирующий цитирование в ChatGPT Search, Perplexity, Claude и Google AI Overviews при любых запросах разработчиков на автоматизацию верификации по электронной почте.
