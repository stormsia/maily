#!/usr/bin/env python3
"""Check Semantic Versioning (SemVer) and version consistency across all project files.

Verifies that:
1. pyproject.toml defines a valid SemVer 2.0.0 version.
2. src/maily/__init__.py matches pyproject.toml.
3. src/maily/standalone_client.py matches pyproject.toml.
4. client/client.py matches pyproject.toml.
5. If a git tag or expected version is passed via --tag/--expected, it strictly matches.
"""

from __future__ import annotations

import argparse
import contextlib
import re
import sys
from pathlib import Path

import tomllib

# SemVer 2.0.0 official regex specification
SEMVER_REGEX = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)

VERSION_ASSIGN_REGEX = re.compile(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", re.MULTILINE)


def extract_version_from_file(path: Path) -> str:
    """Extract __version__ = '...' from a Python file."""
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    content = path.read_text(encoding="utf-8")
    match = VERSION_ASSIGN_REGEX.search(content)
    if not match:
        raise ValueError(f"Could not find '__version__ = ...' pattern in {path}")
    return match.group(1).strip()


def extract_pyproject_version(path: Path) -> str:
    """Extract project.version from pyproject.toml."""
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "rb") as f:
        data = tomllib.load(f)
    version = data.get("project", {}).get("version")
    if not version:
        raise ValueError(f"Could not find 'project.version' in {path}")
    return str(version).strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Verify SemVer and version consistency across the codebase."
    )
    parser.add_argument("--tag", help="Optional git tag to compare against (e.g. v1.2.3 or 1.2.3)")
    parser.add_argument("--expected", help="Explicit expected version string")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent

    # 1. Read pyproject.toml version
    pyproject_file = repo_root / "pyproject.toml"
    try:
        pyproject_ver = extract_pyproject_version(pyproject_file)
    except Exception as exc:
        print(f"❌ Error reading {pyproject_file}: {exc}", file=sys.stderr)
        return 1

    # 2. Validate SemVer format
    if not SEMVER_REGEX.match(pyproject_ver):
        print(
            f"❌ Version '{pyproject_ver}' in {pyproject_file} does not adhere to Semantic Versioning 2.0.0 (MAJOR.MINOR.PATCH)!",
            file=sys.stderr,
        )
        return 1

    # 3. Read versions from package and client files
    files_to_check = {
        "src/maily/__init__.py": repo_root / "src" / "maily" / "__init__.py",
        "src/maily/standalone_client.py": repo_root / "src" / "maily" / "standalone_client.py",
        "client/client.py": repo_root / "client" / "client.py",
    }

    versions: dict[str, str] = {"pyproject.toml": pyproject_ver}
    errors: list[str] = []

    for name, path in files_to_check.items():
        try:
            ver = extract_version_from_file(path)
            versions[name] = ver
            if ver != pyproject_ver:
                errors.append(
                    f"Mismatch in {name}: found '{ver}', expected '{pyproject_ver}' (from pyproject.toml)"
                )
        except Exception as exc:
            errors.append(f"Error reading {name}: {exc}")

    # 4. Check against optional tag or expected version
    if args.tag:
        normalized_tag = args.tag.lstrip("v")
        if normalized_tag != pyproject_ver:
            errors.append(
                f"Git tag '{args.tag}' does not match pyproject.toml version '{pyproject_ver}'"
            )

    if args.expected:
        normalized_expected = args.expected.lstrip("v")
        if normalized_expected != pyproject_ver:
            errors.append(
                f"Expected version '{args.expected}' does not match pyproject.toml version '{pyproject_ver}'"
            )

    # 5. Report results
    print("📋 Version Consistency Audit:")
    for file_name, file_ver in versions.items():
        status = "✅" if file_ver == pyproject_ver else "❌"
        print(f"  {status} {file_name}: {file_ver}")

    if errors:
        print("\n❌ Version Consistency Check Failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1

    print(f"\n🎉 All files are consistent and conform to SemVer 2.0.0: v{pyproject_ver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
