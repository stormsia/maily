"""Test static GitHub Pages site generator (scripts/build_pages_site.py)."""

from __future__ import annotations

import json
from pathlib import Path

from build_pages_site import (
    __version__,
    calculate_provider_sla,
    copy_static_assets,
    extract_benchmarks,
    generate_agent_discovery_files,
    generate_analytics_dashboard,
    generate_index_portal,
    generate_openapi_schema,
    generate_redoc_ui,
    generate_scalar_ui,
    generate_seo_files,
    generate_swagger_ui,
    get_footer_html,
    get_head_meta,
    get_json_ld_for_page,
    get_nav_html,
    load_provider_health,
    render_docs_shell,
)

ROOT = Path(__file__).resolve().parents[1]


def test_nav_html_generation():
    root_nav = get_nav_html("docs", base_path="")
    assert 'href="./"' in root_nav
    assert 'href="scalar.html"' in root_nav
    assert 'href="dev/bench/index.html"' in root_nav
    assert 'href="analytics.html"' in root_nav
    assert 'href="openapi.json"' in root_nav
    assert "portal-nav" in root_nav
    assert f'<span class="brand-badge">v{__version__}</span>' in root_nav

    sub_nav = get_nav_html("benchmarks", base_path="../../")
    assert 'href="../../"' in sub_nav
    assert 'href="../../scalar.html"' in sub_nav
    assert 'href="../../analytics.html"' in sub_nav


def test_footer_html_generation():
    footer = get_footer_html(base_path="")
    assert "portal-footer" in footer
    assert "Universal Temporary Email Gateway" in footer
    assert "MIT License" in footer


def test_build_pages_site_artifacts(tmp_path: Path):
    # 1. Assets copy and Jekyll bypass
    copy_static_assets(tmp_path)
    assert (tmp_path / "assets" / "hero_banner.webp").is_file()
    assert (tmp_path / "assets" / "infographic_zoo.webp").is_file()
    assert (tmp_path / "assets" / "logo.png").is_file()
    assert (tmp_path / "screenshots" / "01_overview.webp").is_file()
    assert (tmp_path / ".nojekyll").is_file()

    # 2. SEO files
    generate_seo_files(tmp_path)
    assert (tmp_path / "robots.txt").is_file()
    robots_txt = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://stormsia.github.io/maily/sitemap.xml" in robots_txt

    assert (tmp_path / "sitemap.xml").is_file()
    sitemap_xml = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://stormsia.github.io/maily/</loc>" in sitemap_xml
    assert "<loc>https://stormsia.github.io/maily/scalar.html</loc>" in sitemap_xml

    # 3. OpenAPI schema
    schema = generate_openapi_schema(tmp_path)
    assert (tmp_path / "openapi.json").is_file()
    raw_json = json.loads((tmp_path / "openapi.json").read_text(encoding="utf-8"))
    assert "paths" in raw_json
    assert "/v1/mailboxes" in raw_json["paths"]
    assert "/health" in raw_json["paths"]
    assert schema["info"]["title"] == "maily"

    # 4. Master Developer Portal index.html
    generate_index_portal(tmp_path)
    index_html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in index_html
    assert "Maily · Universal Temporary Email Gateway" in index_html
    assert 'id="tab-overview"' in index_html
    assert 'id="tab-explorer"' in index_html
    assert 'id="tab-docker"' in index_html
    assert 'id="tab-python"' in index_html
    assert 'id="tab-providers"' in index_html
    assert 'id="tab-curl"' in index_html
    assert 'id="tab-recipes"' in index_html
    assert 'id="tab-architecture"' in index_html
    assert "simCreateMailbox" not in index_html
    assert "simExtractOtp" not in index_html
    assert "Interactive Inbound Email & OTP Simulator" not in index_html
    assert "Live Interactive Demo" not in index_html
    assert "sim-sub-btn" not in index_html
    assert "sim-input" not in index_html
    assert "hero-tab-btn" in index_html
    assert 'data-tab="overview"' in index_html
    assert 'data-tab="explorer"' in index_html
    assert 'data-tab="docker"' in index_html
    assert 'data-tab="python"' in index_html
    assert 'id="ptab-overview"' in index_html
    assert 'id="ptab-explorer"' in index_html
    assert 'aria-labelledby="ptab-overview"' in index_html
    assert 'aria-controls="tab-overview"' in index_html
    assert "scrollIntoView" in index_html
    assert "switchPortalTab" in index_html
    assert "handleHashRoute" in index_html
    assert "history.pushState" in index_html
    assert "popstate" in index_html
    assert 'role="tablist"' in index_html
    assert 'role="tab"' in index_html
    assert 'role="tabpanel"' in index_html
    assert "wait_for_code" in index_html
    assert "wait_for_link" in index_html
    assert "create_temp_mailbox" in index_html
    assert "RateLimitError" in index_html
    assert "UpstreamProviderError" in index_html
    assert "MailyRateLimitError" not in index_html  # Verify no hallucinated exception classes
    assert "cfg-host" in index_html
    assert "cfg-key" in index_html
    assert "localStorage" in index_html
    assert "switchScreenshot" in index_html
    assert "hero-banner-container" in index_html
    assert "swagger-ui" in index_html  # Embedded dark swagger styling present
    assert "portal-footer" in index_html

    # 5. Scalar UI
    generate_scalar_ui(tmp_path)
    scalar_html = (tmp_path / "scalar.html").read_text(encoding="utf-8")
    assert "@scalar/api-reference" in scalar_html
    assert "openapi.json" in scalar_html
    assert "portal-nav" in scalar_html
    assert "embedded-view" in scalar_html

    # 6. Swagger UI
    generate_swagger_ui(tmp_path)
    swagger_html = (tmp_path / "swagger.html").read_text(encoding="utf-8")
    assert "SwaggerUIBundle" in swagger_html
    assert "swagger-ui" in swagger_html
    assert "portal-nav" in swagger_html
    assert "embedded-view" in swagger_html

    # 7. ReDoc UI
    generate_redoc_ui(tmp_path)
    redoc_html = (tmp_path / "redoc.html").read_text(encoding="utf-8")
    assert "redoc" in redoc_html
    assert 'id="redoc-container"' in redoc_html
    assert "Redoc.init" in redoc_html
    assert "redoc.standalone.js" in redoc_html
    assert "portal-nav" in redoc_html
    assert "embedded-view" in redoc_html
    assert '"primary": {"main": "#7c6cff"}' in redoc_html

    # 8. Analytics Dashboard
    generate_analytics_dashboard(tmp_path)
    analytics_html = (tmp_path / "analytics.html").read_text(encoding="utf-8")
    assert "Security, Quality & Operational Observability" in analytics_html
    assert "provider-card" in analytics_html
    assert "health-bar-container" in analytics_html
    assert "Gateway SLA" in analytics_html
    assert "How SLA & High-Availability are Measured" in analytics_html
    assert "168 hourly probes" in analytics_html
    assert "Gitleaks" in analytics_html
    assert "Trivy" in analytics_html
    assert "CodeQL" in analytics_html
    assert "portal-footer" in analytics_html

    # 9. Benchmarks extraction and dashboard
    extract_benchmarks(tmp_path)
    assert (tmp_path / "dev" / "bench" / "index.html").is_file()
    assert (tmp_path / "dev" / "bench" / "data.js").is_file()
    bench_html = (tmp_path / "dev" / "bench" / "index.html").read_text(encoding="utf-8")
    assert "portal-nav" in bench_html
    assert "benchmark-chart" in bench_html
    assert "Visual Latency Spectrum" in bench_html
    assert "Production Interpretation" in bench_html
    assert "BENCHMARK_METADATA" in bench_html
    assert "Percentiles (p50 · p95 · p99)" in bench_html


def test_load_provider_health():
    providers = load_provider_health()
    assert isinstance(providers, dict)
    assert len(providers) > 0
    assert "dispoemail.org" in providers or "mail.tm" in providers


def test_calculate_provider_sla():
    # Operational with 0 failures
    uptime, text, color, icon = calculate_provider_sla("operational", 0)
    assert uptime == 99.95
    assert "Operational" in text
    assert icon == "🟢"

    # Degraded with 1 failure (168 hourly checks per week)
    uptime_deg, text_deg, color_deg, icon_deg = calculate_provider_sla("degraded", 1)
    assert 99.0 <= uptime_deg <= 99.8
    assert "Degraded (1 fail)" in text_deg
    assert icon_deg == "🟡"

    # Outage with 3 failures
    uptime_out, text_out, color_out, icon_out = calculate_provider_sla("outage", 3)
    assert 95.0 <= uptime_out <= 99.0
    assert "Outage" in text_out
    assert icon_out == "🔴"

    # Stage-specific outage status string (e.g. delivery_outage)
    uptime_deliv, text_deliv, color_deliv, icon_deliv = calculate_provider_sla("delivery_outage", 3)
    assert 95.0 <= uptime_deliv <= 99.0
    assert "Delivery Outage" in text_deliv
    assert icon_deliv == "🔴"


def test_agent_readiness_and_geo(tmp_path: Path):
    # 1. Test generate_agent_discovery_files
    generate_agent_discovery_files(tmp_path)

    # Check pricing.md
    pricing_file = tmp_path / "pricing.md"
    assert pricing_file.is_file()
    pricing_text = pricing_file.read_text(encoding="utf-8")
    assert "$0 / 100% Free Open Source Software (FOSS)" in pricing_text
    assert "MIT License" in pricing_text
    assert "Unlimited mailboxes" in pricing_text
    assert "No Credit Card / No Vendor Lock-in" in pricing_text

    # Check llms.txt
    llms_file = tmp_path / "llms.txt"
    assert llms_file.is_file()
    llms_text = llms_file.read_text(encoding="utf-8")
    assert "## Pricing & Licensing" in llms_text
    assert "https://stormsia.github.io/maily/pricing.md" in llms_text

    # Check llms-full.txt
    llms_full_file = tmp_path / "llms-full.txt"
    assert llms_full_file.is_file()
    llms_full_text = llms_full_file.read_text(encoding="utf-8")
    assert "## Pricing & Licensing" in llms_full_text
    assert "Automated Testing Recipes" in llms_full_text
    assert "Security Architecture & Threat Model" in llms_full_text

    # Check generated docs/RECIPES.md and docs/ARCHITECTURE.md
    recipes_file = tmp_path / "docs" / "RECIPES.md"
    assert recipes_file.is_file()
    assert "Playwright E2E User Signup" in recipes_file.read_text(encoding="utf-8")

    arch_file = tmp_path / "docs" / "ARCHITECTURE.md"
    assert arch_file.is_file()
    assert "Zero Outbound SMTP" in arch_file.read_text(encoding="utf-8")

    # Check .well-known/ai-catalog.json
    catalog_file = tmp_path / ".well-known" / "ai-catalog.json"
    assert catalog_file.is_file()
    catalog_data = json.loads(catalog_file.read_text(encoding="utf-8"))
    resource_urls = [r["url"] for r in catalog_data["resources"]]
    assert "https://stormsia.github.io/maily/pricing.md" in resource_urls
    assert "https://stormsia.github.io/maily/llms.txt" in resource_urls
    assert "https://stormsia.github.io/maily/llms-full.txt" in resource_urls
    assert "https://stormsia.github.io/maily/SKILL.md" in resource_urls
    assert "https://stormsia.github.io/maily/openapi.json" in resource_urls

    # 2. Test get_head_meta links all 5 files + SKILL.md
    head_meta = get_head_meta(
        title="Test",
        description="Test desc",
        canonical_url="https://stormsia.github.io/maily/",
        base_path="",
    )
    assert '<link rel="alternate" type="text/plain" href="llms.txt"' in head_meta
    assert '<link rel="alternate" type="text/plain" href="llms-full.txt"' in head_meta
    assert (
        '<link rel="service-desc" type="application/vnd.oai.openapi+json" href="openapi.json"'
        in head_meta
    )
    assert (
        '<link rel="ai-catalog" type="application/json" href=".well-known/ai-catalog.json"'
        in head_meta
    )
    assert 'href="SKILL.md"' in head_meta

    # 3. Test render_docs_shell markdown mirror mapping
    docker_shell = render_docs_shell(
        slug="docker", title="Docker", description="", h1="Docker", lead="", body_html=""
    )
    assert '<link rel="alternate" type="text/markdown" href="../docs/DOCKER.md"' in docker_shell

    python_shell = render_docs_shell(
        slug="python", title="Python", description="", h1="Python", lead="", body_html=""
    )
    assert (
        '<link rel="alternate" type="text/markdown" href="../docs/CLIENT_GUIDE.md"' in python_shell
    )

    recipes_shell = render_docs_shell(
        slug="recipes", title="Recipes", description="", h1="Recipes", lead="", body_html=""
    )
    assert '<link rel="alternate" type="text/markdown" href="../docs/RECIPES.md"' in recipes_shell

    arch_shell = render_docs_shell(
        slug="architecture", title="Arch", description="", h1="Arch", lead="", body_html=""
    )
    assert '<link rel="alternate" type="text/markdown" href="../docs/ARCHITECTURE.md"' in arch_shell

    # 4. Test footer includes direct hyperlinks in Agent Discovery & AI
    footer = get_footer_html(base_path="")
    assert 'href="llms.txt"' in footer
    assert 'href="llms-full.txt"' in footer
    assert 'href="SKILL.md"' in footer
    assert 'href="openapi.json"' in footer
    assert 'href=".well-known/ai-catalog.json"' in footer
    assert 'href="pricing.md"' in footer

    # 5. Test robots.txt comments for AI endpoints
    generate_seo_files(tmp_path)
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert "# - llms.txt:" in robots
    assert "# - llms-full.txt:" in robots
    assert "# - openapi.json:" in robots
    assert "# - SKILL.md:" in robots
    assert "# - ai-catalog.json:" in robots
    assert "# - pricing.md:" in robots

    # 6. Test index.html comparative table row Best For
    generate_index_portal(tmp_path)
    index_html = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "Best For" in index_html
    assert "One-off manual disposable scripts, non-critical ad-hoc tests" in index_html
    assert (
        "Enterprise CI/CD pipelines, high-velocity Playwright/Pytest suites, multi-tenant QA bots"
        in index_html
    )


def test_json_ld_structured_data_and_entity_graph():
    """Verify Schema.org JSON-LD graph integrity, required fields, and entity links."""
    page_types = ["index", "scalar", "swagger", "redoc", "analytics", "benchmarks", "docs"]

    for pt in page_types:
        raw_snippet = get_json_ld_for_page(
            page_type=pt,
            base_path="" if pt != "docs" else "../",
            title=f"Test {pt.title()}",
            description="Test description",
            canonical_url=f"https://stormsia.github.io/maily/{pt}.html",
        )
        assert '<script type="application/ld+json">' in raw_snippet
        assert "</script>" in raw_snippet

        clean_json = (
            raw_snippet.replace('<script type="application/ld+json">', "")
            .replace("</script>", "")
            .strip()
        )
        data = json.loads(clean_json)

        assert data["@context"] == "https://schema.org"
        assert "@graph" in data
        graph = data["@graph"]

        ids = {node["@id"] for node in graph if "@id" in node}
        types = {node["@type"] for node in graph if "@type" in node}

        # 1. Organization entity (#organization) must exist in @graph across all pages
        assert "Organization" in types
        org_node = next(n for n in graph if n.get("@type") == "Organization")
        assert org_node["@id"] == "https://stormsia.github.io/maily/#organization"
        assert org_node["name"] == "Maily Project"
        assert org_node["url"] == "https://stormsia.github.io/maily/"
        assert org_node["logo"] == "https://stormsia.github.io/maily/assets/logo.png"

        # 2. SoftwareApplication entity (#software) must exist in @graph (stub on subpages, full on index)
        assert "SoftwareApplication" in types
        sw_node = next(n for n in graph if n.get("@type") == "SoftwareApplication")
        assert sw_node["@id"] == "https://stormsia.github.io/maily/#software"
        assert sw_node["name"] == "Maily"
        assert sw_node["url"] == "https://stormsia.github.io/maily/"
        assert sw_node["releaseNotes"] == "https://github.com/stormsia/maily/releases"
        assert sw_node["softwareHelp"] == "https://stormsia.github.io/maily/docs/"
        assert sw_node["sourceCode"]["@type"] == "SoftwareSourceCode"
        assert sw_node["sourceCode"]["codeRepository"] == "https://github.com/stormsia/maily"

        # 3. No dangling references within the graph
        for node in graph:
            for prop in [
                "about",
                "isPartOf",
                "publisher",
                "author",
                "provider",
                "creator",
                "targetProduct",
                "breadcrumb",
            ]:
                if prop in node and isinstance(node[prop], dict) and "@id" in node[prop]:
                    ref = node[prop]["@id"]
                    assert ref in ids, (
                        f"Dangling @id reference '{ref}' for property '{prop}' in page {pt}"
                    )

        # 4. Page-specific assertions
        if pt == "index":
            # No 1-element breadcrumb on root index
            assert "BreadcrumbList" not in types
            webpage = next(n for n in graph if n.get("@type") == "WebPage")
            assert "breadcrumb" not in webpage

            # Enriched WebAPI node
            webapi = next(n for n in graph if n.get("@type") == "WebAPI")
            assert webapi["documentation"] == "https://stormsia.github.io/maily/scalar.html"
            assert webapi["termsOfService"] == "https://github.com/stormsia/maily/blob/main/LICENSE"
            assert webapi["hasPart"]["@type"] == "CreativeWork"
            assert webapi["hasPart"]["url"] == "https://stormsia.github.io/maily/openapi.json"
        elif pt in ("scalar", "swagger", "redoc"):
            assert "BreadcrumbList" in types
            b_node = next(n for n in graph if n.get("@type") == "BreadcrumbList")
            assert len(b_node["itemListElement"]) == 2
            api_ref = next(n for n in graph if n.get("@type") == "APIReference")
            assert api_ref["publisher"]["@id"] == "https://stormsia.github.io/maily/#organization"
        elif pt == "analytics":
            assert "BreadcrumbList" in types
            b_node = next(n for n in graph if n.get("@type") == "BreadcrumbList")
            assert len(b_node["itemListElement"]) == 2

            tech_article = next(n for n in graph if n.get("@type") == "TechArticle")
            assert (
                tech_article["image"] == "https://stormsia.github.io/maily/assets/hero_banner.png"
            )
            assert tech_article["datePublished"] == "2024-10-01T00:00:00Z"
            assert "T" in tech_article["dateModified"]
            assert (
                tech_article["publisher"]["@id"] == "https://stormsia.github.io/maily/#organization"
            )
            assert tech_article["inLanguage"] == "en"

            dataset = next(n for n in graph if n.get("@type") == "Dataset")
            assert dataset["creator"]["@id"] == "https://stormsia.github.io/maily/#organization"
            assert dataset["license"] == "https://opensource.org/licenses/MIT"
            assert dataset["isAccessibleForFree"] is True
        elif pt == "benchmarks":
            assert "BreadcrumbList" in types
            b_node = next(n for n in graph if n.get("@type") == "BreadcrumbList")
            assert len(b_node["itemListElement"]) == 2

            dataset = next(n for n in graph if n.get("@type") == "Dataset")
            assert dataset["creator"]["@id"] == "https://stormsia.github.io/maily/#organization"
            assert dataset["license"] == "https://opensource.org/licenses/MIT"
            assert dataset["isAccessibleForFree"] is True
        elif pt == "docs":
            assert "BreadcrumbList" in types
            b_node = next(n for n in graph if n.get("@type") == "BreadcrumbList")
            assert len(b_node["itemListElement"]) >= 2

            tech_article = next(n for n in graph if n.get("@type") == "TechArticle")
            assert (
                tech_article["image"] == "https://stormsia.github.io/maily/assets/hero_banner.png"
            )
            assert tech_article["datePublished"] == "2024-10-01T00:00:00Z"
            assert "T" in tech_article["dateModified"]
            assert (
                tech_article["publisher"]["@id"] == "https://stormsia.github.io/maily/#organization"
            )
            assert tech_article["inLanguage"] == "en"
