"""Generate the deployable standalone client at client/client.py.

The canonical single source of truth for the client is `src/mailtmapi/standalone_client.py`.
This script copies it to `client/client.py` and prepends the "generated" banner
so that pip-installable or downloaded artifacts remain in sync with the implementation.

    python scripts/build_client.py            # regenerate (dry-run: --check)

The same check is enforced by tests/test_client_standalone.py::
`test_standalone_mirror_is_current`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "src" / "mailtmapi" / "standalone_client.py"
OUTPUT = ROOT / "client" / "client.py"

BANNER = (
    "# -=- THIS FILE IS GENERATED from src/mailtmapi/standalone_client.py -=-\n"
    "# Do not edit by hand; edit the canonical file and run:\n"
    "#   python scripts/build_client.py\n"
)


def render(canonical: str = CANONICAL.read_text(encoding="utf-8")) -> str:
    return BANNER + canonical


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail (exit 1) if client/client.py is stale instead of writing it",
    )
    args = parser.parse_args()

    content = render()
    current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    if current == content:
        print(f"up to date: {OUTPUT.relative_to(ROOT)}")
        return 0
    if args.check:
        print(
            f"STALE: {OUTPUT.relative_to(ROOT)} differs from the canonical client; "
            "run `python scripts/build_client.py`",
            file=__import__("sys").stderr,
        )
        return 1
    OUTPUT.write_text(content, encoding="utf-8")
    print(f"regenerated: {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
