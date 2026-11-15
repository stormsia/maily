#!/usr/bin/env python3
"""Export FastAPI OpenAPI 3.1 specification to public/openapi.json."""

import json
from pathlib import Path

from maily.app.main import create_app


def export_openapi(public_dir: Path = Path("public")) -> None:
    public_dir.mkdir(parents=True, exist_ok=True)
    site_public_dir = Path("site") / "public"
    app = create_app()
    schema = app.openapi()
    schema["servers"] = [
        {"url": "http://127.0.0.1:8477", "description": "Default local Maily gateway"}
    ]
    content = json.dumps(schema, indent=2)
    out_file = public_dir / "openapi.json"
    out_file.write_text(content, encoding="utf-8")
    if site_public_dir.is_dir():
        (site_public_dir / "openapi.json").write_text(content, encoding="utf-8")
    print(f"[✓] Exported OpenAPI schema to {out_file} ({len(schema.get('paths', {}))} endpoints)")


if __name__ == "__main__":
    export_openapi()
