"""End-to-end demo mission orchestration."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bundle import SCHEMA_VERSION, compute_bundle_hash, write_bundle
from .canonical import CANONICALIZATION_PROFILE, HASH_ALGORITHM, sha256_digest
from .chain import EventChain
from .merkle import merkle_root_from_step_hashes
from .report import write_report
from .sandbox import LocalProcessSandbox
from .validator import VerificationResult, verify_bundle


class RunDirectoryExists(FileExistsError):
    pass


@dataclass(frozen=True)
class DemoRunResult:
    output_dir: Path
    bundle_path: Path
    report_path: Path
    mission_status: str
    verification: VerificationResult


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _artifact_manifest(output_dir: Path) -> list[dict[str, Any]]:
    artifact_dir = output_dir / "artifact"
    if not artifact_dir.exists():
        return []
    result: list[dict[str, Any]] = []
    for item in sorted(artifact_dir.rglob("*")):
        if item.is_symlink() or not item.is_file():
            continue
        result.append(
            {
                "path": item.relative_to(output_dir).as_posix(),
                "size": item.stat().st_size,
                "sha256": _hash_file(item),
            }
        )
    return result


def run_demo(output_dir: str | Path) -> DemoRunResult:
    destination = Path(output_dir)
    if destination.exists():
        raise RunDirectoryExists(f"run directory already exists: {destination}")
    destination.mkdir(parents=True, exist_ok=False)

    run_id = str(uuid.uuid4())
    started_at = _timestamp()
    sandbox = LocalProcessSandbox()
    chain = EventChain()
    run_details = {
        "run_id": run_id,
        "sandbox_backend": sandbox.backend_name,
        "security_level": sandbox.security_level,
        "network_policy": sandbox.network_policy,
    }
    chain.append(
        "runtime.mission_started",
        event_input={"task": "create-and-test-artifact"},
        event_output={"workspace": "created"},
        details=run_details,
    )

    sandbox_result = sandbox.run(destination / "artifact", run_id=run_id)
    for worker_event in sandbox_result.events:
        chain.append(
            worker_event["type"],
            event_input=worker_event["input"],
            event_output=worker_event["output"],
            details=worker_event["details"],
        )

    artifacts = _artifact_manifest(destination)
    for artifact in artifacts:
        chain.append(
            "runtime.artifact_collected",
            event_input={"path": artifact["path"]},
            event_output=artifact,
            details={"collector": "runtime", "method": "sha256"},
        )

    worker_self_test = any(
        event["type"] == "agent.test_completed"
        and event["output"].get("passed") is True
        for event in sandbox_result.events
    )
    expected_digests = {
        event["input"].get("path"): event["output"].get("sha256")
        for event in sandbox_result.events
        if event["type"] == "agent.file_written"
        and isinstance(event["input"], dict)
        and isinstance(event["output"], dict)
    }
    artifact_digest_matches = bool(artifacts) and all(
        expected_digests.get(artifact["path"]) == artifact["sha256"]
        for artifact in artifacts
    )
    checks = [
        {"name": "worker_exit_zero", "passed": sandbox_result.return_code == 0},
        {"name": "worker_protocol_valid", "passed": not sandbox_result.protocol_errors},
        {"name": "worker_self_test", "passed": worker_self_test},
        {"name": "artifact_present", "passed": bool(artifacts)},
        {"name": "artifact_digest_matches_worker", "passed": artifact_digest_matches},
    ]
    mission_status = "PASSED" if all(check["passed"] for check in checks) else "FAILED"
    validation = {
        "status": mission_status,
        "checks": checks,
        "stderr_hash": sha256_digest(sandbox_result.stderr.encode("utf-8")),
    }
    chain.append(
        "runtime.validation_completed",
        event_input={"check_count": len(checks)},
        event_output=validation,
        details={
            "protocol_errors": sandbox_result.protocol_errors,
            "worker_return_code": sandbox_result.return_code,
        },
    )

    events = chain.events
    finished_at = _timestamp()
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run": {
            "run_id": run_id,
            "started_at": started_at,
            "finished_at": finished_at,
            "duration_ms": sandbox_result.duration_ms,
            "sandbox_backend": sandbox.backend_name,
            "security_level": sandbox.security_level,
            "network_policy": sandbox.network_policy,
        },
        "events": events,
        "artifacts": artifacts,
        "validation": validation,
        "integrity": {
            "canonicalization": CANONICALIZATION_PROFILE,
            "hash_algorithm": HASH_ALGORITHM,
            "event_count": len(events),
            "event_merkle_root": merkle_root_from_step_hashes(
                [event["step_hash"] for event in events]
            ),
            "anchor_status": "UNANCHORED",
        },
    }
    bundle["integrity"]["bundle_hash"] = compute_bundle_hash(bundle)

    bundle_path = destination / "proof-bundle.json"
    write_bundle(bundle_path, bundle)
    verification = verify_bundle(bundle_path)
    report_path = destination / "report.html"
    write_report(report_path, bundle, verification)
    return DemoRunResult(
        output_dir=destination,
        bundle_path=bundle_path,
        report_path=report_path,
        mission_status=mission_status,
        verification=verification,
    )
