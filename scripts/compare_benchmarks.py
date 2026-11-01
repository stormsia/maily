#!/usr/bin/env python3
"""Compare pytest-benchmark JSON outputs between Base and HEAD branches.

Detects performance regressions, computes throughput and latency deltas,
and generates a rich GitHub Flavored Markdown summary report.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
from pathlib import Path


def format_latency(seconds: float) -> str:
    """Format duration in human-readable milliseconds or microseconds."""
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.1f} µs"
    return f"{seconds * 1_000:.3f} ms"


def format_ops(ops: float) -> str:
    """Format operations per second."""
    if ops >= 1_000:
        return f"{ops:,.1f}"
    return f"{ops:.1f}"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Compare base and head benchmark JSON files.")
    parser.add_argument("base", type=Path, help="Base branch benchmark JSON file")
    parser.add_argument("head", type=Path, help="HEAD/PR branch benchmark JSON file")
    parser.add_argument(
        "--threshold",
        type=float,
        default=25.0,
        help="Max allowed latency regression percentage before failing (default: 25.0%%)",
    )
    parser.add_argument(
        "--min-delta-ms",
        type=float,
        default=0.5,
        help="Minimum absolute latency increase in ms to count as regression (avoids sub-ms CI jitter, default: 0.5ms)",
    )
    args = parser.parse_args()

    if not args.base.is_file():
        print(f"Error: Base benchmark file not found: {args.base}", file=sys.stderr)
        return 1
    if not args.head.is_file():
        print(f"Error: Head benchmark file not found: {args.head}", file=sys.stderr)
        return 1

    with open(args.base, encoding="utf-8") as f:
        base_data = json.load(f)
    with open(args.head, encoding="utf-8") as f:
        head_data = json.load(f)

    base_map = {b["name"]: b for b in base_data.get("benchmarks", [])}
    head_benchmarks = head_data.get("benchmarks", [])

    rows: list[dict[str, str | float | bool]] = []
    regressions: list[str] = []

    for hb in head_benchmarks:
        name = hb.get("name", "unknown")
        group = hb.get("group", "default") or "default"
        h_stats = hb.get("stats", {})
        h_mean = float(h_stats.get("mean", 0.0))
        h_ops = float(h_stats.get("ops", 0.0))

        bb = base_map.get(name)
        if not bb:
            rows.append(
                {
                    "name": name,
                    "group": group,
                    "base_latency": "—",
                    "head_latency": format_latency(h_mean),
                    "delta_pct": 0.0,
                    "delta_str": "New",
                    "base_ops": "—",
                    "head_ops": format_ops(h_ops),
                    "status": "🆕 Added",
                    "is_regression": False,
                }
            )
            continue

        b_stats = bb.get("stats", {})
        b_mean = float(b_stats.get("mean", 0.0))
        b_ops = float(b_stats.get("ops", 0.0))

        latency_delta = (h_mean - b_mean) / b_mean * 100 if b_mean > 0 else 0.0
        abs_increase_s = h_mean - b_mean
        min_delta_s = args.min_delta_ms / 1000.0

        is_regression = latency_delta > args.threshold and abs_increase_s >= min_delta_s

        if latency_delta <= -5.0:
            delta_str = f"🟢 {abs(latency_delta):.1f}% faster"
            verdict = "🟢 Improved"
        elif latency_delta <= 10.0 or (latency_delta > 0 and abs_increase_s < min_delta_s):
            sign = "+" if latency_delta > 0 else ""
            delta_str = f"🟢 {sign}{latency_delta:.1f}%"
            verdict = "🟢 Stable"
        elif latency_delta <= args.threshold:
            delta_str = f"🟡 +{latency_delta:.1f}% slower"
            verdict = "🟡 Warning"
        else:
            delta_str = f"🔴 +{latency_delta:.1f}% slower"
            verdict = "🔴 Regression"
            regressions.append(
                f"`{name}` ({group}): {format_latency(b_mean)} -> {format_latency(h_mean)} (+{latency_delta:.1f}% slower, threshold {args.threshold:.1f}%)"
            )

        rows.append(
            {
                "name": name,
                "group": group,
                "base_latency": format_latency(b_mean),
                "head_latency": format_latency(h_mean),
                "delta_pct": latency_delta,
                "delta_str": delta_str,
                "base_ops": format_ops(b_ops),
                "head_ops": format_ops(h_ops),
                "status": verdict,
                "is_regression": is_regression,
            }
        )

    # Sort rows by group then name
    rows.sort(key=lambda r: (str(r["group"]), str(r["name"])))

    # Build Markdown Report
    lines: list[str] = []
    lines.append("## ⚡ PR Performance Regression & Benchmark Comparison\n")

    overall_verdict = (
        "🟢 **PASS (No Regressions Detected)**"
        if not regressions
        else f"🔴 **FAIL ({len(regressions)} Regression(s) Detected)**"
    )
    lines.append(
        f"> **Verdict:** {overall_verdict} | **Regression Threshold:** `+{args.threshold:.1f}%`\n"
    )

    lines.append(
        "| Benchmark | Group | Base Mean | PR Mean | Latency Delta | Base Ops/s | PR Ops/s | Status |"
    )
    lines.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")

    for r in rows:
        bname = f"`{r['name']}`"
        lines.append(
            f"| {bname} | {r['group']} | {r['base_latency']} | {r['head_latency']} | {r['delta_str']} | {r['base_ops']} | {r['head_ops']} | {r['status']} |"
        )

    lines.append("")

    if regressions:
        lines.append("### ⚠️ Performance Regressions Detected:\n")
        for reg in regressions:
            lines.append(f"- 🔴 {reg}")
        lines.append(
            "\n> **Action required:** Please profile the affected component before merging."
        )
        lines.append("")

    summary_text = "\n".join(lines)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(summary_text + "\n")

    print(summary_text)

    return 1 if regressions else 0


if __name__ == "__main__":
    sys.exit(main())
