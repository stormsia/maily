"""CLI runner for autonomous test email sender.

Usage examples:
    python -m test_mail_sender test@example.com
    python -m test_mail_sender send test@example.com --mode fallback
    python -m test_mail_sender send test@example.com --json
    python -m test_mail_sender probe test@example.com
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys

from .exceptions import EmailSenderError
from .sender import TestEmailSender, send_test_email


def configure_logging(verbose: bool, json_output: bool = False) -> None:
    if json_output and not verbose:
        level = logging.WARNING
    else:
        level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )


async def cmd_send(args: argparse.Namespace) -> int:
    try:
        res = await send_test_email(
            args.email,
            mode=args.mode,
            timeout=args.timeout,
            proxy=args.proxy,
            cf_clearance=args.cf_clearance,
        )
        if args.json:
            print(json.dumps(res.to_dict(), indent=2))
        else:
            fb = " (via fallback)" if res.fallback_used else ""
            print(f"SUCCESS: Email sent to {res.email} via {res.provider}{fb}")
            print(f"Detail: {res.detail}")
            print(f"Latency: {res.duration_ms:.1f}ms")
        return 0
    except EmailSenderError as exc:
        if args.json:
            print(
                json.dumps(
                    {
                        "email": args.email,
                        "success": False,
                        "error": str(exc),
                    },
                    indent=2,
                )
            )
        else:
            print(f"ERROR: Failed to send test email: {exc}", file=sys.stderr)
        return 1


async def cmd_probe(args: argparse.Namespace) -> int:
    """Probes both primary and fallback providers and prints health diagnostics."""
    print(f"Probing both test email providers with target: {args.email}...\n")
    async with TestEmailSender(
        timeout=args.timeout,
        proxy=args.proxy,
        cf_clearance=args.cf_clearance,
    ) as sender:
        # Test Primary
        print("[1/2] Probing Primary (WeSendTestMail)...")
        try:
            p_res = await sender.send(args.email, mode="primary")
            print(f"  OK: {p_res.detail} ({p_res.duration_ms:.1f}ms)")
            p_ok = True
        except Exception as exc:
            print(f"  FAIL: {exc}")
            p_ok = False

        # Test Fallback
        print("\n[2/2] Probing Fallback (XeraMail)...")
        try:
            f_res = await sender.send(args.email, mode="fallback")
            print(f"  OK: {f_res.detail} ({f_res.duration_ms:.1f}ms)")
            f_ok = True
        except Exception as exc:
            print(f"  FAIL: {exc}")
            f_ok = False

        print("\nProbe Summary:")
        print(f"  Primary (wesendtestmail.com): {'OPERATIONAL' if p_ok else 'DOWN/DEGRADED'}")
        print(f"  Fallback (xeramail.com):      {'OPERATIONAL' if f_ok else 'DOWN/DEGRADED'}")

        return 0 if (p_ok or f_ok) else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m test_mail_sender",
        description="Autonomous test email sender with primary & fallback providers for tests & CI.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose debug logging")
    parser.add_argument(
        "--timeout", type=float, default=20.0, help="HTTP timeout in seconds (default: 20)"
    )
    parser.add_argument("--proxy", type=str, default=None, help="HTTP/HTTPS/SOCKS proxy URL")
    parser.add_argument(
        "--cf-clearance", type=str, default=None, help="Optional Cloudflare cf_clearance cookie"
    )
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    subparsers = parser.add_subparsers(dest="command")

    # send sub-command (or default)
    send_parser = subparsers.add_parser("send", help="Send a test email to an inbox")
    send_parser.add_argument("email", help="Recipient email address")
    send_parser.add_argument(
        "--mode",
        choices=["auto", "primary", "fallback"],
        default="auto",
        help="Provider mode: auto (primary -> fallback), primary, or fallback",
    )
    send_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    send_parser.add_argument(
        "--timeout", type=float, default=20.0, help="HTTP timeout in seconds (default: 20)"
    )
    send_parser.add_argument("--proxy", type=str, default=None, help="HTTP/HTTPS/SOCKS proxy URL")
    send_parser.add_argument(
        "--cf-clearance", type=str, default=None, help="Optional Cloudflare cf_clearance cookie"
    )
    send_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # probe sub-command
    probe_parser = subparsers.add_parser("probe", help="Probe both services and test delivery")
    probe_parser.add_argument("email", help="Recipient email address to probe")
    probe_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose debug logging"
    )
    probe_parser.add_argument(
        "--timeout", type=float, default=20.0, help="HTTP timeout in seconds (default: 20)"
    )
    probe_parser.add_argument("--proxy", type=str, default=None, help="HTTP/HTTPS/SOCKS proxy URL")
    probe_parser.add_argument(
        "--cf-clearance", type=str, default=None, help="Optional Cloudflare cf_clearance cookie"
    )

    # If invoked directly with just an email, e.g. `python -m test_mail_sender user@example.com`
    # map it to `send`
    raw_args = sys.argv[1:]
    if (
        raw_args
        and not raw_args[0].startswith("-")
        and raw_args[0] not in ("send", "probe", "help", "-h", "--help")
    ):
        raw_args = ["send"] + raw_args

    parsed = parser.parse_args(raw_args)
    if not parsed.command:
        parser.print_help()
        return 2

    configure_logging(parsed.verbose, getattr(parsed, "json", False))

    if parsed.command == "send":
        return asyncio.run(cmd_send(parsed))
    if parsed.command == "probe":
        return asyncio.run(cmd_probe(parsed))

    return 0


if __name__ == "__main__":
    sys.exit(main())
