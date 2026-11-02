"""Verify documentation sync integrity across docs/ SSoT, docs.html, and README files."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_DOCS_SCRIPT = ROOT / "scripts" / "build_docs.py"


def _load_build_docs():
    spec = importlib.util.spec_from_file_location("build_docs", BUILD_DOCS_SCRIPT)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_docs_exist_and_non_empty():
    docs_dir = ROOT / "docs"
    assert (docs_dir / "DOCKER.md").is_file()
    assert (docs_dir / "PROVIDERS.md").is_file()
    assert (docs_dir / "CURL_GUIDE.md").is_file()
    assert (docs_dir / "CLIENT_GUIDE.md").is_file()
    assert (docs_dir / "ADDING_PROVIDERS.md").is_file()

    for filename in ["DOCKER.md", "PROVIDERS.md", "CURL_GUIDE.md", "CLIENT_GUIDE.md"]:
        content = (docs_dir / filename).read_text(encoding="utf-8")
        assert len(content.strip()) > 100, f"{filename} appears unexpectedly short"


def test_docs_are_in_sync():
    mod = _load_build_docs()
    targets = mod.build_all()

    stale: list[str] = []
    for path, expected in targets.items():
        actual = path.read_text(encoding="utf-8") if path.exists() else ""
        if actual != expected:
            stale.append(str(path.relative_to(ROOT)))

    assert not stale, (
        f"Documentation files out of sync with docs/: {stale}. "
        "Run `python scripts/build_docs.py` to regenerate."
    )


def test_docs_html_contains_all_tabs():
    docs_html = (ROOT / "src" / "maily" / "static" / "docs.html").read_text(encoding="utf-8")
    assert 'id="tab-swagger"' in docs_html
    assert 'id="tab-docker"' in docs_html
    assert 'id="tab-python"' in docs_html
    assert 'id="tab-providers"' in docs_html
    assert 'id="tab-curl"' in docs_html
    assert 'data-tab="docker"' in docs_html
    assert 'data-tab="python"' in docs_html
    assert 'data-tab="providers"' in docs_html
    assert 'data-tab="curl"' in docs_html
