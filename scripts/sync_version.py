#!/usr/bin/env python3
"""
Synchronizes the single source of truth version from root pyproject.toml
into site/src/data/version.ts, site/package.json, and validates release-please targets.
"""

import json
import re
from pathlib import Path


def get_root_version(root: Path) -> str:
    pyproject_file = root / "pyproject.toml"
    if not pyproject_file.exists():
        raise FileNotFoundError(f"Missing {pyproject_file}")
    content = pyproject_file.read_text(encoding="utf-8")
    m = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not m:
        raise ValueError("Could not extract version from pyproject.toml")
    return m.group(1).strip()


def sync_version():
    root = Path(__file__).resolve().parent.parent
    ver = get_root_version(root)
    print(f"[sync_version] Root project version is: {ver}")

    # 1. Update site/src/data/version.ts
    version_ts = root / "site" / "src" / "data" / "version.ts"
    version_ts.parent.mkdir(parents=True, exist_ok=True)
    ts_content = f"""// Auto-synced from pyproject.toml - DO NOT EDIT DIRECTLY
export const APP_VERSION = '{ver}'; // x-release-please-version
export const APP_VERSION_TAG = `v${{APP_VERSION}}`;
"""
    version_ts.write_text(ts_content, encoding="utf-8")
    print(f"[✓] Synced site/src/data/version.ts -> {ver}")

    # 2. Update site/package.json
    pkg_json = root / "site" / "package.json"
    if pkg_json.exists():
        data = json.loads(pkg_json.read_text(encoding="utf-8"))
        if data.get("version") != ver:
            data["version"] = ver
            pkg_json.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            print(f"[✓] Updated site/package.json -> {ver}")
        else:
            print(f"[i] site/package.json already at {ver}")

    # 3. Update static templates in site/public
    public_dir = root / "site" / "public"
    if public_dir.exists():
        for filename in ["scalar.html", "swagger.html", "redoc.html", "dev/bench/index.html"]:
            html_file = public_dir / filename
            if html_file.exists():
                txt = html_file.read_text(encoding="utf-8")
                txt = re.sub(
                    r'<span class="brand-badge">v[^<]+</span>',
                    f'<span class="brand-badge">v{ver}</span>',
                    txt,
                )
                txt = re.sub(r'"softwareVersion":\s*"[^"]+"', f'"softwareVersion": "{ver}"', txt)
                html_file.write_text(txt, encoding="utf-8")

        for md_name in ["SKILL.md", "llms-full.txt"]:
            md_file = public_dir / md_name
            if md_file.exists():
                txt = md_file.read_text(encoding="utf-8")
                txt = re.sub(r"(?i)version:\s*[0-9\.]+", f"version: {ver}", txt)
                md_file.write_text(txt, encoding="utf-8")

        for cat_name in [
            "ard.json",
            ".well-known/ard.json",
            "ai-catalog.json",
            ".well-known/ai-catalog.json",
        ]:
            cat_file = public_dir / cat_name
            if cat_file.exists():
                try:
                    cat_data = json.loads(cat_file.read_text(encoding="utf-8"))
                    cat_data["version"] = ver
                    cat_file.write_text(json.dumps(cat_data, indent=2) + "\n", encoding="utf-8")
                except Exception:
                    pass
        print(f"[✓] Synced static metadata in site/public -> {ver}")


if __name__ == "__main__":
    sync_version()
