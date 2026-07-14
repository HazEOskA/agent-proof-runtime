"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from . import __version__
from .runtime import RunDirectoryExists, run_demo
from .validator import verify_bundle


def _default_output() -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runs") / f"{stamp}-{uuid.uuid4().hex[:8]}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="apr",
        description="Run an agent in a development sandbox and verify its execution receipt.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)

    demo = commands.add_parser("demo", help="run the built-in vertical-slice mission")
    demo.add_argument(
        "--output",
        type=Path,
        default=None,
        help="new output directory (default: timestamped directory under .runs)",
    )

    verify = commands.add_parser("verify", help="independently verify a Proof Bundle")
    verify.add_argument("bundle", type=Path)
    verify.add_argument("--json", action="store_true", help="print machine-readable result")

    commands.add_parser("explain", help="explain the v0.1 trust boundary in plain language")
    return parser


def _print_explanation() -> None:
    print(
        "\n".join(
            [
                "Agent Proof Runtime v0.1 has two separate jobs:",
                "1. Run one fixed demo agent in a fresh disposable workspace.",
                "2. Produce a receipt that another command can recalculate.",
                "",
                "LOCAL_VERIFIED means the receipt and artifact match.",
                "UNANCHORED means no independent server or HSM has vouched for it yet.",
                "development-only means this local backend must not run hostile code.",
            ]
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "explain":
        _print_explanation()
        return 0

    if arguments.command == "verify":
        result = verify_bundle(arguments.bundle)
        if arguments.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Proof:   {result.status}")
            print(f"Mission: {result.mission_status}")
            print(f"Anchor:  {result.anchor_status}")
            print(f"Events:  {result.event_count}")
            for error in result.errors:
                print(f"ERROR:   {error}")
        return 0 if result.valid else 1

    output = arguments.output or _default_output()
    try:
        result = run_demo(output)
    except RunDirectoryExists as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    except Exception as error:
        print(f"ERROR: demo run failed: {error}", file=sys.stderr)
        return 1

    print(f"Mission: {result.mission_status}")
    print(f"Proof:   {result.verification.status}")
    print(f"Anchor:  {result.verification.anchor_status}")
    print(f"Bundle:  {result.bundle_path}")
    print(f"Report:  {result.report_path}")
    print("Security: development-only local process backend")
    return 0 if result.mission_status == "PASSED" and result.verification.valid else 1
