#!/usr/bin/env python3
"""Intelligent Mutation Testing Runner & Quality Gate for maily.

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

from typing_extensions import TypedDict

# Mapping of critical source files to their targeted test suites
FILE_TO_TESTS_MAP: dict[str, list[str]] = {
    "src/maily/crypto.py": ["tests/test_crypto.py"],
    "src/maily/utils/misc.py": ["tests/test_misc.py"],
    "src/maily/app/authz.py": [
        "tests/test_authz.py",
        "tests/test_authz_properties.py",
        "tests/test_scope_filters.py",
        "tests/test_mailbox_ownership.py",
        "tests/test_security_routing.py",
    ],
    "src/maily/app/services/keys.py": [
        "tests/test_keys_service.py",
        "tests/test_keys_router.py",
        "tests/test_api_keys.py",
        "tests/test_authz_properties.py",
    ],
    "src/maily/app/middleware/origin.py": [
        "tests/test_security_routing.py",
        "tests/test_authz_properties.py",
    ],
    "src/maily/app/services/retention.py": [
        "tests/test_retention_lifecycle.py",
        "tests/test_retention_scope.py",
        "tests/test_stats_retention_history.py",
    ],
    "src/maily/utils/retry.py": ["tests/test_retry.py"],
    "src/maily/app/services/mailboxes.py": [
        "tests/test_mailboxes_service.py",
        "tests/test_mailbox_ownership.py",
    ],
}


class ProfileConfig(TypedDict):
    mutate: list[str]
    tests: list[str]
    min_score: float
    max_survived: int


PROFILES: dict[str, ProfileConfig] = {
    "crypto_misc": {
        "mutate": [
            "src/maily/crypto.py",
            "src/maily/utils/misc.py",
        ],
        "tests": [
            "tests/test_crypto.py",
            "tests/test_misc.py",
        ],
        "min_score": 100.0,
        "max_survived": 0,
    },
    "auth_security": {
        "mutate": [
            "src/maily/app/authz.py",
            "src/maily/app/services/keys.py",
            "src/maily/app/middleware/origin.py",
        ],
        "tests": [
            "tests/test_authz.py",
            "tests/test_authz_properties.py",
            "tests/test_keys_service.py",
            "tests/test_keys_router.py",
            "tests/test_api_keys.py",
            "tests/test_security_routing.py",
            "tests/test_scope_filters.py",
            "tests/test_mailbox_ownership.py",
        ],
        "min_score": 90.0,
        "max_survived": 50,
    },
    "retention_retry": {
        "mutate": [
            "src/maily/app/services/retention.py",
            "src/maily/utils/retry.py",
        ],
        "tests": [
            "tests/test_retention_lifecycle.py",
            "tests/test_retention_scope.py",
            "tests/test_stats_retention_history.py",
            "tests/test_retry.py",
        ],
        "min_score": 65.0,
        "max_survived": 140,
    },
}


def get_diff_files(base_ref: str) -> list[str]:
    """Return list of modified files compared to base_ref."""
    try:
        cmd = ["git", "diff", "--name-only", f"{base_ref}...HEAD"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        return [
            line.strip().replace("\\", "/")
            for line in output.splitlines()
            if line.strip()
        ]
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
also_copy = [
    "alembic",
    "alembic.ini",
]
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


def evaluate_mutation_results(
    stats_file: Path,
    profile_name: str,
    min_score: float = 70.0,
    max_survived: int = 0,
) -> int:
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

    passed = (total == 0) or (
        score >= min_score and survived <= max_survived and (killed + timeout) > 0
    )

    print(
        f"Mutation Summary [{profile_name}]: "
        f"killed={killed}, survived={survived}, no_tests={no_tests}, "
        f"timeout={timeout}, total={total}, score={score:.1f}% "
        f"(targets: score>={min_score:.1f}%, max_survived<={max_survived})"
    )

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(f"### 🧬 Mutation Testing — {profile_name}\n\n")
            status_badge = "🟢 PASS" if passed else "🔴 FAIL"
            sf.write(
                f"**Gate Status:** {status_badge} | **Score:** `{score:.1f}%` (target: `{min_score:.1f}%`)\n\n"
            )
            sf.write("| Metric | Count | Target / Ratchet |\n")
            sf.write("| :--- | :---: | :---: |\n")
            sf.write(
                f"| **Mutation Score** | **{score:.1f}%** | $\\ge {min_score:.1f}%$ |\n"
            )
            sf.write(f"| Total Mutants | {total} | — |\n")
            sf.write(f"| Killed Mutants | {killed} | — |\n")
            sf.write(f"| Survived Mutants | {survived} | $\\le {max_survived}$ |\n")
            sf.write(f"| Untested Mutants | {no_tests} | 0 |\n")
            sf.write(f"| Timeout | {timeout} | — |\n\n")

    if total > 0 and (killed + timeout) == 0:
        print(
            f"::error::Mutation testing failed: zero mutants killed or run aborted out of {total} mutants!"
        )
        return 1

    if score < min_score:
        print(
            f"::error::Mutation score {score:.1f}% is below required threshold of {min_score:.1f}%!"
        )
        return 1

    if survived > max_survived:
        print(
            f"::error::Mutation testing failed quality gate: {survived} survived mutants (max allowed: {max_survived})!"
        )
        return 1

    print(
        f"Mutation testing quality gate passed for {profile_name}: "
        f"score={score:.1f}% >= {min_score:.1f}%, survived={survived} <= {max_survived}."
    )
    return 0


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description="Run mutation tests with targeted scopes or git diff."
    )
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
        print(
            f"Detected {len(diff_files)} modified file(s) in PR diff against {args.diff_base}"
        )
        matched_files: list[str] = []
        for df in diff_files:
            if df in FILE_TO_TESTS_MAP:
                matched_files.append(df)
                target_tests.update(FILE_TO_TESTS_MAP[df])

        if not matched_files:
            print(
                "🟢 No mutation-monitored files touched in this PR diff. Skipping mutation run."
            )
            summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
            if summary_path:
                with open(summary_path, "a", encoding="utf-8") as sf:
                    sf.write("### 🧬 Mutation Testing (PR Diff)\n\n")
                    sf.write(
                        "⚪ *No mutation-monitored files were changed in this PR. Check skipped.*\n"
                    )
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
    min_score = 70.0
    max_survived = 0

    if args.profile and args.profile in PROFILES:
        min_score = float(PROFILES[args.profile].get("min_score", 70.0))
        max_survived = int(PROFILES[args.profile].get("max_survived", 0))

    return evaluate_mutation_results(
        stats_file, label, min_score=min_score, max_survived=max_survived
    )


if __name__ == "__main__":
    sys.exit(main())
