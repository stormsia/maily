"""Generate deployable standalone client files at client/maily_client.py and client/client.py.

The canonical single source of truth for the client is `src/maily/standalone_client.py`.
This script copies it to `client/maily_client.py` and `client/client.py` and prepends the "generated" banner
so that pip-installable or downloaded artifacts remain in sync with the implementation.

    python scripts/build_client.py            # regenerate (dry-run: --check)

The same check is enforced by tests/test_client_standalone.py::
`test_standalone_mirror_is_current`.
"""

from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / "src" / "maily" / "standalone_client.py"
OUTPUTS = [
    ROOT / "client" / "maily_client.py",
    ROOT / "client" / "client.py",
]

BANNER = (
    "# -=- THIS FILE IS GENERATED from src/maily/standalone_client.py -=-\n"
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
        help="fail (exit 1) if generated client files are stale instead of writing them",
    )
    args = parser.parse_args()

    content = render()
    stale = False
    for output in OUTPUTS:
        current = output.read_text(encoding="utf-8") if output.exists() else ""
        if current == content:
            print(f"up to date: {output.relative_to(ROOT)}")
        else:
            stale = True
            if args.check:
                print(
                    f"STALE: {output.relative_to(ROOT)} differs from the canonical client; "
                    "run `python scripts/build_client.py`",
                    file=__import__("sys").stderr,
                )
            else:
                output.write_text(content, encoding="utf-8")
                print(f"regenerated: {output.relative_to(ROOT)}")

    return 1 if (stale and args.check) else 0


if __name__ == "__main__":
    raise SystemExit(main())
