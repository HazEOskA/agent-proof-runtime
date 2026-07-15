"""Command-line interface."""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Sequence

from . import __version__
from .gvisor import DockerGVisorSandbox
from .mission import MissionSpec, MissionValidationError
from .mission_loader import load_declared_mission
from .mission_v1 import BuildWeekMission
from .mission_control import MissionControlConfig, MissionControlError, serve
from .build_week_runtime import ArtifactPolicyError, run_build_week_mission
from .providers import ProviderError
from .runtime import RunDirectoryExists, run_demo, run_mission
from .validator import verify_bundle
from .tamper_lab import TAMPER_CASES, run_tamper_case


def _default_output(label: str = "run") -> Path:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    return Path(".runs") / f"{stamp}-{label}-{uuid.uuid4().hex[:8]}"


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

    run = commands.add_parser("run", help="execute a versioned declarative mission")
    run.add_argument("mission", type=Path, help="path to a mission JSON manifest")
    run.add_argument(
        "--output",
        type=Path,
        default=None,
        help="new output directory (default: timestamped directory under .runs)",
    )
    run.add_argument(
        "--provider",
        choices=["fixture", "openai"],
        default=None,
        help="override provider for apr.mission.v1",
    )

    mission = commands.add_parser("mission", help="inspect a MissionSpec")
    mission_commands = mission.add_subparsers(dest="mission_command", required=True)
    validate = mission_commands.add_parser("validate", help="strictly validate a mission")
    validate.add_argument("mission", type=Path)
    validate.add_argument("--json", action="store_true")

    doctor = commands.add_parser("doctor", help="check sandbox backend availability")
    doctor.add_argument("--backend", choices=["gvisor"], default="gvisor")
    doctor.add_argument("--json", action="store_true")

    tamper = commands.add_parser(
        "tamper-lab", help="verify a disposable tampered copy of a run"
    )
    tamper.add_argument("bundle", type=Path, help="original proof-bundle.json")
    tamper.add_argument("--case", choices=TAMPER_CASES, required=True)
    tamper.add_argument("--json", action="store_true")

    control = commands.add_parser(
        "mission-control", help="start the local operator dashboard"
    )
    control.add_argument("--host", default="127.0.0.1")
    try:
        default_port = int(os.environ.get("PORT", "8080"))
    except ValueError:
        default_port = 8080
    control.add_argument("--port", type=int, default=default_port)
    control.add_argument("--missions-dir", type=Path, default=Path("missions"))
    control.add_argument("--runs-dir", type=Path, default=Path(".runs"))
    control.add_argument(
        "--allow-remote",
        action="store_true",
        help="explicitly allow binding outside loopback (no authentication is provided)",
    )

    commands.add_parser("explain", help="explain the trust boundary in plain language")
    return parser


def _print_explanation() -> None:
    print(
        "\n".join(
            [
                "Agent Proof Runtime has two separate jobs:",
                "1. Run an approved mission in a fresh disposable workspace.",
                "2. Produce a receipt that another command can recalculate.",
                "",
                "LOCAL_VERIFIED means the receipt and artifact match.",
                "UNANCHORED means no independent server or HSM has vouched for it yet.",
                "development-only means this local backend must not run hostile code.",
                "The gvisor backend fails closed unless Docker reports runtime=runsc.",
            ]
        )
    )


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    if arguments.command == "explain":
        _print_explanation()
        return 0

    if arguments.command == "mission-control":
        try:
            serve(
                MissionControlConfig(
                    missions_dir=arguments.missions_dir,
                    runs_dir=arguments.runs_dir,
                    host=arguments.host,
                    port=arguments.port,
                    allow_remote=arguments.allow_remote,
                )
            )
        except (MissionControlError, OSError) as error:
            print(f"ERROR: mission control failed: {error}", file=sys.stderr)
            return 2
        return 0

    if arguments.command == "doctor":
        result = DockerGVisorSandbox().doctor()
        if arguments.json:
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Backend:   {result.backend}")
            print(f"Available: {'YES' if result.available else 'NO'}")
            for check in result.checks:
                status = "PASS" if check["passed"] else "FAIL"
                print(f"{status:4} {check['name']}: {check['detail']}")
        return 0 if result.available else 1

    if arguments.command == "tamper-lab":
        try:
            result = run_tamper_case(arguments.bundle.parent, arguments.case)
        except (OSError, ValueError, RuntimeError) as error:
            print(f"ERROR: Tamper Lab failed: {error}", file=sys.stderr)
            return 2
        if arguments.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"Case:     {result['case']}")
            print(f"Copy:     {result['status']}")
            print(f"Original: {result['original_status']}")
            print(f"Preserved: {'YES' if result['original_preserved'] else 'NO'}")
            for error in result["errors"]:
                print(f"DETECTED: {error}")
        return 0

    if arguments.command == "mission":
        try:
            spec = load_declared_mission(arguments.mission)
        except MissionValidationError as error:
            if arguments.json:
                print(
                    json.dumps(
                        {"valid": False, "errors": list(error.errors)},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
            else:
                print("Mission: INVALID")
                for item in error.errors:
                    print(f"ERROR:   {item}")
            return 1
        result = {
            "valid": True,
            "mission_id": spec.mission_id,
            "schema_version": (
                "apr.mission.v1" if isinstance(spec, BuildWeekMission) else "apr.mission.v0.2"
            ),
            "provider": spec.provider if isinstance(spec, BuildWeekMission) else None,
            "backend": spec.backend if isinstance(spec, MissionSpec) else "controlled-artifact-runtime",
            "workload": spec.workload.kind if isinstance(spec, MissionSpec) else "artifact-proposal",
            "spec_hash": spec.spec_hash if isinstance(spec, MissionSpec) else spec.manifest_hash,
        }
        if arguments.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("Mission: VALID")
            print(f"ID:      {spec.mission_id}")
            print(f"Backend: {result['backend']}")
            print(f"Workload: {result['workload']}")
            if result["provider"]:
                print(f"Provider: {result['provider']}")
            print(f"Hash:    {result['spec_hash']}")
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

    if arguments.command == "run":
        try:
            spec = load_declared_mission(arguments.mission)
            output = arguments.output or _default_output(spec.mission_id)
            if isinstance(spec, BuildWeekMission):
                result = run_build_week_mission(
                    spec, output, provider_name=arguments.provider
                )
            else:
                if arguments.provider is not None:
                    raise MissionValidationError(
                        ["--provider is only valid for apr.mission.v1"]
                    )
                result = run_mission(spec, output)
        except MissionValidationError as error:
            for item in error.errors:
                print(f"ERROR: {item}", file=sys.stderr)
            return 2
        except RunDirectoryExists as error:
            print(f"ERROR: {error}", file=sys.stderr)
            return 2
        except ProviderError as error:
            print(f"ERROR: provider failed: {error}", file=sys.stderr)
            return 3
        except ArtifactPolicyError as error:
            print(f"ERROR: artifact policy rejected proposal: {error}", file=sys.stderr)
            return 3
        except Exception as error:
            print(f"ERROR: mission run failed: {error}", file=sys.stderr)
            return 1
        print(f"Mission: {result.mission_status}")
        print(f"Proof:   {result.verification.status}")
        print(f"Anchor:  {result.verification.anchor_status}")
        print(f"Bundle:  {result.bundle_path}")
        print(f"Report:  {result.report_path}")
        return 0 if result.mission_status == "PASSED" and result.verification.valid else 4

    output = arguments.output or _default_output("demo")
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
