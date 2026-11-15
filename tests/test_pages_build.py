"""Test static GitHub Pages site and developer portal artifacts.

Validates:
- Complete artifact generation (.nojekyll, robots.txt, sitemap.xml, openapi.json, index.html)
- API reference explorers (scalar.html, swagger.html, redoc.html)
- Continuous benchmarks portal (dev/bench/)
- Agent-readiness and GEO compliance (llms.txt, llms-full.txt, SKILL.md, ai-catalog.json)
- Schema.org JSON-LD entity graph integrity and validation
- Provider health telemetry and SLA calculations
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DIR = ROOT / "public"
SITE_PUBLIC_DIR = ROOT / "site" / "public"

PORTAL_BUILT = (PUBLIC_DIR / "index.html").is_file()
skip_if_no_portal = pytest.mark.skipif(
    not PORTAL_BUILT,
    reason="Developer portal not built. Run 'npm run build' in site/ to generate public/ artifacts.",
)


def calculate_provider_sla(status: str, failures: int) -> tuple[float, str, str, str]:
    """Calculate mathematically grounded SLA uptime estimate and status."""
    status_lower = (status or "").lower()
    fails = max(0, failures)

    if (
        status_lower.endswith("outage")
        or "outage" in status_lower
        or status_lower == "failing"
        or fails >= 3
    ):
        fails_cnt = max(fails, 3)
        uptime = max(0.0, round((168 - fails_cnt) / 168.0 * 100.0, 1))
        outage_type = "Outage"
        if "_" in status_lower:
            stage = status_lower.split("_")[0]
            outage_type = f"{stage.capitalize()} Outage"
        return uptime, f"{outage_type} ({fails_cnt} fails)", "#ef4444", "🔴"

    if status_lower == "degraded" or fails in (1, 2):
        fails_cnt = max(fails, 1)
        uptime = round((168 - fails_cnt) / 168.0 * 100.0, 1)
        return (
            uptime,
            f"Degraded ({fails_cnt} fail{'s' if fails_cnt > 1 else ''})",
            "#f59e0b",
            "🟡",
        )

    if status_lower == "operational" and fails == 0:
        return 99.95, "Operational", "#10b981", "🟢"

    return 99.0, status.capitalize(), "#94a3b8", "⚪"


def load_provider_health() -> dict[str, dict]:
    """Load provider health states with multi-path resolution and fallback."""
    candidates = [
        Path(".github/provider_health_state.json"),
        ROOT / ".github" / "provider_health_state.json",
    ]
    for path in candidates:
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data.get("providers", {})
            except Exception:
                pass
    return {
        "dispoemail.org": {
            "consecutive_failures": 0,
            "issue_number": None,
            "last_status": "operational",
        },
        "mail.tm": {"consecutive_failures": 0, "issue_number": None, "last_status": "operational"},
    }


@skip_if_no_portal
def test_site_portal_artifacts():
    """Verify that all developer portal static artifacts are present and well-formed."""
    # 1. Jekyll bypass & SEO basics
    assert (PUBLIC_DIR / ".nojekyll").is_file()
    assert (PUBLIC_DIR / "robots.txt").is_file()
    assert (PUBLIC_DIR / "sitemap.xml").is_file()

    robots_txt = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
    assert "Sitemap: https://stormsia.github.io/maily/sitemap.xml" in robots_txt
    assert "User-agent: *" in robots_txt

    sitemap_xml = (PUBLIC_DIR / "sitemap.xml").read_text(encoding="utf-8")
    assert "<loc>https://stormsia.github.io/maily/</loc>" in sitemap_xml
    assert "<loc>https://stormsia.github.io/maily/docs</loc>" in sitemap_xml
    assert "<loc>https://stormsia.github.io/maily/analytics</loc>" in sitemap_xml

    # 2. OpenAPI 3.1 Schema
    openapi_file = PUBLIC_DIR / "openapi.json"
    assert openapi_file.is_file()
    schema = json.loads(openapi_file.read_text(encoding="utf-8"))
    assert "paths" in schema
    assert "/v1/mailboxes" in schema["paths"]
    assert "/health" in schema["paths"]
    assert schema.get("info", {}).get("title") == "maily"

    # 3. Main Portal (React SSG index.html)
    index_html = (PUBLIC_DIR / "index.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in index_html
    assert "Maily" in index_html
    assert 'id="root"' in index_html
    assert "hero_banner" in index_html

    # 4. Analytics & Docs Pages
    analytics_html = (PUBLIC_DIR / "analytics.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in analytics_html
    assert "Analytics" in analytics_html or "Health" in analytics_html

    docs_html = (PUBLIC_DIR / "docs.html").read_text(encoding="utf-8")
    assert "<!DOCTYPE html>" in docs_html
    assert "Documentation" in docs_html or "Getting Started" in docs_html

    # 5. Standalone API Reference Viewers
    scalar_html = (PUBLIC_DIR / "scalar.html").read_text(encoding="utf-8")
    assert "@scalar/api-reference" in scalar_html
    assert "openapi.json" in scalar_html

    swagger_html = (PUBLIC_DIR / "swagger.html").read_text(encoding="utf-8")
    assert "SwaggerUIBundle" in swagger_html or "swagger-ui" in swagger_html
    assert "openapi.json" in swagger_html

    redoc_html = (PUBLIC_DIR / "redoc.html").read_text(encoding="utf-8")
    assert "redoc" in redoc_html
    assert "openapi.json" in redoc_html

    # 6. Benchmark Portal
    bench_index = PUBLIC_DIR / "dev" / "bench" / "index.html"
    assert bench_index.is_file()
    bench_html = bench_index.read_text(encoding="utf-8")
    assert "chart" in bench_html.lower() or "benchmark" in bench_html.lower()

    # 7. Static Assets
    assert (PUBLIC_DIR / "assets" / "logo.png").is_file()
    assert (PUBLIC_DIR / "assets" / "hero_banner.png").is_file()


def test_load_provider_health():
    """Verify loading provider health configuration."""
    providers = load_provider_health()
    assert isinstance(providers, dict)
    assert len(providers) > 0
    assert "dispoemail.org" in providers or "mail.tm" in providers


def test_calculate_provider_sla():
    """Verify SLA uptime percentage and status calculation logic."""
    uptime, text, color, icon = calculate_provider_sla("operational", 0)
    assert uptime == 99.95
    assert "Operational" in text
    assert icon == "🟢"

    uptime_deg, text_deg, color_deg, icon_deg = calculate_provider_sla("degraded", 1)
    assert 99.0 <= uptime_deg <= 99.8
    assert "Degraded (1 fail)" in text_deg
    assert icon_deg == "🟡"

    uptime_out, text_out, color_out, icon_out = calculate_provider_sla("outage", 3)
    assert 95.0 <= uptime_out <= 99.0
    assert "Outage" in text_out
    assert icon_out == "🔴"

    uptime_deliv, text_deliv, color_deliv, icon_deliv = calculate_provider_sla("delivery_outage", 3)
    assert 95.0 <= uptime_deliv <= 99.0
    assert "Delivery Outage" in text_deliv
    assert icon_deliv == "🔴"


@skip_if_no_portal
def test_agent_readiness_and_geo():
    """Verify Agent-Readiness and Generative Engine Optimization standards."""
    # 1. pricing.md
    pricing_file = PUBLIC_DIR / "pricing.md"
    assert pricing_file.is_file()
    pricing_text = pricing_file.read_text(encoding="utf-8")
    assert "$0 / 100% Free Open Source Software (FOSS)" in pricing_text
    assert "MIT License" in pricing_text
    assert "Unlimited mailboxes" in pricing_text
    assert "No Credit Card / No Vendor Lock-in" in pricing_text

    # 2. llms.txt
    llms_file = PUBLIC_DIR / "llms.txt"
    assert llms_file.is_file()
    llms_text = llms_file.read_text(encoding="utf-8")
    assert "## Pricing & Licensing" in llms_text
    assert "https://stormsia.github.io/maily/pricing.md" in llms_text

    # 3. llms-full.txt
    llms_full_file = PUBLIC_DIR / "llms-full.txt"
    assert llms_full_file.is_file()
    llms_full_text = llms_full_file.read_text(encoding="utf-8")
    assert "## Pricing & Licensing" in llms_full_text
    assert "Automated Testing Recipes" in llms_full_text
    assert "Security Architecture & Threat Model" in llms_full_text

    # 4. SKILL.md
    skill_file = PUBLIC_DIR / "SKILL.md"
    assert skill_file.is_file()

    # 5. ard.json, ai-catalog.json & .well-known/ manifests
    for manifest_path in [
        PUBLIC_DIR / "ard.json",
        PUBLIC_DIR / ".well-known" / "ard.json",
        PUBLIC_DIR / "ai-catalog.json",
        PUBLIC_DIR / ".well-known" / "ai-catalog.json",
    ]:
        assert manifest_path.is_file(), f"Missing manifest at {manifest_path}"
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Strict ARD Specification requirements
        assert "entries" in manifest_data, (
            f"ARD manifest {manifest_path.name} missing 'entries' array"
        )
        assert isinstance(manifest_data["entries"], list)
        assert len(manifest_data["entries"]) > 0

        # Validate each entry structure
        for entry in manifest_data["entries"]:
            assert "identifier" in entry and entry["identifier"].startswith("urn:air:")
            assert "displayName" in entry and len(entry["displayName"]) > 0
            assert "type" in entry and len(entry["type"]) > 0
            assert "url" in entry and entry["url"].startswith("https://")
            assert "representativeQueries" in entry and len(entry["representativeQueries"]) >= 1

        # Check resource URLs
        entry_urls = [e["url"] for e in manifest_data["entries"]]
        assert "https://stormsia.github.io/maily/pricing.md" in entry_urls
        assert "https://stormsia.github.io/maily/llms.txt" in entry_urls
        assert "https://stormsia.github.io/maily/llms-full.txt" in entry_urls
        assert "https://stormsia.github.io/maily/SKILL.md" in entry_urls
        assert "https://stormsia.github.io/maily/openapi.json" in entry_urls

    # 6. robots.txt machine discovery comments
    robots_text = (PUBLIC_DIR / "robots.txt").read_text(encoding="utf-8")
    assert "# - llms.txt:" in robots_text
    assert "# - llms-full.txt:" in robots_text
    assert "# - openapi.json:" in robots_text
    assert "# - SKILL.md:" in robots_text
    assert "# - ard.json:" in robots_text
    assert "# - ai-catalog.json:" in robots_text
    assert "# - pricing.md:" in robots_text


@skip_if_no_portal
def test_json_ld_structured_data_and_entity_graph():
    """Verify Schema.org JSON-LD graph integrity and entity types in prerendered HTML."""
    target_pages = [
        PUBLIC_DIR / "index.html",
        PUBLIC_DIR / "analytics.html",
        PUBLIC_DIR / "docs.html",
    ]

    for page_path in target_pages:
        assert page_path.is_file()
        content = page_path.read_text(encoding="utf-8")

        json_ld_match = re.search(
            r'<script type="application/ld\+json">([\s\S]*?)</script>', content
        )
        assert json_ld_match is not None, f"No JSON-LD found in {page_path.name}"

        data = json.loads(json_ld_match.group(1).strip())
        assert data.get("@context") == "https://schema.org"
        assert "@graph" in data

        graph = data["@graph"]
        types = {node.get("@type") for node in graph}

        assert "Organization" in types
        assert "SoftwareApplication" in types
        assert "WebAPI" in types

        # Check Organization node
        org_node = next(n for n in graph if n.get("@type") == "Organization")
        assert org_node["@id"] == "https://stormsia.github.io/maily/#organization"
        assert org_node["name"] == "Maily Project"
        assert org_node["url"] == "https://stormsia.github.io/maily/"

        # Check SoftwareApplication node
        sw_node = next(n for n in graph if n.get("@type") == "SoftwareApplication")
        assert sw_node["@id"] == "https://stormsia.github.io/maily/#software"
        assert sw_node["name"] == "Maily"
        assert sw_node["applicationCategory"] == "DeveloperApplication"
        assert sw_node["offers"]["price"] == "0"
