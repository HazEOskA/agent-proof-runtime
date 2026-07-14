"""Independent Proof Bundle validator.

This module does not call the runtime and does not trust its recorded verdict.
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .bundle import BundleFormatError, SCHEMA_VERSION, compute_bundle_hash, load_bundle
from .canonical import (
    CANONICALIZATION_PROFILE,
    HASH_ALGORITHM,
    CanonicalizationError,
    parse_sha256_digest,
    sha256_digest,
)
from .chain import verify_event_chain
from .merkle import merkle_root_from_step_hashes

TOP_LEVEL_KEYS = frozenset(
    {"schema_version", "run", "events", "artifacts", "validation", "integrity"}
)
RUN_KEYS = frozenset(
    {
        "run_id",
        "started_at",
        "finished_at",
        "duration_ms",
        "sandbox_backend",
        "security_level",
        "network_policy",
    }
)
VALIDATION_KEYS = frozenset({"status", "checks", "stderr_hash"})
INTEGRITY_KEYS = frozenset(
    {
        "canonicalization",
        "hash_algorithm",
        "event_count",
        "event_merkle_root",
        "anchor_status",
        "bundle_hash",
    }
)
ARTIFACT_KEYS = frozenset({"path", "size", "sha256"})
EXPECTED_EVENT_TYPES = (
    "runtime.mission_started",
    "agent.file_written",
    "agent.test_completed",
    "runtime.artifact_collected",
    "runtime.validation_completed",
)
EXPECTED_CHECK_NAMES = (
    "worker_exit_zero",
    "worker_protocol_valid",
    "worker_self_test",
    "artifact_present",
    "artifact_digest_matches_worker",
)


@dataclass(frozen=True)
class VerificationResult:
    status: str
    mission_status: str
    anchor_status: str
    errors: tuple[str, ...]
    event_count: int

    @property
    def valid(self) -> bool:
        return self.status == "LOCAL_VERIFIED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "mission_status": self.mission_status,
            "anchor_status": self.anchor_status,
            "event_count": self.event_count,
            "errors": list(self.errors),
        }


def _key_errors(label: str, value: Any, expected: frozenset[str]) -> list[str]:
    if not isinstance(value, dict):
        return [f"{label} must be an object"]
    errors: list[str] = []
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{label} is missing keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
    return errors


def _valid_rfc3339(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _parse_rfc3339(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _validate_artifacts(
    artifacts: Any, *, run_root: Path
) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(artifacts, list):
        return ["artifacts must be an array"], []

    errors: list[str] = []
    valid_manifests: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    root = run_root.resolve()

    for index, artifact in enumerate(artifacts):
        label = f"artifact[{index}]"
        key_errors = _key_errors(label, artifact, ARTIFACT_KEYS)
        errors.extend(key_errors)
        if key_errors:
            continue
        raw_path = artifact["path"]
        if not isinstance(raw_path, str) or not raw_path:
            errors.append(f"{label} path must be a non-empty string")
            continue
        path = PurePosixPath(raw_path)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in raw_path
            or path.as_posix() != raw_path
        ):
            errors.append(f"{label} path is not a canonical relative POSIX path")
            continue
        if raw_path in seen_paths:
            errors.append(f"{label} duplicates artifact path {raw_path}")
            continue
        seen_paths.add(raw_path)

        target = root.joinpath(*path.parts)
        try:
            resolved = target.resolve(strict=True)
        except (OSError, ValueError):
            errors.append(f"{label} file is missing: {raw_path}")
            continue
        if not resolved.is_relative_to(root):
            errors.append(f"{label} escapes the run directory")
            continue
        if target.is_symlink() or not target.is_file():
            errors.append(f"{label} is not a regular non-symlink file")
            continue
        if not isinstance(artifact["size"], int) or isinstance(artifact["size"], bool):
            errors.append(f"{label} size must be an integer")
            continue
        try:
            actual_size = target.stat().st_size
        except OSError as error:
            errors.append(f"{label} cannot be inspected: {error}")
            continue
        if artifact["size"] != actual_size:
            errors.append(f"{label} size mismatch")
        try:
            parse_sha256_digest(artifact["sha256"])
        except ValueError as error:
            errors.append(f"{label} has an invalid digest: {error}")
            continue
        try:
            if artifact["sha256"] != _hash_file(target):
                errors.append(f"{label} sha256 mismatch")
        except OSError as error:
            errors.append(f"{label} cannot be hashed: {error}")
            continue
        valid_manifests.append(artifact)
    return errors, valid_manifests


def _schema_errors(bundle: dict[str, Any]) -> list[str]:
    errors = _key_errors("bundle", bundle, TOP_LEVEL_KEYS)
    if bundle.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"unsupported schema_version; expected {SCHEMA_VERSION}")

    run = bundle.get("run")
    errors.extend(_key_errors("run", run, RUN_KEYS))
    if isinstance(run, dict):
        for field in ("run_id", "sandbox_backend", "security_level", "network_policy"):
            if not isinstance(run.get(field), str) or not run.get(field):
                errors.append(f"run.{field} must be a non-empty string")
        if not isinstance(run.get("duration_ms"), int) or isinstance(
            run.get("duration_ms"), bool
        ) or run.get("duration_ms", -1) < 0:
            errors.append("run.duration_ms must be a non-negative integer")
        for field in ("started_at", "finished_at"):
            if not _valid_rfc3339(run.get(field)):
                errors.append(f"run.{field} must be an RFC 3339 timestamp")
        if _valid_rfc3339(run.get("started_at")) and _valid_rfc3339(
            run.get("finished_at")
        ) and _parse_rfc3339(run["finished_at"]) < _parse_rfc3339(run["started_at"]):
            errors.append("run.finished_at cannot be before run.started_at")
        try:
            parsed_run_id = uuid.UUID(str(run.get("run_id")))
            if parsed_run_id.version != 4 or str(parsed_run_id) != run.get("run_id"):
                raise ValueError
        except ValueError:
            errors.append("run.run_id must be a canonical UUIDv4")
        expected_runtime = {
            "sandbox_backend": "local-process",
            "security_level": "development-only",
            "network_policy": "not-enforced",
        }
        for field, expected in expected_runtime.items():
            if run.get(field) != expected:
                errors.append(f"run.{field} must be {expected} for schema v0.1")

    validation = bundle.get("validation")
    errors.extend(_key_errors("validation", validation, VALIDATION_KEYS))
    if isinstance(validation, dict):
        if validation.get("status") not in {"PASSED", "FAILED"}:
            errors.append("validation.status must be PASSED or FAILED")
        checks = validation.get("checks")
        if not isinstance(checks, list) or not checks:
            errors.append("validation.checks must be a non-empty array")
        else:
            names: set[str] = set()
            for index, check in enumerate(checks):
                if not isinstance(check, dict) or set(check) != {"name", "passed"}:
                    errors.append(f"validation.checks[{index}] has an invalid shape")
                    continue
                valid_name = isinstance(check["name"], str) and bool(check["name"])
                if not valid_name:
                    errors.append(f"validation.checks[{index}] has an invalid name")
                if not isinstance(check["passed"], bool):
                    errors.append(f"validation.checks[{index}] passed must be boolean")
                if not valid_name:
                    continue
                if check["name"] in names:
                    errors.append(f"validation check name is duplicated: {check['name']}")
                names.add(check["name"])
        try:
            parse_sha256_digest(validation.get("stderr_hash"))
        except ValueError as error:
            errors.append(f"validation.stderr_hash is invalid: {error}")

    integrity = bundle.get("integrity")
    errors.extend(_key_errors("integrity", integrity, INTEGRITY_KEYS))
    if isinstance(integrity, dict):
        if integrity.get("canonicalization") != CANONICALIZATION_PROFILE:
            errors.append("integrity.canonicalization profile mismatch")
        if integrity.get("hash_algorithm") != HASH_ALGORITHM:
            errors.append("integrity.hash_algorithm must be sha256")
        if integrity.get("anchor_status") != "UNANCHORED":
            errors.append("v0.1 only permits anchor_status UNANCHORED")
        for field in ("event_merkle_root", "bundle_hash"):
            try:
                parse_sha256_digest(integrity.get(field))
            except ValueError as error:
                errors.append(f"integrity.{field} is invalid: {error}")
    return errors


def _demo_semantic_errors(
    *,
    events: Any,
    artifacts: list[dict[str, Any]],
    validation: Any,
) -> list[str]:
    """Re-derive the built-in v0.1 demo verdict instead of trusting it."""

    if not isinstance(events, list) or not all(isinstance(event, dict) for event in events):
        return []
    errors: list[str] = []
    event_types = tuple(event.get("type") for event in events)
    if event_types != EXPECTED_EVENT_TYPES:
        errors.append("v0.1 demo event sequence mismatch")
        return errors
    if not isinstance(validation, dict):
        return errors

    start, file_event, test_event, collected_event, final_event = events
    if start.get("input") != {"task": "create-and-test-artifact"}:
        errors.append("mission start task mismatch")
    if start.get("output") != {"workspace": "created"}:
        errors.append("mission start workspace result mismatch")

    final_details = final_event.get("details")
    if not isinstance(final_details, dict) or set(final_details) != {
        "protocol_errors",
        "worker_return_code",
    }:
        errors.append("final event details have an invalid shape")
        return errors
    protocol_errors = final_details["protocol_errors"]
    worker_return_code = final_details["worker_return_code"]
    if not isinstance(protocol_errors, list) or not all(
        isinstance(item, str) for item in protocol_errors
    ):
        errors.append("final event protocol_errors must be an array of strings")
        return errors
    if not isinstance(worker_return_code, int) or isinstance(worker_return_code, bool):
        errors.append("final event worker_return_code must be an integer")
        return errors

    expected_digest = None
    if isinstance(file_event.get("input"), dict) and isinstance(
        file_event.get("output"), dict
    ):
        written_path = file_event["input"].get("path")
        expected_digest = file_event["output"].get("sha256")
    else:
        written_path = None
    artifact_digest_matches = (
        len(artifacts) == 1
        and artifacts[0].get("path") == written_path
        and artifacts[0].get("sha256") == expected_digest
        and collected_event.get("output") == artifacts[0]
    )
    worker_self_test = (
        isinstance(test_event.get("output"), dict)
        and test_event["output"].get("passed") is True
    )
    expected_checks = {
        "worker_exit_zero": worker_return_code == 0,
        "worker_protocol_valid": not protocol_errors,
        "worker_self_test": worker_self_test,
        "artifact_present": bool(artifacts),
        "artifact_digest_matches_worker": artifact_digest_matches,
    }
    recorded_checks = validation.get("checks")
    if isinstance(recorded_checks, list) and all(
        isinstance(check, dict)
        and set(check) == {"name", "passed"}
        and isinstance(check["name"], str)
        and isinstance(check["passed"], bool)
        for check in recorded_checks
    ):
        recorded_names = tuple(check["name"] for check in recorded_checks)
        if recorded_names != EXPECTED_CHECK_NAMES:
            errors.append("validation check set or order mismatch")
        for check in recorded_checks:
            if expected_checks.get(check["name"]) != check["passed"]:
                errors.append(f"validation check was not independently reproduced: {check['name']}")

    expected_status = "PASSED" if all(expected_checks.values()) else "FAILED"
    if validation.get("status") != expected_status:
        errors.append("validation status does not match independently reproduced checks")
    return errors


def verify_bundle(path: str | Path) -> VerificationResult:
    bundle_path = Path(path)
    try:
        bundle = load_bundle(bundle_path)
    except BundleFormatError as error:
        return VerificationResult(
            status="FAILED",
            mission_status="UNKNOWN",
            anchor_status="UNKNOWN",
            errors=(str(error),),
            event_count=0,
        )

    errors = _schema_errors(bundle)
    events = bundle.get("events")
    event_count = len(events) if isinstance(events, list) else 0
    validation = bundle.get("validation")
    mission_status = (
        validation.get("status", "UNKNOWN") if isinstance(validation, dict) else "UNKNOWN"
    )
    integrity = bundle.get("integrity")
    anchor_status = (
        integrity.get("anchor_status", "UNKNOWN")
        if isinstance(integrity, dict)
        else "UNKNOWN"
    )

    try:
        expected_bundle_hash = compute_bundle_hash(bundle)
        if isinstance(integrity, dict) and integrity.get("bundle_hash") != expected_bundle_hash:
            errors.append("integrity.bundle_hash mismatch")
    except (
        BundleFormatError,
        CanonicalizationError,
        RecursionError,
        TypeError,
        ValueError,
    ) as error:
        errors.append(f"bundle cannot be canonicalized: {error}")

    errors.extend(verify_event_chain(events))

    if isinstance(events, list):
        step_hashes = [
            event.get("step_hash")
            for event in events
            if isinstance(event, dict) and isinstance(event.get("step_hash"), str)
        ]
        if len(step_hashes) != len(events):
            errors.append("cannot construct Merkle tree from malformed events")
        else:
            try:
                expected_root = merkle_root_from_step_hashes(step_hashes)
                if (
                    isinstance(integrity, dict)
                    and integrity.get("event_merkle_root") != expected_root
                ):
                    errors.append("integrity.event_merkle_root mismatch")
            except (RecursionError, ValueError) as error:
                errors.append(f"cannot construct Merkle tree: {error}")
        if isinstance(integrity, dict) and integrity.get("event_count") != len(events):
            errors.append("integrity.event_count mismatch")

    artifact_errors, valid_artifacts = _validate_artifacts(
        bundle.get("artifacts"), run_root=bundle_path.parent
    )
    errors.extend(artifact_errors)
    errors.extend(
        _demo_semantic_errors(
            events=events,
            artifacts=valid_artifacts,
            validation=validation,
        )
    )

    if isinstance(events, list) and events:
        run = bundle.get("run")
        first = events[0]
        if not isinstance(first, dict) or first.get("type") != "runtime.mission_started":
            errors.append("first event must be runtime.mission_started")
        elif isinstance(run, dict):
            expected_details = {
                "run_id": run.get("run_id"),
                "sandbox_backend": run.get("sandbox_backend"),
                "security_level": run.get("security_level"),
                "network_policy": run.get("network_policy"),
            }
            if first.get("details") != expected_details:
                errors.append("run metadata does not match the hashed start event")

        last = events[-1]
        if not isinstance(last, dict) or last.get("type") != "runtime.validation_completed":
            errors.append("last event must be runtime.validation_completed")
        elif last.get("output") != validation:
            errors.append("validation summary does not match the hashed final event")

        collected = [
            event.get("output")
            for event in events
            if isinstance(event, dict) and event.get("type") == "runtime.artifact_collected"
        ]
        if sorted(collected, key=lambda item: str(item.get("path")) if isinstance(item, dict) else "") != sorted(
            valid_artifacts, key=lambda item: item["path"]
        ):
            errors.append("artifact manifest does not match hashed collection events")

    return VerificationResult(
        status="FAILED" if errors else "LOCAL_VERIFIED",
        mission_status=mission_status,
        anchor_status=anchor_status,
        errors=tuple(errors),
        event_count=event_count,
    )
