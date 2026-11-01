#!/usr/bin/env python3
"""Intelligent Mutation Testing Runner & Quality Gate for mailtmapi.

Supports:
1. Predefined module profiles (crypto_misc, auth_security, retention_retry, all).
2. Git diff-aware mutation for PRs (mutates only files modified in the PR diff).
3. Automated test selection mapping for sub-minute execution.
4. CI/CD Step Summary generation and quality gate enforcement (survived == 0).
"""

from __future__ import annotations

import argparse
import atexit
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

# Mapping of critical source files to their targeted test suites
FILE_TO_TESTS_MAP: dict[str, list[str]] = {
    "src/mailtmapi/crypto.py": ["tests/test_crypto.py"],
    "src/mailtmapi/utils/misc.py": ["tests/test_misc.py"],
    "src/mailtmapi/app/authz.py": ["tests/test_authz.py"],
    "src/mailtmapi/app/services/keys.py": [
        "tests/test_keys_service.py",
        "tests/test_keys_router.py",
    ],
    "src/mailtmapi/app/middleware/origin.py": ["tests/test_security_routing.py"],
    "src/mailtmapi/app/services/retention.py": [
        "tests/test_retention_lifecycle.py",
        "tests/test_retention_scope.py",
    ],
    "src/mailtmapi/utils/retry.py": ["tests/test_retry.py"],
    "src/mailtmapi/app/services/mailboxes.py": [
        "tests/test_mailboxes_service.py",
        "tests/test_mailbox_ownership.py",
    ],
}

PROFILES: dict[str, dict[str, list[str]]] = {
    "crypto_misc": {
        "mutate": [
            "src/mailtmapi/crypto.py",
            "src/mailtmapi/utils/misc.py",
        ],
        "tests": [
            "tests/test_crypto.py",
            "tests/test_misc.py",
        ],
    },
    "auth_security": {
        "mutate": [
            "src/mailtmapi/app/authz.py",
            "src/mailtmapi/app/services/keys.py",
            "src/mailtmapi/app/middleware/origin.py",
        ],
        "tests": [
            "tests/test_authz.py",
            "tests/test_keys_service.py",
            "tests/test_keys_router.py",
            "tests/test_security_routing.py",
        ],
    },
    "retention_retry": {
        "mutate": [
            "src/mailtmapi/app/services/retention.py",
            "src/mailtmapi/utils/retry.py",
        ],
        "tests": [
            "tests/test_retention_lifecycle.py",
            "tests/test_retention_scope.py",
            "tests/test_retry.py",
        ],
    },
}


def get_diff_files(base_ref: str) -> list[str]:
    """Return list of modified files compared to base_ref."""
    try:
        cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return [line.strip().replace("\\", "/") for line in output.splitlines() if line.strip()]
    except Exception as exc:
        print(f"Warning: Failed to compute git diff against {base_ref}: {exc}")
        return []


def patch_pyproject_toml(mutate_paths: list[str], test_paths: list[str]) -> Path:
    """Temporarily update [tool.mutmut] in pyproject.toml with target scope."""
    pyproject = Path("pyproject.toml")
    backup = Path("pyproject.toml.mutmut_bak")
    shutil.copyfile(pyproject, backup)

    def _restore() -> None:
        if backup.exists():
            shutil.copyfile(backup, pyproject)
            backup.unlink()

    atexit.register(_restore)

    content = pyproject.read_text(encoding="utf-8")
    mutmut_marker = "[tool.mutmut]"
    if mutmut_marker in content:
        content = content.split(mutmut_marker)[0].rstrip() + "\n"

    mutate_lines = "\n".join(f'    "{p}",' for p in mutate_paths)
    test_lines = "\n".join(f'    "{t}",' for t in test_paths)

    new_section = f"""[tool.mutmut]
source_paths = ["src"]
only_mutate = [
{mutate_lines}
]
pytest_add_cli_args_test_selection = [
{test_lines}
]
pytest_add_cli_args = [
    "-q",
    "-n",
    "0",
]
"""
    pyproject.write_text(content + "\n" + new_section, encoding="utf-8")
    return backup


def evaluate_mutation_results(stats_file: Path, profile_name: str) -> int:
    """Read mutmut CI/CD json stats, write Step Summary, and evaluate gate."""
    if not stats_file.exists():
        print(f"::error::Mutation stats file {stats_file} not found!")
        return 1

    try:
        with open(stats_file, encoding="utf-8") as f:
            stats = json.load(f)
    except Exception as exc:
        print(f"::error::Failed to parse {stats_file}: {exc}")
        return 1

    killed = stats.get("killed", 0)
    survived = stats.get("survived", 0)
    no_tests = stats.get("no_tests", 0)
    timeout = stats.get("timeout", 0)
    total = stats.get("total", 0)
    skipped = stats.get("skipped", 0)

    tested = total - skipped
    score = 0.0 if tested <= 0 else ((killed + timeout) / tested) * 100

    print(
        f"Mutation Summary [{profile_name}]: "
        f"killed={killed}, survived={survived}, no_tests={no_tests}, "
        f"timeout={timeout}, total={total}, score={score:.1f}%"
    )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(f"### 🧬 Mutation Testing — {profile_name}\n\n")
            status_badge = "🟢 PASS" if (survived == 0 and no_tests == 0) else "🔴 FAIL"
            sf.write(f"**Gate Status:** {status_badge} | **Score:** `{score:.1f}%`\n\n")
            sf.write("| Metric | Count |\n")
            sf.write("| :--- | :---: |\n")
            sf.write(f"| **Score** | **{score:.1f}%** |\n")
            sf.write(f"| Total Mutants | {total} |\n")
            sf.write(f"| Killed | {killed} |\n")
            sf.write(f"| Survived | {survived} |\n")
            sf.write(f"| No Tests | {no_tests} |\n")
            sf.write(f"| Timeout | {timeout} |\n\n")

    if survived > 0 or no_tests > 0:
        print(f"::error::Mutation testing failed quality gate: {survived} survived, {no_tests} untested mutants!")
        return 1

    print(f"Mutation testing quality gate passed for {profile_name}: 0 survived mutants.")
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Run mutation tests with targeted scopes or git diff.")
    parser.add_argument(
        "--profile",
        choices=list(PROFILES.keys()) + ["all"],
        help="Predefined module profile to mutate",
    )
    parser.add_argument(
        "--diff-base",
        help="Git base ref (e.g. origin/main) to run mutation tests only on files modified in the diff",
    )
    args = parser.parse_args()

    target_mutate: list[str] = []
    target_tests: set[str] = set()
    label = "custom"

    if args.diff_base:
        diff_files = get_diff_files(args.diff_base)
        print(f"Detected {len(diff_files)} modified file(s) in PR diff against {args.diff_base}")
        matched_files: list[str] = []
        for df in diff_files:
            if df in FILE_TO_TESTS_MAP:
                matched_files.append(df)
                target_tests.update(FILE_TO_TESTS_MAP[df])

        if not matched_files:
            print("🟢 No mutation-monitored files touched in this PR diff. Skipping mutation run.")
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path:
                with open(summary_path, "a", encoding="utf-8") as sf:
                    sf.write("### 🧬 Mutation Testing (PR Diff)\n\n")
                    sf.write("⚪ *No mutation-monitored files were changed in this PR. Check skipped.*\n")
            return 0

        target_mutate = matched_files
        label = f"PR Diff ({len(matched_files)} files)"
    elif args.profile:
        label = args.profile
        if args.profile == "all":
            for prof in PROFILES.values():
                target_mutate.extend(prof["mutate"])
                target_tests.update(prof["tests"])
        else:
            prof = PROFILES[args.profile]
            target_mutate = prof["mutate"]
            target_tests.update(prof["tests"])
    else:
        # Default fallback: crypto_misc
        label = "crypto_misc"
        prof = PROFILES["crypto_misc"]
        target_mutate = prof["mutate"]
        target_tests.update(prof["tests"])

    print(f"Configuring mutmut for [{label}]:")
    print(f"  Files to mutate: {target_mutate}")
    print(f"  Test suite: {sorted(target_tests)}")

    patch_pyproject_toml(target_mutate, sorted(target_tests))

    # Clean previous mutants dir
    shutil.rmtree("mutants", ignore_errors=True)

    print("Running mutmut run...")
    run_cmd = ["mutmut", "run"]
    subprocess.run(run_cmd)

    print("Exporting CI/CD stats...")
    subprocess.run(["mutmut", "export-cicd-stats"], check=False)

    stats_file = Path("mutants/mutmut-cicd-stats.json")
    return evaluate_mutation_results(stats_file, label)


if __name__ == "__main__":
    sys.exit(main())
