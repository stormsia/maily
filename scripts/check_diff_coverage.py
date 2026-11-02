#!/usr/bin/env python3
"""PR Diff Coverage Gate.

Uses `diff-cover` to evaluate test coverage specifically on newly added or modified
lines in a Pull Request against the base branch (e.g. origin/main).
Generates a markdown summary for GITHUB_STEP_SUMMARY and updates sticky PR comment.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def format_lines_range(lines: list[int]) -> str:
    """Format a list of line numbers into compact ranges (e.g. 1-3, 7, 10-12)."""
    if not lines:
        return "None"
    sorted_lines = sorted(lines)
    ranges: list[str] = []
    start = sorted_lines[0]
    prev = sorted_lines[0]

    for line in sorted_lines[1:]:
        if line == prev + 1:
            prev = line
        else:
            ranges.append(f"{start}-{prev}" if start != prev else str(start))
            start = line
            prev = line
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def generate_markdown_report(
    data: dict[str, Any],
    threshold: float,
    compare_branch: str,
) -> tuple[str, bool]:
    """Generate Markdown report and return (markdown_text, is_success)."""
    total_lines = int(data.get("total_num_lines", 0))
    total_violations = int(data.get("total_num_violations", 0))
    pct_covered = float(data.get("total_percent_covered", 100.0))
    covered_lines = max(0, total_lines - total_violations)

    lines: list[str] = []
    lines.append("## 🎯 PR Diff Coverage Report\n")

    if total_lines == 0:
        lines.append(
            f"> **Verdict:** 🟢 **PASS** | Base: `{compare_branch}` | **0** executable code lines in PR diff."
        )
        return "\n".join(lines), True

    is_success = pct_covered >= threshold
    status_icon = "🟢 **PASS**" if is_success else "🔴 **FAIL**"
    score_badge = f"🟢 `{pct_covered:.1f}%`" if is_success else f"🔴 `{pct_covered:.1f}%`"

    lines.append(
        f"> **Verdict:** {status_icon} | **Diff Coverage:** {score_badge} | "
        f"**Threshold:** `{threshold:.1f}%` | **Lines:** `{covered_lines}/{total_lines}` covered\n"
    )

    lines.append("| Source File | Lines in PR | Covered | Missing | Coverage % | Uncovered Lines |")
    lines.append("| :--- | :---: | :---: | :---: | :---: | :--- |")

    src_stats = data.get("src_stats", {})
    for src_path, stats in sorted(src_stats.items()):
        total_f_lines = len(stats.get("covered_lines", [])) + len(stats.get("violation_lines", []))
        if total_f_lines == 0:
            continue
        missing_lines = stats.get("violation_lines", [])
        covered_f_lines = total_f_lines - len(missing_lines)
        f_pct = float(stats.get("percent_covered", 100.0))
        pct_display = f"🟢 **{f_pct:.1f}%**" if f_pct >= threshold else f"🔴 **{f_pct:.1f}%**"
        missing_display = format_lines_range(missing_lines)

        lines.append(
            f"| `{src_path}` | {total_f_lines} | {covered_f_lines} | {len(missing_lines)} | {pct_display} | `{missing_display}` |"
        )

    lines.append("")

    if not is_success:
        lines.append("### ⚠️ Coverage Threshold Not Met\n")
        lines.append(
            f"The PR introduces executable lines without sufficient test coverage (`{pct_covered:.1f}%` < `{threshold:.1f}%`).\n"
            "Please add unit or integration tests for the uncovered lines listed above before merging."
        )

    return "\n".join(lines), is_success


def post_sticky_pr_comment(comment_body: str) -> None:
    """Post or update sticky PR comment using GitHub CLI."""
    pr_number = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_PR_NUMBER")
    repo = os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    if not pr_number or not repo or not gh_token:
        print("Note: Sticky PR comment skipped (missing PR_NUMBER or REPO or GH_TOKEN).")
        return

    marker = "<!-- maily-pr-diff-coverage-summary -->"
    full_body = f"{marker}\n\n{comment_body}"

    try:
        cmd_find = [
            "gh",
            "api",
            f"repos/{repo}/issues/{pr_number}/comments",
            "--jq",
            f'.[] | select(.body | startswith("{marker}")) | .id',
        ]
        out = subprocess.check_output(cmd_find, text=True, stderr=subprocess.DEVNULL)
        existing_id = out.strip().splitlines()[0] if out.strip() else None

        if existing_id:
            print(f"Updating existing PR diff coverage comment (ID: {existing_id})...")
            cmd_update = [
                "gh",
                "api",
                "-X",
                "PATCH",
                f"repos/{repo}/issues/comments/{existing_id}",
                "-f",
                f"body={full_body}",
            ]
            subprocess.run(cmd_update, check=True, stdout=subprocess.DEVNULL)
        else:
            print("Posting new PR diff coverage comment...")
            cmd_create = ["gh", "pr", "comment", str(pr_number), "--body", full_body]
            subprocess.run(cmd_create, check=True, stdout=subprocess.DEVNULL)
    except Exception as exc:
        print(f"Warning: Failed to update PR sticky comment: {exc}", file=sys.stderr)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Check test coverage of PR diff lines.")
    parser.add_argument(
        "coverage_file",
        nargs="?",
        default="coverage.xml",
        type=Path,
        help="Path to coverage XML file (default: coverage.xml)",
    )
    parser.add_argument(
        "--compare-branch",
        default="origin/main",
        help="Base branch to compare diff against (default: origin/main)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=85.0,
        help="Minimum required diff coverage percentage (default: 85.0%%)",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=None,
        help="Optional path to output markdown summary file",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=None,
        help="Optional path to output raw json summary file",
    )
    parser.add_argument(
        "--sticky-pr",
        action="store_true",
        help="Post or update sticky PR comment via GitHub CLI",
    )
    args = parser.parse_args()

    if not args.coverage_file.is_file():
        print(f"Error: Coverage file not found: {args.coverage_file}", file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_json = Path(tmp.name)

    try:
        cmd = [
            sys.executable,
            "-m",
            "diff_cover.diff_cover_tool",
            str(args.coverage_file),
            f"--compare-branch={args.compare_branch}",
            f"--format=json:{tmp_json}",
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode not in (0, 1):
            print(
                f"Error running diff-cover:\n{res.stderr}\n{res.stdout}",
                file=sys.stderr,
            )
            return 1

        with open(tmp_json, encoding="utf-8") as f:
            data = json.load(f)
        if args.json_output:
            args.json_output.write_text(json.dumps(data, indent=2), encoding="utf-8")
    finally:
        with contextlib.suppress(Exception):
            tmp_json.unlink()

    markdown_text, is_success = generate_markdown_report(
        data=data,
        threshold=args.threshold,
        compare_branch=args.compare_branch,
    )

    print(markdown_text)

    # Write to GITHUB_STEP_SUMMARY
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(markdown_text + "\n")
        print(f"Diff coverage summary appended to {summary_path}")

    if args.output_markdown:
        args.output_markdown.write_text(markdown_text, encoding="utf-8")

    if args.sticky_pr:
        post_sticky_pr_comment(markdown_text)

    if not is_success:
        print(f"::error::PR diff coverage is below required threshold {args.threshold:.1f}%!")
        return 1

    print(f"PR diff coverage passed (>= {args.threshold:.1f}%).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
