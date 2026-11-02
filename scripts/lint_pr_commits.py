#!/usr/bin/env python3
"""Lint individual commit messages in a Pull Request against Conventional Commits.

Enforces clean linear commit history:
1. Every commit must follow Conventional Commits (type[(scope)]: description).
2. Forbids sloppy / temporary commit messages (e.g. 'wip', 'fix', 'test').
3. Forbids merge commits within the PR branch (rebase workflow required).
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import subprocess
import sys

CONVENTIONAL_REGEX = re.compile(
    r"^(?P<type>feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert|deps)"
    r"(?:\((?P<scope>[a-zA-Z0-9_\-\./]+)\))?"
    r"(?P<breaking>!)?"
    r":\s+(?P<desc>.{3,100})$"
)

ALLOWED_TYPES = [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert",
    "deps",
]


def run_git(args: list[str]) -> str:
    """Run git command and return stripped stdout."""
    res = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return res.stdout.strip()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Lint commit messages against Conventional Commits."
    )
    parser.add_argument("range", nargs="?", help="Git commit range (e.g. origin/main..HEAD)")
    parser.add_argument(
        "--commit-msg-file", help="Path to commit message file for git commit-msg hook"
    )
    args = parser.parse_args()

    # Mode 1: Validate a single commit message file (for pre-commit commit-msg hook)
    if args.commit_msg_file:
        from pathlib import Path

        msg_path = Path(args.commit_msg_file)
        if not msg_path.is_file():
            print(f"Error: Commit message file not found: {msg_path}", file=sys.stderr)
            return 1
        raw_text = msg_path.read_text(encoding="utf-8", errors="replace")
        lines = [line.strip() for line in raw_text.splitlines()]
        non_comment_lines = [item for item in lines if item and not item.startswith("#")]
        if not non_comment_lines:
            print("Error: Empty commit message.", file=sys.stderr)
            return 1
        subject = non_comment_lines[0]
        # Ignore automatic merge/fixup commits
        if subject.startswith(("Merge ", "fixup! ", "squash! ", "rebase! ")):
            return 0
        match = CONVENTIONAL_REGEX.match(subject)
        if not match:
            print(
                f'\n❌ Invalid commit message: "{subject}"\n'
                f"   Conventional Commits required: <type>[(<scope>)][!]: <description>\n"
                f"   Allowed types: {', '.join(ALLOWED_TYPES)}\n"
                f"   Examples:\n"
                f"     feat(api): add mailbox expiry webhook\n"
                f"     fix(client): handle 429 rate limit retry\n"
                f"     docs: update installation guide\n",
                file=sys.stderr,
            )
            return 1
        print(f'✅ Commit message follows Conventional Commits: "{subject}"')
        return 0

    # Mode 2: Validate a commit range (for PR CI checks)

    commit_range = args.range
    if not commit_range:
        base_ref = os.environ.get("GITHUB_BASE_REF", "main")
        commit_range = f"origin/{base_ref}..HEAD"

    try:
        # Check for merge commits in PR
        merge_commits = run_git(["rev-list", "--merges", commit_range]).splitlines()
        # Get list of commits with hash and subject
        raw_log = run_git(["log", "--format=%H %s", commit_range])
    except Exception as exc:
        print(
            f"Warning: Failed to inspect commits in range '{commit_range}': {exc}", file=sys.stderr
        )
        return 0

    if not raw_log.strip():
        print(f"No commits found in range '{commit_range}'.")
        return 0

    commits: list[tuple[str, str]] = []
    for line in raw_log.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        commit_hash = parts[0]
        subject = parts[1] if len(parts) > 1 else ""
        commits.append((commit_hash, subject))

    errors: list[str] = []
    results: list[dict[str, str | bool]] = []

    # Check merge commits
    if merge_commits:
        errors.append(
            f"Found {len(merge_commits)} merge commit(s). PR branches must use rebase/linear history without merge commits from main."
        )

    for chash, subject in commits:
        match = CONVENTIONAL_REGEX.match(subject)
        is_valid = bool(match)
        short_hash = chash[:7]
        results.append({"hash": short_hash, "subject": subject, "valid": is_valid})

        if not is_valid:
            errors.append(
                f"Commit `{short_hash}` does not follow Conventional Commits:\n"
                f'    "{subject}"\n'
                f"    Allowed types: {', '.join(ALLOWED_TYPES)}\n"
                f"    Format: <type>[(<scope>)][!]: <description> (length 3-100 chars)"
            )

    # Format Markdown Report
    lines: list[str] = []
    lines.append("### 🔍 Git Commit History Lint Report\n")
    lines.append(f"> Validated `{len(commits)}` commit(s) in range `{commit_range}`.\n")
    lines.append("| Commit | Subject | Status |")
    lines.append("| :---: | :--- | :---: |")

    for r in results:
        status_icon = "✅ Clean" if r["valid"] else "❌ Invalid"
        lines.append(f"| `{r['hash']}` | `{r['subject']}` | {status_icon} |")

    lines.append("")

    if errors:
        lines.append("#### ❌ Violations Detected:\n")
        for err in errors:
            lines.append(f"- {err}")
        lines.append("\n> **How to fix:**\n")
        lines.append("> Use interactive rebase to reword invalid commits:\n")
        lines.append("```bash\n")
        lines.append(f"git rebase -i {commit_range.split('..')[0]}\n")
        lines.append("git push --force-with-lease\n")
        lines.append("```\n")

    summary_text = "\n".join(lines)

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(summary_text + "\n")

    print(summary_text)

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
