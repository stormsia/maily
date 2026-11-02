#!/usr/bin/env python3
"""PR Size & Complexity Labeler.

Calculates the net non-generated diff size of a Pull Request, assigns standardized
`size/XS` through `size/XL` labels via GitHub CLI, and renders a summary table in
GITHUB_STEP_SUMMARY.
"""

from __future__ import annotations

import argparse
import contextlib
import fnmatch
import os
import subprocess
import sys
from pathlib import Path

SIZE_DEFINITIONS = [
    ("size/XS", 0, 29, "3CBF00", "Extra small change (< 30 lines)"),
    ("size/S", 30, 99, "5D9CEC", "Small change (30-99 lines)"),
    ("size/M", 100, 299, "F5D76E", "Medium change (100-299 lines)"),
    ("size/L", 300, 799, "F64747", "Large change (300-799 lines)"),
    ("size/XL", 800, sys.maxsize, "6C7A89", "Extra large change (>= 800 lines)"),
]

IGNORED_PATTERNS = [
    "uv.lock",
    "client/maily_client.py",
    "*.svg",
    "*.png",
    "*.jpg",
    "*.ico",
    "*.min.js",
    "*.min.css",
    ".trivyignore",
    "zizmor.yml",
    ".gitignore",
]


def is_ignored(path_str: str) -> bool:
    """Check if file should be excluded from size calculation."""
    normalized = path_str.replace("\\", "/")
    for pattern in IGNORED_PATTERNS:
        if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(Path(normalized).name, pattern):
            return True
    return False


def get_diff_stats(base_ref: str) -> tuple[int, int, int, list[dict[str, str | int]]]:
    """Parse git diff --numstat against base_ref."""
    cmd = ["git", "diff", "--numstat", f"{base_ref}..HEAD"]
    out = subprocess.check_output(cmd, text=True, errors="replace")

    total_add = 0
    total_del = 0
    file_records: list[dict[str, str | int]] = []

    for line in out.strip().splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        add_str, del_str, file_path = parts
        if is_ignored(file_path):
            continue
        try:
            add = int(add_str)
            dels = int(del_str)
        except ValueError:
            # Binary files show '-'
            continue

        total_add += add
        total_del += dels
        file_records.append(
            {
                "file": file_path,
                "add": add,
                "del": dels,
                "total": add + dels,
            }
        )

    file_records.sort(key=lambda r: int(r["total"]), reverse=True)
    return total_add, total_del, len(file_records), file_records


def determine_size_label(total_lines: int) -> tuple[str, str, str]:
    """Return (label_name, color, description)."""
    for label, min_lines, max_lines, color, desc in SIZE_DEFINITIONS:
        if min_lines <= total_lines <= max_lines:
            return label, color, desc
    return "size/XL", "6C7A89", "Extra large change"


def apply_github_label(
    pr_number: str,
    target_label: str,
    color: str,
    description: str,
    repo: str,
) -> None:
    """Ensure label exists and update PR labels via gh CLI."""
    all_size_labels = [label for label, _, _, _, _ in SIZE_DEFINITIONS]

    try:
        # 1. Ensure label exists in repository
        subprocess.run(
            [
                "gh",
                "label",
                "create",
                target_label,
                "--color",
                color,
                "--description",
                description,
                "--repo",
                repo,
                "--force",
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        # 2. Fetch current PR labels
        out = subprocess.check_output(
            [
                "gh",
                "pr",
                "view",
                str(pr_number),
                "--repo",
                repo,
                "--json",
                "labels",
                "--jq",
                ".labels[].name",
            ],
            text=True,
            errors="replace",
        )
        current_labels = set(out.strip().splitlines())

        # 3. Remove other size labels
        labels_to_remove = [
            lbl for lbl in all_size_labels if lbl in current_labels and lbl != target_label
        ]
        for lbl in labels_to_remove:
            subprocess.run(
                ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--remove-label", lbl],
                capture_output=True,
                check=False,
            )

        # 4. Add target size label
        if target_label not in current_labels:
            subprocess.run(
                ["gh", "pr", "edit", str(pr_number), "--repo", repo, "--add-label", target_label],
                capture_output=True,
                check=True,
            )
            print(f"Applied label '{target_label}' to PR #{pr_number}")
        else:
            print(f"PR #{pr_number} already has label '{target_label}'")
    except Exception as exc:
        print(f"Warning: Could not update PR labels via gh CLI: {exc}", file=sys.stderr)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Label PR by change size and complexity.")
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Base branch to diff against (default: origin/main)",
    )
    parser.add_argument(
        "--pr-number",
        default=os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_PR_NUMBER"),
        help="PR number (default: read from PR_NUMBER env var)",
    )
    args = parser.parse_args()

    total_add, total_del, file_count, top_files = get_diff_stats(args.base_ref)
    total_lines = total_add + total_del

    target_label, color, description = determine_size_label(total_lines)

    lines: list[str] = []
    lines.append("## 📏 Pull Request Size & Complexity Audit\n")
    lines.append(
        f"> **Assigned Size:** `{target_label}` ({description}) | "
        f"**Changes:** `+{total_add}` / `-{total_del}` (`{total_lines}` lines total) | "
        f"**Files Changed:** `{file_count}`\n"
    )

    if target_label == "size/XL":
        lines.append(
            "> [!WARNING]\n"
            "> **Large PR Detected:** This PR modifies over 800 lines of non-generated code. "
            "Large PRs take longer to review and have higher regression rates. "
            "Please consider splitting this PR into smaller, independent pull requests.\n"
        )

    if top_files:
        lines.append("| Modified File | Lines Changed | Additions | Deletions |")
        lines.append("| :--- | :---: | :---: | :---: |")
        for rec in top_files[:10]:
            lines.append(
                f"| `{rec['file']}` | {rec['total']} | `+{rec['add']}` | `-{rec['del']}` |"
            )
        if len(top_files) > 10:
            lines.append(f"| *...and {len(top_files) - 10} more file(s)* | | | |")
        lines.append("")

    report = "\n".join(lines)
    print(report)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(report + "\n")

    repo = os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY")
    if args.pr_number and repo:
        apply_github_label(
            pr_number=args.pr_number,
            target_label=target_label,
            color=color,
            description=description,
            repo=repo,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
