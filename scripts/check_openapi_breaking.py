#!/usr/bin/env python3
"""OpenAPI Breaking Changes Detector.

Compares a base OpenAPI specification (e.g. from main) against a target
OpenAPI specification (e.g. from a PR branch) to catch backwards-incompatible API changes.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def load_spec(path_or_str: str | Path) -> dict[str, Any]:
    p = Path(path_or_str)
    if not p.exists():
        raise FileNotFoundError(f"OpenAPI spec file not found: {p}")
    with p.open(encoding="utf-8") as f:
        return json.load(f)


def find_breaking_changes(
    base: dict[str, Any],
    head: dict[str, Any],
) -> tuple[list[str], list[str]]:
    """Return a tuple of (breaking_changes, non_breaking_changes)."""
    breaking: list[str] = []
    non_breaking: list[str] = []

    base_paths = base.get("paths", {})
    head_paths = head.get("paths", {})

    # 1. Check for removed endpoints
    for path, base_methods in base_paths.items():
        if path not in head_paths:
            breaking.append(f"Removed endpoint: `{path}`")
            continue

        head_methods = head_paths[path]

        # 2. Check for removed HTTP methods on existing endpoint
        for method, base_op in base_methods.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch", "options", "head"):
                continue

            if method not in head_methods:
                breaking.append(f"Removed method: `{method.upper()} {path}`")
                continue

            head_op = head_methods[method]

            # 3. Check parameters
            base_params = {
                (p.get("name"), p.get("in")): p
                for p in base_op.get("parameters", [])
            }
            head_params = {
                (p.get("name"), p.get("in")): p
                for p in head_op.get("parameters", [])
            }

            # Check for removed parameters
            for (p_name, p_in), _p_def in base_params.items():
                if (p_name, p_in) not in head_params:
                    breaking.append(
                        f"Removed parameter `{p_name}` ({p_in}) from `{method.upper()} {path}`"
                    )

            # Check for newly added required parameters
            for (p_name, p_in), p_def in head_params.items():
                if (p_name, p_in) not in base_params:
                    if p_def.get("required", False):
                        breaking.append(
                            f"Added new REQUIRED parameter `{p_name}` ({p_in}) to `{method.upper()} {path}`"
                        )
                    else:
                        non_breaking.append(
                            f"Added optional parameter `{p_name}` ({p_in}) to `{method.upper()} {path}`"
                        )

            # 4. Check requestBody required status
            base_rb = base_op.get("requestBody", {})
            head_rb = head_op.get("requestBody", {})
            if not base_rb.get("required", False) and head_rb.get("required", False):
                breaking.append(
                    f"Request body made required on `{method.upper()} {path}`"
                )

            # 5. Check removed success response codes
            base_responses = base_op.get("responses", {})
            head_responses = head_op.get("responses", {})
            for status_code in base_responses:
                if status_code.startswith("2") and status_code not in head_responses:
                    breaking.append(
                        f"Removed success response `{status_code}` on `{method.upper()} {path}`"
                    )

    # 6. Check for newly added endpoints
    for path, head_methods in head_paths.items():
        if path not in base_paths:
            methods = [
                m.upper()
                for m in head_methods
                if m.lower() in ("get", "post", "put", "delete", "patch", "options", "head")
            ]
            non_breaking.append(f"Added endpoint: `{', '.join(methods)} {path}`")
        else:
            for method in head_methods:
                if method.lower() in ("get", "post", "put", "delete", "patch") and method not in base_paths[path]:
                    non_breaking.append(f"Added method: `{method.upper()} {path}`")

    return breaking, non_breaking


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <base_openapi.json> <head_openapi.json>")
        return 2

    base_file = sys.argv[1]
    head_file = sys.argv[2]

    try:
        base = load_spec(base_file)
        head = load_spec(head_file)
    except Exception as e:
        print(f"::error::Failed to load OpenAPI specs: {e}")
        return 1

    breaking, non_breaking = find_breaking_changes(base, head)

    summary_lines = ["### 🌐 OpenAPI Contract & Breaking Changes Report", ""]

    if breaking:
        summary_lines.append(f"❌ **{len(breaking)} Breaking Change(s) Detected:**")
        for b in breaking:
            summary_lines.append(f"- ⚠️ {b}")
        summary_lines.append("")

    if non_breaking:
        summary_lines.append(f"✨ **{len(non_breaking)} Non-breaking Change(s):**")
        for nb in non_breaking:
            summary_lines.append(f"- {nb}")
        summary_lines.append("")

    if not breaking and not non_breaking:
        summary_lines.append("✅ No schema changes detected. API contract is 100% compatible.")

    summary_text = "\n".join(summary_lines)
    print(summary_text)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(summary_text + "\n")

    if breaking:
        print(f"::error::{len(breaking)} breaking changes found in OpenAPI schema!")
        return 1

    print("OpenAPI compatibility gate passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
