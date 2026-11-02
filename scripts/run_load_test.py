#!/usr/bin/env python3
"""Automated Macro Load & Stress Test Runner for maily using Locust.

Launches maily server in an isolated environment, runs headless Locust load
scenarios with concurrency, asserts strict SLOs (0% error rate, p95 < 65ms),
and exports rich markdown reports for CI/CD Step Summary.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen


def wait_for_server(url: str, timeout_sec: float = 15.0) -> bool:
    """Poll URL until 200 OK or timeout expires."""
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        try:
            with urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except (URLError, OSError):
            time.sleep(0.3)
    return False


def warmup_server(port: int, root_key: str, rounds: int = 5) -> None:
    """Warm up server event loop and SQLite queries to avoid cold-start skew."""
    endpoints = [
        "/health",
        "/v1/mailboxes",
        "/v1/admin/domain-cache",
        "/v1/admin/keys/me",
    ]
    for _ in range(rounds):
        for ep in endpoints:
            req = Request(
                f"http://127.0.0.1:{port}{ep}",
                headers={"X-API-Key": root_key},
            )
            with contextlib.suppress(Exception), urlopen(req, timeout=2.0) as resp:
                resp.read()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run automated load & stress test.")
    parser.add_argument(
        "--users", type=int, default=25, help="Number of concurrent users (default: 25)"
    )
    parser.add_argument(
        "--spawn-rate",
        type=int,
        default=10,
        help="User spawn rate per second (default: 10)",
    )
    parser.add_argument("--run-time", default="10s", help="Load test duration (default: 10s)")
    parser.add_argument("--port", type=int, default=8478, help="Target server port (default: 8478)")
    parser.add_argument(
        "--max-p95-ms",
        type=float,
        default=65.0,
        help="Max allowed p95 latency in ms (default: 65.0)",
    )
    parser.add_argument(
        "--max-p99-ms",
        type=float,
        default=150.0,
        help="Max allowed p99 latency in ms (default: 150.0)",
    )
    args = parser.parse_args()

    temp_dir = tempfile.mkdtemp(prefix="mailtm_load_")
    db_file = Path(temp_dir) / "load_test.db"
    out_dir = Path("benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_prefix = out_dir / "locust_stats"
    html_report = out_dir / "locust_report.html"

    root_key = "test-secret-load-test-key-32bytes!"
    env = os.environ.copy()
    env["MAILY_DATABASE_URL"] = f"sqlite+aiosqlite:///{db_file}"
    env["MAILY_API_KEY"] = root_key
    env["MAILY_SECRET_KEY"] = root_key
    env["MAILY_HOST"] = "127.0.0.1"
    env["MAILY_PORT"] = str(args.port)

    server_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "maily.app.main:create_app",
        "--factory",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--log-level",
        "warning",
    ]

    print(f"Starting test server on http://127.0.0.1:{args.port}...")
    server_proc = subprocess.Popen(server_cmd, env=env)

    try:
        health_url = f"http://127.0.0.1:{args.port}/health"
        if not wait_for_server(health_url, timeout_sec=20.0):
            print("Error: Test server failed to start within timeout", file=sys.stderr)
            return 1

        print("Warming up server before load test...")
        warmup_server(args.port, root_key, rounds=5)

        print("Test server ready. Running Locust load test...")
        locust_cmd = [
            sys.executable,
            "-m",
            "locust",
            "--headless",
            "-f",
            "benchmarks/locustfile.py",
            "-H",
            f"http://127.0.0.1:{args.port}",
            "-u",
            str(args.users),
            "-r",
            str(args.spawn_rate),
            "--run-time",
            args.run_time,
            f"--csv={csv_prefix}",
            f"--html={html_report}",
        ]

        locust_res = subprocess.run(locust_cmd)
        if locust_res.returncode != 0:
            print(f"Warning: Locust exited with code {locust_res.returncode}")

    finally:
        print("Stopping test server...")
        server_proc.terminate()
        with contextlib.suppress(Exception):
            server_proc.wait(timeout=5)
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Parse and validate results
    stats_csv = out_dir / "locust_stats_stats.csv"
    if not stats_csv.is_file():
        print(f"Error: Expected Locust stats file not found: {stats_csv}", file=sys.stderr)
        return 1

    rows: list[dict[str, str]] = []
    with open(stats_csv, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    if not rows:
        print("Error: No data recorded in Locust stats", file=sys.stderr)
        return 1

    agg_row = rows[-1]  # "Aggregated" summary row
    total_reqs = int(agg_row.get("Request Count", 0) or 0)
    fail_count = int(agg_row.get("Failure Count", 0) or 0)
    median_ms = float(agg_row.get("50%", 0) or 0)
    p95_ms = float(agg_row.get("95%", 0) or 0)
    p99_ms = float(agg_row.get("99%", 0) or 0)
    rps = float(agg_row.get("Requests/s", 0) or 0)
    fail_ratio = (fail_count / total_reqs * 100.0) if total_reqs > 0 else 0.0

    print("\n--- Load & Stress Test Summary ---")
    print(f"Total Requests: {total_reqs:,}")
    print(f"Requests / Sec: {rps:,.1f}")
    print(f"Failure Count:  {fail_count} ({fail_ratio:.2f}%)")
    print(f"Latency Median: {median_ms:.2f} ms")
    print(f"Latency p95:    {p95_ms:.2f} ms (max: {args.max_p95_ms:.1f} ms)")
    print(f"Latency p99:    {p99_ms:.2f} ms (max: {args.max_p99_ms:.1f} ms)")

    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    all_passed = fail_count == 0 and p95_ms <= args.max_p95_ms and p99_ms <= args.max_p99_ms
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as sf:
            sf.write("### ⚡ Macro Load & Stress Test Summary\n\n")
            status_badge = "🟢 PASS" if all_passed else "🔴 FAIL"
            sf.write(
                f"**Status:** {status_badge} | **Throughput:** `{rps:,.1f} req/s` | **Total:** `{total_reqs:,}` requests\n\n"
            )
            sf.write("| Metric | Result | Target SLO | Status |\n")
            sf.write("| :--- | :---: | :---: | :---: |\n")
            sf.write(
                f"| **Error Rate** | {fail_ratio:.2f}% ({fail_count}) | `0.00%` | {'🟢' if fail_count == 0 else '🔴'} |\n"
            )
            sf.write(
                f"| **Median (p50)** | {median_ms:.2f} ms | `< 25.0 ms` | {'🟢' if median_ms < 25.0 else '🟡'} |\n"
            )
            sf.write(
                f"| **p95 Latency** | {p95_ms:.2f} ms | `< {args.max_p95_ms:.1f} ms` | {'🟢' if p95_ms <= args.max_p95_ms else '🔴'} |\n"
            )
            sf.write(
                f"| **p99 Latency** | {p99_ms:.2f} ms | `< {args.max_p99_ms:.1f} ms` | {'🟢' if p99_ms <= args.max_p99_ms else '🔴'} |\n\n"
            )

            sf.write("| Endpoint / Task | Requests | Failures | Median (ms) | p95 (ms) | Req/s |\n")
            sf.write("| :--- | :---: | :---: | :---: | :---: | :---: |\n")
            for r in rows[:-1]:
                name = r.get("Name", "unknown")
                cnt = int(r.get("Request Count", 0) or 0)
                fc = int(r.get("Failure Count", 0) or 0)
                med = float(r.get("50%", 0) or 0)
                p95 = float(r.get("95%", 0) or 0)
                r_rps = float(r.get("Requests/s", 0) or 0)
                sf.write(f"| `{name}` | {cnt:,} | {fc} | {med:.1f} | {p95:.1f} | {r_rps:,.1f} |\n")

    if fail_count > 0:
        print(
            f"::error::Load test failed with {fail_count} request failure(s)!",
            file=sys.stderr,
        )
        return 1

    if p95_ms > args.max_p95_ms:
        print(
            f"::error::p95 latency {p95_ms:.2f}ms exceeded SLO threshold of {args.max_p95_ms:.1f}ms!",
            file=sys.stderr,
        )
        return 1

    if p99_ms > args.max_p99_ms:
        print(
            f"::error::p99 latency {p99_ms:.2f}ms exceeded SLO threshold of {args.max_p99_ms:.1f}ms!",
            file=sys.stderr,
        )
        return 1

    print("🟢 Macro load & stress test passed all SLO gates successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
