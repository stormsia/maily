"""Test static GitHub Pages site generator (scripts/build_pages_site.py)."""

from __future__ import annotations

import json
from pathlib import Path

from build_pages_site import (
    copy_static_assets,
    extract_benchmarks,
    generate_analytics_dashboard,
    generate_index_portal,
    generate_openapi_schema,
    generate_redoc_ui,
    generate_scalar_ui,
    generate_seo_files,
    generate_swagger_ui,
    get_footer_html,
    get_nav_html,
    load_provider_health,
)

ROOT = Path(__file__).resolve().parents[1]


def test_nav_html_generation():
    root_nav = get_nav_html("docs", base_path="")
    assert 'href="index.html"' in root_nav
    assert 'href="scalar.html"' in root_nav
    assert 'href="swagger.html"' in root_nav
    assert 'href="redoc.html"' in root_nav
    assert 'href="dev/bench/index.html"' in root_nav
    assert 'href="analytics.html"' in root_nav
    assert 'href="openapi.json"' in root_nav
    assert "portal-nav" in root_nav

    sub_nav = get_nav_html("benchmarks", base_path="../../")
    assert 'href="../../index.html"' in sub_nav
    assert 'href="../../scalar.html"' in sub_nav
    assert 'href="../../swagger.html"' in sub_nav
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
    assert "simCreateMailbox" in index_html
    assert "simExtractOtp" in index_html
    assert "simExtractLink" in index_html
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
    assert "portal-nav" in redoc_html
    assert "embedded-view" in redoc_html
    assert '"primary": {"main": "#7c6cff"}' in redoc_html

    # 8. Analytics Dashboard
    generate_analytics_dashboard(tmp_path)
    analytics_html = (tmp_path / "analytics.html").read_text(encoding="utf-8")
    assert "Security, Quality & Operational Observability" in analytics_html
    assert "provider-card" in analytics_html
    assert "Gitleaks" in analytics_html
    assert "Trivy" in analytics_html
    assert "CodeQL" in analytics_html
    assert "portal-footer" in analytics_html

    # 9. Benchmarks extraction and fallback
    extract_benchmarks(tmp_path)
    assert (tmp_path / "dev" / "bench" / "index.html").is_file()
    bench_html = (tmp_path / "dev" / "bench" / "index.html").read_text(encoding="utf-8")
    assert "portal-nav" in bench_html


def test_load_provider_health():
    providers = load_provider_health()
    assert isinstance(providers, dict)
    assert len(providers) > 0
    assert "dispoemail.org" in providers or "mail.tm" in providers
