# ruff: noqa: E402
#!/usr/bin/env python3
"""Live Provider Health & E2E Email Delivery Verification Suite.

Performs live end-to-end operations (target discovery, mailbox creation,
inbox listing, email delivery, and deletion) across all supported public providers.
Updates README status badges, tracks consecutive failures, and manages GitHub issues.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure local packages and scripts are importable
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "src"))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from mailtmapi.http import HttpClient
from mailtmapi.providers.anonymmail_net import AnonymMailNet
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.dispoemail_org import DispoEmailOrg
from mailtmapi.providers.mailtm import MailTM
from mailtmapi.providers.noopmail_org import NoopMail
from mailtmapi.providers.temp_tf import TempTF
from mailtmapi.providers.tempmail_io import TempMailIO
from mailtmapi.providers.tempmail_plus import TempMailPlus
from test_mail_sender import TestEmailSender

__test__ = False


@dataclass
class ProviderTestResult:
    slug: str
    name: str
    website: str
    success: bool
    stage: str  # "targets", "create", "messages", "delete", "delivery", "ok"
    targets_count: int = 0
    mailbox_address: str = ""
    duration_s: float = 0.0
    error: str = ""
    delivery_tested: bool = False
    delivery_success: bool | None = None
    delivery_duration_s: float = 0.0
    delivery_error: str = ""

    @property
    def fully_operational(self) -> bool:
        """True if basic API operations passed, and if delivery was tested, delivery also passed."""
        if not self.success:
            return False
        if self.delivery_tested:
            return bool(self.delivery_success)
        return True

    @property
    def effective_stage(self) -> str:
        if not self.success:
            return self.stage
        if self.delivery_tested and not self.delivery_success:
            return "delivery"
        return "ok"

    @property
    def effective_error(self) -> str:
        if not self.success:
            return self.error
        if self.delivery_tested and not self.delivery_success:
            return self.delivery_error or "Delivery timed out or message not received"
        return ""


PROVIDER_FACTORIES = [
    ("mail.tm", "Mail.tm", "https://mail.tm", lambda client: MailTM(http=client)),
    (
        "tempmail.plus",
        "TempMail Plus",
        "https://tempmail.plus",
        lambda client: TempMailPlus(http=client),
    ),
    ("temp-mail.io", "TempMail.io", "https://temp-mail.io", lambda client: TempMailIO(http=client)),
    ("temp.tf", "Temp.tf", "https://temp.tf", lambda client: TempTF(http=client)),
    (
        "anonymmail.net",
        "AnonymMail.net",
        "https://anonymmail.net",
        lambda client: AnonymMailNet(http=client),
    ),
    (
        "dispoemail.org",
        "DispoEmail.org",
        "https://dispoemail.org",
        lambda client: DispoEmailOrg(http=client),
    ),
    ("noopmail.org", "NoopMail.org", "https://noopmail.org", lambda client: NoopMail(http=client)),
]


async def execute_provider_operations(
    provider: Any,
    name: str,
    website: str,
    timeout_s: float = 25.0,
) -> ProviderTestResult:
    """Execute live CRUD operations for a single mail provider."""
    slug = provider.slug
    t0 = time.monotonic()
    created_mb: MailboxInfo | None = None

    try:
        # 1. Target discovery
        targets = await asyncio.wait_for(provider.list_targets(fresh=True), timeout=timeout_s)
        if not targets:
            raise RuntimeError(f"No available domain targets returned by {slug}")
        targets_count = len(targets)

        # 2. Mailbox creation
        mb = await asyncio.wait_for(
            provider.create_mailbox(MailboxSpec()),
            timeout=timeout_s,
        )
        created_mb = mb
        if not mb.address or "@" not in mb.address:
            raise RuntimeError(f"Invalid mailbox address returned: {mb.address!r}")

        # 3. Message listing
        await asyncio.wait_for(provider.list_messages(mb), timeout=timeout_s)

        # 4. Mailbox cleanup / deletion
        caps = getattr(provider, "capabilities", None)
        if caps is None or caps.supports_delete_mailbox:
            await asyncio.wait_for(provider.delete_mailbox(mb), timeout=timeout_s)

        total_dur = time.monotonic() - t0
        return ProviderTestResult(
            slug=slug,
            name=name,
            website=website,
            success=True,
            stage="ok",
            targets_count=targets_count,
            mailbox_address=mb.address,
            duration_s=total_dur,
        )

    except asyncio.TimeoutError:
        total_dur = time.monotonic() - t0
        return ProviderTestResult(
            slug=slug,
            name=name,
            website=website,
            success=False,
            stage="timeout",
            duration_s=total_dur,
            error=f"Operation timed out after {timeout_s:.1f}s",
            mailbox_address=created_mb.address if created_mb else "",
        )
    except Exception as exc:
        total_dur = time.monotonic() - t0
        # Attempt best-effort cleanup on failure
        if created_mb:
            with contextlib.suppress(Exception):
                await provider.delete_mailbox(created_mb)
        return ProviderTestResult(
            slug=slug,
            name=name,
            website=website,
            success=False,
            stage="error",
            duration_s=total_dur,
            error=str(exc) or exc.__class__.__name__,
            mailbox_address=created_mb.address if created_mb else "",
        )


async def execute_email_delivery(
    provider: Any,
    client: HttpClient,
    poll_timeout_s: float = 30.0,
) -> tuple[bool, float, str]:
    """Test actual end-to-end email delivery using TestEmailSender."""
    t0 = time.monotonic()
    mailbox: MailboxInfo | None = None
    try:
        # Create dedicated mailbox
        mailbox = await provider.create_mailbox(MailboxSpec())

        # Dispatch real email via autonomous sender
        async with TestEmailSender(timeout=15.0) as sender:
            send_res = await sender.send(mailbox.address)
            if not send_res.success:
                return False, time.monotonic() - t0, f"Dispatcher failed: {send_res.detail}"

        # Poll for message arrival
        deadline = time.monotonic() + poll_timeout_s
        while time.monotonic() < deadline:
            await asyncio.sleep(2.0)
            msgs = await provider.list_messages(mailbox)
            if msgs:
                total_time = time.monotonic() - t0
                return True, total_time, ""

        return False, time.monotonic() - t0, f"Message not delivered within {poll_timeout_s:.0f}s"

    except Exception as exc:
        return False, time.monotonic() - t0, str(exc)
    finally:
        if mailbox:
            with contextlib.suppress(Exception):
                await provider.delete_mailbox(mailbox)


def load_health_state(state_file: Path) -> dict[str, Any]:
    """Load consecutive failure and issue tracking state."""
    if state_file.is_file():
        try:
            with open(state_file, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"providers": {}}


def save_health_state(state_file: Path, state: dict[str, Any]) -> None:
    """Save updated state atomically."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


def manage_github_issues(
    results: list[ProviderTestResult],
    state: dict[str, Any],
    run_url: str = "",
) -> None:
    """Create alert issues on 3 consecutive failures, and auto-close upon recovery."""
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY") or os.environ.get("REPO")

    if not gh_token or not repo:
        print("Note: GitHub issue management skipped (missing GH_TOKEN or GITHUB_REPOSITORY).")
        return

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    for r in results:
        p_state = state["providers"].setdefault(
            r.slug,
            {"consecutive_failures": 0, "issue_number": None, "last_status": "unknown"},
        )

        if r.fully_operational:
            # Check if this provider was previously in outage with an open issue
            issue_num = p_state.get("issue_number")
            if issue_num:
                print(f"Provider {r.slug} recovered! Auto-closing issue #{issue_num}...")
                deliv_info = (
                    f"🟢 Delivered in {r.delivery_duration_s:.1f}s"
                    if r.delivery_tested
                    else "Not tested"
                )
                close_comment = (
                    f"🎉 **Provider Outage Resolved**\n\n"
                    f"The health check suite verified that `{r.name}` (`{r.slug}`) has fully recovered.\n"
                    f"* **Verification Time:** `{now_iso}`\n"
                    f"* **Targets Available:** `{r.targets_count}`\n"
                    f"* **API Latency:** `{r.duration_s:.2f}s`\n"
                    f"* **E2E Email Delivery:** {deliv_info}\n\n"
                    f"Closing this issue automatically."
                )
                try:
                    subprocess.run(
                        ["gh", "issue", "comment", str(issue_num), "--body", close_comment],
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        ["gh", "issue", "close", str(issue_num), "--reason", "completed"],
                        check=True,
                        capture_output=True,
                    )
                    p_state["issue_number"] = None
                except Exception as exc:
                    print(
                        f"Warning: Failed to auto-close issue #{issue_num}: {exc}", file=sys.stderr
                    )

            p_state["consecutive_failures"] = 0
            p_state["last_status"] = "operational"

        else:
            p_state["consecutive_failures"] = p_state.get("consecutive_failures", 0) + 1
            failures = p_state["consecutive_failures"]
            outage_type = "Email Delivery" if r.effective_stage == "delivery" else "API Operations"
            p_state["last_status"] = f"{r.effective_stage}_outage" if failures >= 3 else "degraded"

            print(
                f"Provider {r.slug} failed at stage '{r.effective_stage}' ({failures} consecutive failure(s))."
            )

            # Circuit breaker: open an issue after exactly 3 consecutive failures
            if failures >= 3 and not p_state.get("issue_number"):
                print(f"Opening degradation issue for {r.slug} (3 consecutive failures)...")
                title = f"[Provider Outage] {r.name} ({r.slug}) {outage_type} failed 3 consecutive checks"
                body = (
                    f"<!-- automated-provider-outage-issue -->\n"
                    f"## 🚨 Automated Provider Degradation Alert: {r.name}\n\n"
                    f"### 📋 Outage Summary\n"
                    f"* **Provider:** `{r.name}` (`{r.slug}`)\n"
                    f"* **Website:** {r.website}\n"
                    f"* **Consecutive Failures:** `{failures}`\n"
                    f"* **Outage Type:** `{outage_type}`\n"
                    f"* **Detected At:** `{now_iso}`\n"
                    f"* **Action Run:** {run_url or 'Scheduled Health Run'}\n\n"
                    f"### ❌ Failure Diagnostic\n"
                    f"* **Failed Stage:** `{r.effective_stage}`\n"
                    f"* **Error Message:** `{r.effective_error}`\n"
                    f"* **API Health:** {'🟢 PASS' if r.success else f'🔴 FAIL ({r.stage})'}\n"
                    f"* **E2E Delivery:** {'🟢 PASS' if r.delivery_success else ('🔴 FAIL' if r.delivery_tested else '—')}\n"
                    f"* **Mailbox Tested:** `{r.mailbox_address or 'N/A'}`\n\n"
                    f"### 🛠️ Recommended Actions\n"
                    f"1. Check if upstream domain, MX records, or API signatures changed at [{r.name}]({r.website}).\n"
                    f"2. Inspect recent commits touching `src/mailtmapi/providers/{r.slug.replace('.', '_')}/`.\n"
                    f"3. Verify if provider IP ranges are blocking GitHub Actions runners or test mail dispatchers.\n\n"
                    f"---\n"
                    f"*This issue was automatically created by the Provider Health Suite and will automatically close once restored.*"
                )
                try:
                    cmd_create = [
                        "gh",
                        "issue",
                        "create",
                        "--title",
                        title,
                        "--body",
                        body,
                        "--label",
                        "bug",
                    ]
                    out = subprocess.check_output(cmd_create, text=True).strip()
                    # Extract issue number from returned issue URL
                    match = re.search(r"/issues/(\d+)", out)
                    if match:
                        p_state["issue_number"] = int(match.group(1))
                        print(f"Created issue #{p_state['issue_number']} for {r.slug}.")
                except Exception as exc:
                    print(f"Warning: Failed to create issue for {r.slug}: {exc}", file=sys.stderr)


def generate_status_markdown(
    results: list[ProviderTestResult],
    timestamp: str,
) -> str:
    """Generate Markdown status table for README.md and Step Summary."""
    all_ok = all(r.fully_operational for r in results)
    overall_badge = "🟢 **All Systems Operational**" if all_ok else "🟡 **Degraded Performance**"

    lines = [
        "<!-- provider-status:start -->",
        "### 🌐 Live Provider Operational Status\n",
        f"> **Last Verified:** `{timestamp}` | **Overall Health:** {overall_badge}\n",
        "| Provider | Slug | Targets | API Health | E2E Delivery | Latency | Status |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: |",
    ]

    for r in results:
        dur = f"{r.duration_s:.2f}s"
        targets = str(r.targets_count) if r.success else "—"

        if r.delivery_tested:
            deliv_str = f"🟢 `{r.delivery_duration_s:.1f}s`" if r.delivery_success else "🔴 Failed"
        else:
            deliv_str = "—"

        if r.fully_operational:
            status_icon = "🟢 Operational"
        elif not r.success:
            status_icon = "🔴 API Outage"
        else:
            status_icon = "🔴 Delivery Outage"

        api_icon = "🟢 PASS" if r.success else "🔴 FAIL"

        lines.append(
            f"| [{r.name}]({r.website}) | `{r.slug}` | {targets} | {api_icon} | {deliv_str} | `{dur}` | {status_icon} |"
        )

    lines.append("")
    lines.append("*Automated health checks run twice daily via GitHub Actions.*")
    lines.append("<!-- provider-status:end -->")
    return "\n".join(lines)


def update_readme(readme_path: Path, status_md: str) -> bool:
    """Update README.md between provider-status markers."""
    if not readme_path.is_file():
        return False
    content = readme_path.read_text(encoding="utf-8")
    pattern = r"<!-- provider-status:start -->.*?<!-- provider-status:end -->"
    if not re.search(pattern, content, flags=re.DOTALL):
        # Append before license or at the bottom
        new_content = content + "\n\n" + status_md + "\n"
    else:
        new_content = re.sub(pattern, status_md, content, flags=re.DOTALL)

    if new_content != content:
        readme_path.write_text(new_content, encoding="utf-8")
        print(f"Updated status table in {readme_path}")
        return True
    return False


def post_sticky_pr_comment(results: list[ProviderTestResult], timestamp: str) -> None:
    """Post or update sticky PR comment with provider health status."""
    pr_number = os.environ.get("PR_NUMBER") or os.environ.get("GITHUB_PR_NUMBER")
    repo = os.environ.get("REPO") or os.environ.get("GITHUB_REPOSITORY")
    gh_token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

    if not pr_number or not repo or not gh_token:
        print("Note: Sticky PR Provider Health comment skipped (missing PR_NUMBER or REPO).")
        return

    marker = "<!-- mailtmapi-pr-provider-health -->"
    all_ok = all(r.fully_operational for r in results)
    verdict = (
        "🟢 **PASS (All 7 Providers Verified)**"
        if all_ok
        else "⚠️ **NOTICE (Upstream Degradation Detected)**"
    )

    lines = [
        marker,
        "## 🌐 Live Upstream Provider Compatibility Gate\n",
        f"> **Verdict:** {verdict} | **Verified:** `{timestamp}`\n",
        "| Provider | Slug | Live API | E2E Delivery | Latency | Diagnostic |",
        "| :--- | :--- | :---: | :---: | :---: | :--- |",
    ]

    for r in results:
        api_icon = "🟢 OK" if r.success else "🔴 FAIL"
        dur = f"{r.duration_s:.2f}s"
        deliv = (
            f"🟢 `{r.delivery_duration_s:.1f}s`"
            if r.delivery_success
            else ("🔴 Fail" if r.delivery_tested else "—")
        )
        if r.fully_operational:
            diag = "None (Operational)"
        elif not r.success:
            diag = f"API `{r.stage}`: {r.error}"
        else:
            diag = f"Delivery: {r.delivery_error or 'Timed out or not received'}"

        lines.append(
            f"| [{r.name}]({r.website}) | `{r.slug}` | {api_icon} | {deliv} | `{dur}` | `{diag}` |"
        )

    lines.append("")
    if not all_ok:
        lines.append(
            "> ⚠️ **Note:** Upstream third-party degradation does not block PR merge, but please check if your changes affected this provider."
        )

    full_body = "\n".join(lines)

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
            print(f"Updating existing PR Provider Health comment (ID: {existing_id})...")
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
            print("Posting new PR Provider Health comment...")
            cmd_create = ["gh", "pr", "comment", str(pr_number), "--body", full_body]
            subprocess.run(cmd_create, check=True, stdout=subprocess.DEVNULL)
    except Exception as exc:
        print(f"Warning: Failed to update sticky PR comment: {exc}", file=sys.stderr)


async def async_main() -> int:
    parser = argparse.ArgumentParser(description="Test live mail providers and email delivery")
    parser.add_argument("--all", action="store_true", help="Test all 7 public providers")
    parser.add_argument(
        "--providers", type=str, default="", help="Comma-separated provider slugs to test"
    )
    parser.add_argument(
        "--with-delivery",
        dest="with_delivery",
        action="store_true",
        default=True,
        help="Test real email delivery e2e (default: True)",
    )
    parser.add_argument(
        "--no-delivery",
        dest="with_delivery",
        action="store_false",
        help="Skip e2e email delivery test",
    )
    parser.add_argument(
        "--update-readme", action="store_true", help="Update README.md status table"
    )
    parser.add_argument(
        "--manage-issues", action="store_true", help="Auto-create or close GitHub issues"
    )
    parser.add_argument("--sticky-pr", action="store_true", help="Post or update sticky PR comment")
    parser.add_argument(
        "--state-file", type=Path, default=ROOT_DIR / ".github" / "provider_health_state.json"
    )
    parser.add_argument(
        "--timeout", type=float, default=30.0, help="Per-provider timeout in seconds"
    )
    args = parser.parse_args()

    client = HttpClient()
    results: list[ProviderTestResult] = []

    # Filter target providers
    target_slugs = [s.strip() for s in args.providers.split(",") if s.strip()]

    print("=================================================================")
    print("      🚀 MailTM API Live Provider & E2E Delivery Suite")
    print("=================================================================")

    for slug, name, website, factory in PROVIDER_FACTORIES:
        if target_slugs and slug not in target_slugs:
            continue

        print(f"Testing provider: {name:<16} ({slug})...", end=" ", flush=True)
        provider = factory(client)
        res = await execute_provider_operations(provider, name, website, timeout_s=args.timeout)

        # Optional Email Delivery check on supported providers
        if args.with_delivery and res.success:
            print("testing delivery...", end=" ", flush=True)
            res.delivery_tested = True
            d_ok, d_dur, d_err = await execute_email_delivery(
                provider, client, poll_timeout_s=args.timeout
            )
            res.delivery_success = d_ok
            res.delivery_duration_s = d_dur
            res.delivery_error = d_err

        results.append(res)
        status_tag = "🟢 PASS" if res.success else f"🔴 FAIL ({res.stage})"
        deliv_tag = (
            f"| Delivery: {'🟢' if res.delivery_success else '🔴'}" if res.delivery_tested else ""
        )
        print(f"{status_tag} in {res.duration_s:.2f}s {deliv_tag}")
        if res.error:
            print(f"   └─ Error: {res.error}")
        if res.delivery_error:
            print(f"   └─ Delivery Error: {res.delivery_error}")

    await client.close()

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status_md = generate_status_markdown(results, now_iso)

    # Write to GITHUB_STEP_SUMMARY if available
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as sf:
            sf.write(status_md + "\n")

    # Update README
    if args.update_readme:
        update_readme(ROOT_DIR / "README.md", status_md)

    # Manage issues and state
    state = load_health_state(args.state_file)
    if args.manage_issues:
        run_id = os.environ.get("GITHUB_RUN_ID", "")
        repo = os.environ.get("GITHUB_REPOSITORY", "")
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if run_id and repo else ""
        manage_github_issues(results, state, run_url=run_url)
        save_health_state(args.state_file, state)

    # Post sticky PR comment if requested
    if args.sticky_pr:
        post_sticky_pr_comment(results, now_iso)

    print("\nSummary:")
    passed_count = sum(1 for r in results if r.success)
    print(f"Total: {len(results)} | Passed: {passed_count} | Failed: {len(results) - passed_count}")

    return 0


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(Exception):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ret = asyncio.run(async_main())
    sys.exit(ret)


if __name__ == "__main__":
    main()
