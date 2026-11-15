#!/usr/bin/env python3
"""Sync continuous benchmark results from gh-pages branch to public/dev/bench/."""

import subprocess
from pathlib import Path


def sync_benchmarks(public_dir: Path = Path("public")) -> None:
    bench_dir = public_dir / "dev" / "bench"
    bench_dir.mkdir(parents=True, exist_ok=True)

    data_file = bench_dir / "data.js"
    res = subprocess.run(
        ["git", "show", "origin/gh-pages:dev/bench/data.js"],
        capture_output=True,
    )
    if res.returncode == 0 and res.stdout and len(res.stdout) > 100:
        data_file.write_bytes(res.stdout)
        print(f"[✓] Synced data.js from origin/gh-pages ({len(res.stdout)} bytes)")
    elif data_file.exists():
        print(f"[i] Kept existing benchmark data.js ({data_file.stat().st_size} bytes)")
    else:
        print("[!] No benchmark data found; keeping local repository state.")


if __name__ == "__main__":
    sync_benchmarks()
