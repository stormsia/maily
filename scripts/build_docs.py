#!/usr/bin/env python3
"""Build and synchronize documentation across maily artifacts.

Single Source of Truth (SSoT):
- `docs/DOCKER.md`: Docker installation, compose, and development setup.
- `docs/PROVIDERS.md`: Supported providers table and capability matrix.
- `docs/CURL_GUIDE.md`: cURL cheatsheet and API authentication examples.
- `docs/CLIENT_GUIDE.md`: Python client guide and quickstart examples.

Targets kept in sync:
- `src/maily/static/docs.html`: Served at http://127.0.0.1:8477/docs (Docker, Python, Providers, cURL tabs).
- `README.md`: Quick Start, Providers table, and Python client sections.
- `client/README.md`: Installation and quickstart recipes.

Usage:
    python scripts/build_docs.py          # Update all files
    python scripts/build_docs.py --check  # Verify all files are in sync (exit 1 if stale)
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"

DOC_DOCKER = DOCS_DIR / "DOCKER.md"
DOC_PROVIDERS = DOCS_DIR / "PROVIDERS.md"
DOC_CURL = DOCS_DIR / "CURL_GUIDE.md"
DOC_CLIENT = DOCS_DIR / "CLIENT_GUIDE.md"

TARGET_DOCS_HTML = ROOT / "src" / "maily" / "static" / "docs.html"
TARGET_README = ROOT / "README.md"
TARGET_CLIENT_README = ROOT / "client" / "README.md"


def replace_sync_block(content: str, marker: str, replacement: str, indent: str = "      ") -> str:
    """Replace content between <!-- doc-sync:{marker}:start --> and <!-- doc-sync:{marker}:end -->."""
    start_tag = f"<!-- doc-sync:{marker}:start -->"
    end_tag = f"<!-- doc-sync:{marker}:end -->"

    pattern = re.compile(
        rf"([ \t]*{re.escape(start_tag)}).*?([ \t]*{re.escape(end_tag)})",
        re.DOTALL,
    )
    if not pattern.search(content):
        raise ValueError(f"Marker '{marker}' not found in content!")

    formatted_replacement = "\n".join(
        f"{indent}{line}" if line.strip() else "" for line in replacement.strip().splitlines()
    )

    return pattern.sub(
        lambda m: f"{m.group(1)}\n{formatted_replacement}\n{m.group(2)}",
        content,
    )


def parse_code_blocks(markdown_text: str) -> list[tuple[str, str, str]]:
    """Parse markdown text for `### Title` followed by a fenced code block."""
    blocks = []
    # Match: ### Title \n ... ```lang \n code \n ```
    pattern = re.compile(
        r"###\s+([^\n]+)\s*\n+(?:.*?\n)*?```([a-zA-Z0-9_-]*)\r?\n(.*?)\r?\n```",
        re.DOTALL,
    )
    for m in pattern.finditer(markdown_text):
        title = m.group(1).strip()
        lang = m.group(2).strip()
        code = m.group(3)
        blocks.append((title, lang, code))
    return blocks


def render_html_code_boxes(blocks: list[tuple[str, str, str]], is_curl: bool = False) -> str:
    """Render list of (title, lang, code) into .code-box HTML structures."""
    boxes = []
    for title, _, code in blocks:
        # Title can contain markdown code `...`
        clean_title = re.sub(r"`([^`]+)`", r"<code>\1</code>", html.escape(title))
        escaped_code = html.escape(code)
        code_html = f'<span class="curl-cmd">{escaped_code}</span>' if is_curl else escaped_code

        box = f"""<div class="code-box">
  <div class="code-box-header">
    <span>{clean_title}</span>
    <button class="copy-btn" onclick="copySnippet(this)">Copy</button>
  </div>
  <pre class="code-content">{code_html}</pre>
</div>"""
        boxes.append(box)
    return "\n\n".join(boxes)


def render_tab_docker() -> str:
    """Render HTML content for #tab-docker from docs/DOCKER.md."""
    text = DOC_DOCKER.read_text(encoding="utf-8")
    blocks = parse_code_blocks(text)
    boxes_html = render_html_code_boxes(blocks, is_curl=False)

    return f"""<h2 class="section-title">Self-Hosted Docker &amp; Deployment Guide</h2>
<p class="section-desc">
  Deploy a 100% self-hosted temporary email server via official pre-built Docker containers, Docker Compose, or develop locally from source.
</p>

{boxes_html}"""


def render_tab_curl() -> str:
    """Render HTML content for #tab-curl from docs/CURL_GUIDE.md."""
    text = DOC_CURL.read_text(encoding="utf-8")
    blocks = parse_code_blocks(text)
    boxes_html = render_html_code_boxes(blocks, is_curl=True)

    return f"""<h2 class="section-title">cURL & Authentication Cheat Sheet</h2>
<p class="section-desc">
  Authenticate all requests with the <code>X-API-Key</code> HTTP header.
</p>

{boxes_html}"""


def render_tab_python() -> str:
    """Render HTML content for #tab-python from docs/CLIENT_GUIDE.md."""
    text = DOC_CLIENT.read_text(encoding="utf-8")
    quickstart_match = re.search(
        r"<!-- doc-sync:client-quickstart:start -->\r?\n(.*?)\r?\n<!-- doc-sync:client-quickstart:end -->",
        text,
        re.DOTALL,
    )
    if not quickstart_match:
        raise ValueError("Could not find client-quickstart block in docs/CLIENT_GUIDE.md")

    quickstart_text = quickstart_match.group(1)
    blocks = parse_code_blocks(quickstart_text)
    boxes_html = render_html_code_boxes(blocks, is_curl=False)

    return f"""<h2 class="section-title">Standalone Python Async Client</h2>
<p class="section-desc">
  <code>maily-client</code> is a zero-dependency (only httpx, loguru, pydantic) single-file client.
  Full async support, typed pydantic models, granular exception hierarchy, and high-level verification helpers.
</p>

{boxes_html}"""


def _format_table_cell(cell: str) -> str:
    """Format table cell with badge styling."""
    c = cell.strip()
    c_clean = c.replace("`", "").strip()

    if c_clean in ("domain",):
        return f'<span class="badge badge--domain">{c_clean}</span>'
    if c_clean in ("parent",):
        return f'<span class="badge badge--parent">{c_clean}</span>'
    if (
        "Supported" in c_clean
        or "+alias" in c_clean
        or "PIN code" in c_clean
        or "PIN Code" in c_clean
        or "Password" in c_clean
    ):
        text = c_clean.replace("✅", "").strip()
        return f'<span class="badge badge--yes">{text}</span>'
    if (
        "No" in c_clean
        or "No-op" in c_clean
        or "OAuth2" in c_clean
        or "Own Account" in c_clean
        or "Parent account" in c_clean
    ):
        text = c_clean.replace("❌", "").replace("⚪", "").strip()
        return f'<span class="badge badge--no">{text}</span>'
    if c.startswith("**") and c.endswith("**"):
        return f"<strong>{c[2:-2]}</strong>"
    return html.escape(c)


def render_tab_providers() -> str:
    """Render HTML content for #tab-providers from docs/PROVIDERS.md."""
    text = DOC_PROVIDERS.read_text(encoding="utf-8")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    table_lines = [line for line in lines if line.startswith("|")]

    headers = [col.strip() for col in table_lines[0].split("|")[1:-1]]
    rows = []
    for line in table_lines[2:]:  # skip header and separator
        cols = [col.strip() for col in line.split("|")[1:-1]]
        rows.append(cols)

    th_html = "\n".join(f"          <th>{html.escape(h)}</th>" for h in headers)
    tr_html = []
    for row in rows:
        td_html = []
        for i, col in enumerate(row):
            if i == 0:
                slug = col.replace("**", "").strip()
                td_html.append(f"          <td><strong>{html.escape(slug)}</strong></td>")
            else:
                td_html.append(f"          <td>{_format_table_cell(col)}</td>")
        tr_html.append("        <tr>\n" + "\n".join(td_html) + "\n        </tr>")

    tbody_html = "\n".join(tr_html)

    return f"""<h2 class="section-title">Active Provider Adapters</h2>
<p class="section-desc">
  Maily seamlessly aggregates public temporary-mail networks and private Gmail parent accounts into one unified REST API.
</p>

<div class="table-wrap">
  <table class="data-table">
    <thead>
      <tr>
{th_html}
      </tr>
    </thead>
    <tbody>
{tbody_html}
    </tbody>
  </table>
</div>

<div class="card">
  <h3 class="card-title">Adding a New Provider?</h3>
  <p class="card-body">
    See the developer guide in <code>docs/ADDING_PROVIDERS.md</code> for a complete step-by-step
    walkthrough and copy-pasteable boilerplate for adding any new email service with hermetic unit tests.
  </p>
</div>"""


def sync_docs_html(content: str) -> str:
    """Synchronize all documentation tabs into docs.html."""
    docker_html = render_tab_docker()
    python_html = render_tab_python()
    providers_html = render_tab_providers()
    curl_html = render_tab_curl()

    content = replace_sync_block(content, "tab-docker", docker_html)
    content = replace_sync_block(content, "tab-python", python_html)
    content = replace_sync_block(content, "tab-providers", providers_html)
    content = replace_sync_block(content, "tab-curl", curl_html)
    return content


def sync_readme(content: str) -> str:
    """Synchronize docs sections into README.md."""
    # 1. Supported Providers table from docs/PROVIDERS.md
    providers_text = DOC_PROVIDERS.read_text(encoding="utf-8")
    table_match = re.search(r"(\| Provider.*?\n> 💡.*?\n)", providers_text, re.DOTALL)
    if table_match:
        content = replace_sync_block(content, "providers", table_match.group(1).strip(), indent="")

    # 2. Quick Start from docs/DOCKER.md
    docker_text = DOC_DOCKER.read_text(encoding="utf-8")
    docker_body = re.sub(r"^#\s+[^\n]+\r?\n+", "", docker_text).strip()
    content = replace_sync_block(content, "docker", docker_body, indent="")

    # 3. Python Client Quickstart from docs/CLIENT_GUIDE.md
    client_text = DOC_CLIENT.read_text(encoding="utf-8")
    quickstart_match = re.search(
        r"<!-- doc-sync:client-quickstart:start -->\r?\n(.*?)\r?\n<!-- doc-sync:client-quickstart:end -->",
        client_text,
        re.DOTALL,
    )
    if quickstart_match:
        content = replace_sync_block(
            content, "client", quickstart_match.group(1).strip(), indent=""
        )

    return content


def sync_client_readme(content: str) -> str:
    """Synchronize client quickstarts into client/README.md."""
    client_text = DOC_CLIENT.read_text(encoding="utf-8")
    quickstart_match = re.search(
        r"<!-- doc-sync:client-quickstart:start -->\r?\n(.*?)\r?\n<!-- doc-sync:client-quickstart:end -->",
        client_text,
        re.DOTALL,
    )
    if quickstart_match:
        # Extract snippets starting after the overview intro (from `### 1-Line Mailbox`)
        snippets_match = re.search(r"(### 1-Line Mailbox.*)", quickstart_match.group(1), re.DOTALL)
        if snippets_match:
            content = replace_sync_block(
                content, "client-recipes", snippets_match.group(1).strip(), indent=""
            )

    return content


def build_all() -> dict[Path, str]:
    """Calculate the synced content for all target files."""
    results: dict[Path, str] = {}

    docs_html_curr = TARGET_DOCS_HTML.read_text(encoding="utf-8")
    results[TARGET_DOCS_HTML] = sync_docs_html(docs_html_curr)

    readme_curr = TARGET_README.read_text(encoding="utf-8")
    results[TARGET_README] = sync_readme(readme_curr)

    client_readme_curr = TARGET_CLIENT_README.read_text(encoding="utf-8")
    results[TARGET_CLIENT_README] = sync_client_readme(client_readme_curr)

    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail (exit 1) if target files are out of sync instead of updating them",
    )
    args = parser.parse_args()

    targets = build_all()
    stale_files: list[Path] = []

    for path, new_content in targets.items():
        current_content = path.read_text(encoding="utf-8") if path.exists() else ""
        if current_content != new_content:
            stale_files.append(path)

    if not stale_files:
        print("All documentation targets are in sync with docs/!")
        return 0

    if args.check:
        print(f"STALE: {len(stale_files)} documentation file(s) differ from docs/ SSoT:")
        for p in stale_files:
            print(f"  - {p.relative_to(ROOT)}")
        print("\nRun `python scripts/build_docs.py` to regenerate and sync.")
        return 1

    for p, new_content in targets.items():
        p.write_text(new_content, encoding="utf-8", newline="\n")
        print(f"Updated: {p.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
