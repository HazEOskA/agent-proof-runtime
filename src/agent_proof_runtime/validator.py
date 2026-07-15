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

from .bundle import (
    BundleFormatError,
    SCHEMA_VERSION,
    SCHEMA_VERSION_BUILD_WEEK,
    SCHEMA_VERSION_V2,
    compute_bundle_hash,
    load_bundle,
)
from .canonical import (
    CANONICALIZATION_PROFILE,
    HASH_ALGORITHM,
    CanonicalizationError,
    hash_json,
    parse_sha256_digest,
)
from .chain import verify_event_chain
from .merkle import merkle_root_from_step_hashes
from .mission import MissionSpec, MissionValidationError, parse_mission
from .mission_v1 import BuildWeekMission, parse_build_week_mission
from .acceptance import evaluate_acceptance

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
TOP_LEVEL_KEYS_V2 = frozenset(
    {
        "schema_version",
        "mission",
        "run",
        "events",
        "artifacts",
        "validation",
        "integrity",
    }
)
MISSION_BUNDLE_KEYS = frozenset({"spec", "spec_hash"})
EXPECTED_CHECK_NAMES_V2 = (
    "backend_exit_zero",
    "backend_protocol_valid",
    "artifact_requirement_met",
)
TOP_LEVEL_KEYS_BUILD_WEEK = frozenset(
    {
        "schema_version",
        "mission",
        "provider",
        "run",
        "events",
        "artifacts",
        "acceptance",
        "verification",
        "integrity",
    }
)
MISSION_KEYS_BUILD_WEEK = frozenset({"manifest", "manifest_hash"})
PROVIDER_KEYS_BUILD_WEEK = frozenset(
    {
        "provider",
        "requested_model",
        "resolved_model",
        "response_id",
        "token_usage",
        "latency_ms",
        "input_hash",
        "response_hash",
        "implementation_status",
    }
)
TOKEN_USAGE_KEYS = frozenset({"input_tokens", "output_tokens", "total_tokens"})
ARTIFACT_KEYS_BUILD_WEEK = frozenset({"path", "media_type", "size", "sha256"})
ACCEPTANCE_KEYS = frozenset({"status", "checks"})
ACCEPTANCE_CHECK_KEYS = frozenset({"id", "type", "passed", "expected", "actual"})
VERIFICATION_KEYS_BUILD_WEEK = frozenset({"claimed_status"})


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


def _v02_shape_errors(
    bundle: dict[str, Any],
) -> tuple[list[str], MissionSpec | None]:
    errors = _key_errors("bundle", bundle, TOP_LEVEL_KEYS_V2)
    if bundle.get("schema_version") != SCHEMA_VERSION_V2:
        errors.append(f"unsupported schema_version; expected {SCHEMA_VERSION_V2}")

    mission_value = bundle.get("mission")
    errors.extend(_key_errors("mission", mission_value, MISSION_BUNDLE_KEYS))
    spec: MissionSpec | None = None
    if isinstance(mission_value, dict):
        try:
            spec = parse_mission(mission_value.get("spec"), check_source=False)
        except MissionValidationError as error:
            errors.extend(f"mission.spec: {item}" for item in error.errors)
        try:
            parse_sha256_digest(mission_value.get("spec_hash"))
        except ValueError as error:
            errors.append(f"mission.spec_hash is invalid: {error}")
        if spec and mission_value.get("spec_hash") != spec.spec_hash:
            errors.append("mission.spec_hash mismatch")

    run = bundle.get("run")
    errors.extend(_key_errors("run", run, RUN_KEYS))
    if isinstance(run, dict):
        for field in ("run_id", "sandbox_backend", "security_level", "network_policy"):
            if not isinstance(run.get(field), str) or not run.get(field):
                errors.append(f"run.{field} must be a non-empty string")
        duration = run.get("duration_ms")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
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

        if spec:
            expected_runtime = (
                {
                    "sandbox_backend": "local-process",
                    "security_level": "development-only",
                    "network_policy": "not-enforced",
                }
                if spec.backend == "local-demo"
                else {
                    "sandbox_backend": "docker-gvisor",
                    "security_level": "sandboxed",
                    "network_policy": "blocked",
                }
            )
            for field, expected in expected_runtime.items():
                if run.get(field) != expected:
                    errors.append(
                        f"run.{field} does not match mission backend {spec.backend}"
                    )

    validation = bundle.get("validation")
    errors.extend(_key_errors("validation", validation, VALIDATION_KEYS))
    if isinstance(validation, dict):
        if validation.get("status") not in {"PASSED", "FAILED"}:
            errors.append("validation.status must be PASSED or FAILED")
        checks = validation.get("checks")
        if not isinstance(checks, list):
            errors.append("validation.checks must be an array")
        else:
            names: list[str] = []
            for index, check in enumerate(checks):
                if not isinstance(check, dict) or set(check) != {"name", "passed"}:
                    errors.append(f"validation.checks[{index}] has an invalid shape")
                    continue
                if not isinstance(check["name"], str) or not check["name"]:
                    errors.append(f"validation.checks[{index}] has an invalid name")
                    continue
                if not isinstance(check["passed"], bool):
                    errors.append(f"validation.checks[{index}] passed must be boolean")
                names.append(check["name"])
            if tuple(names) != EXPECTED_CHECK_NAMES_V2:
                errors.append("validation check set or order mismatch")
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
            errors.append("v0.2 only permits anchor_status UNANCHORED")
        for field in ("event_merkle_root", "bundle_hash"):
            try:
                parse_sha256_digest(integrity.get(field))
            except ValueError as error:
                errors.append(f"integrity.{field} is invalid: {error}")
    return errors, spec


def _verify_v02_loaded(
    bundle: dict[str, Any], *, bundle_path: Path
) -> VerificationResult:
    errors, spec = _v02_shape_errors(bundle)
    events = bundle.get("events")
    event_count = len(events) if isinstance(events, list) else 0
    if not isinstance(events, list):
        errors.append("events must be an array")
    elif len(events) < 3:
        errors.append("v0.2 proof must contain start, backend, and validation events")
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
    if spec:
        total_artifact_bytes = sum(
            artifact.get("size", 0)
            for artifact in valid_artifacts
            if isinstance(artifact.get("size"), int)
        )
        if len(valid_artifacts) > spec.artifacts.max_files:
            errors.append("artifact manifest exceeds mission max_files")
        if total_artifact_bytes > spec.artifacts.max_bytes:
            errors.append("artifact manifest exceeds mission max_bytes")
        if spec.artifacts.required and not valid_artifacts:
            errors.append("mission requires at least one valid artifact")

    if isinstance(events, list) and events:
        run = bundle.get("run")
        mission_value = bundle.get("mission")
        first = events[0]
        if not isinstance(first, dict) or first.get("type") != "runtime.mission_started":
            errors.append("first event must be runtime.mission_started")
        elif isinstance(run, dict) and isinstance(mission_value, dict) and spec:
            expected_details = {
                "run_id": run.get("run_id"),
                "sandbox_backend": run.get("sandbox_backend"),
                "security_level": run.get("security_level"),
                "network_policy": run.get("network_policy"),
            }
            if first.get("details") != expected_details:
                errors.append("run metadata does not match the hashed start event")
            if first.get("input") != {
                "mission_id": spec.mission_id,
                "mission_spec_hash": mission_value.get("spec_hash"),
            }:
                errors.append("mission metadata does not match the hashed start event")
            if first.get("output") != {"workspace": "created"}:
                errors.append("mission start workspace result mismatch")

        last = events[-1]
        if not isinstance(last, dict) or last.get("type") != "runtime.validation_completed":
            errors.append("last event must be runtime.validation_completed")
        elif last.get("output") != validation:
            errors.append("validation summary does not match the hashed final event")

        collected_events = [
            (index, event.get("output"))
            for index, event in enumerate(events)
            if isinstance(event, dict) and event.get("type") == "runtime.artifact_collected"
        ]
        collected = [item for _, item in collected_events]
        if sorted(
            collected,
            key=lambda item: str(item.get("path")) if isinstance(item, dict) else "",
        ) != sorted(valid_artifacts, key=lambda item: item["path"]):
            errors.append("artifact manifest does not match hashed collection events")
        expected_collection_indices = list(
            range(len(events) - 1 - len(collected_events), len(events) - 1)
        )
        if [index for index, _ in collected_events] != expected_collection_indices:
            errors.append("artifact collection events must immediately precede validation")

        final_details = last.get("details") if isinstance(last, dict) else None
        if not isinstance(final_details, dict) or set(final_details) != {
            "artifact_required",
            "backend_return_code",
            "protocol_errors",
        }:
            errors.append("final event details have an invalid shape")
        elif spec and isinstance(validation, dict):
            return_code = final_details["backend_return_code"]
            protocol_errors = final_details["protocol_errors"]
            artifact_required = final_details["artifact_required"]
            valid_final_details = True
            if not isinstance(return_code, int) or isinstance(return_code, bool):
                errors.append("backend_return_code must be an integer")
                valid_final_details = False
            if not isinstance(protocol_errors, list) or not all(
                isinstance(item, str) for item in protocol_errors
            ):
                errors.append("protocol_errors must be an array of strings")
                valid_final_details = False
            if not isinstance(artifact_required, bool):
                errors.append("artifact_required must be boolean")
                valid_final_details = False
            elif artifact_required != spec.artifacts.required:
                errors.append("artifact_required does not match MissionSpec")

            if valid_final_details:
                expected_checks = {
                    "backend_exit_zero": return_code == 0,
                    "backend_protocol_valid": not protocol_errors,
                    "artifact_requirement_met": bool(valid_artifacts)
                    or not artifact_required,
                }
                checks = validation.get("checks")
                if isinstance(checks, list):
                    for check in checks:
                        if (
                            isinstance(check, dict)
                            and isinstance(check.get("name"), str)
                            and isinstance(check.get("passed"), bool)
                            and expected_checks.get(check["name"]) != check["passed"]
                        ):
                            errors.append(
                                "validation check was not independently reproduced: "
                                + check["name"]
                            )
                expected_status = (
                    "PASSED" if all(expected_checks.values()) else "FAILED"
                )
                if validation.get("status") != expected_status:
                    errors.append(
                        "validation status does not match independently reproduced checks"
                    )
                if last.get("input") != {"check_count": len(EXPECTED_CHECK_NAMES_V2)}:
                    errors.append("final event check_count mismatch")

                backend_end = len(events) - 1 - len(collected_events)
                backend_events = events[1:backend_end]
                if spec.backend == "local-demo":
                    if tuple(event.get("type") for event in backend_events) != (
                        "agent.file_written",
                        "agent.test_completed",
                    ):
                        errors.append("local-demo backend event sequence mismatch")
                    elif return_code == 0 and backend_events[1].get("output") != {
                        "passed": True
                    }:
                        errors.append("local-demo test result contradicts backend exit code")
                elif spec.backend == "gvisor":
                    if len(backend_events) != 1 or backend_events[0].get("type") != (
                        "sandbox.container_completed"
                    ):
                        errors.append("gvisor backend event sequence mismatch")
                    else:
                        container_event = backend_events[0]
                        expected_input = {
                            "mission_id": spec.mission_id,
                            "image": spec.workload.image,
                            "command_hash": hash_json(list(spec.workload.command)),
                        }
                        if container_event.get("input") != expected_input:
                            errors.append("gvisor container input mismatch")
                        if container_event.get("details") != {
                            "backend": "docker-gvisor",
                            "runtime": "runsc",
                            "network_policy": "blocked",
                        }:
                            errors.append("gvisor container details mismatch")
                        output = container_event.get("output")
                        if not isinstance(output, dict) or set(output) != {
                            "exit_code",
                            "timed_out",
                            "stdout_hash",
                            "stderr_hash",
                        }:
                            errors.append("gvisor container output has an invalid shape")
                        else:
                            if output.get("exit_code") != return_code:
                                errors.append("gvisor exit code mismatch")
                            if not isinstance(output.get("timed_out"), bool):
                                errors.append("gvisor timed_out must be boolean")
                            elif output["timed_out"] and return_code != 124:
                                errors.append("timed out gvisor run must use exit code 124")
                            for field in ("stdout_hash", "stderr_hash"):
                                try:
                                    parse_sha256_digest(output.get(field))
                                except ValueError as error:
                                    errors.append(f"gvisor {field} is invalid: {error}")
                            if output.get("stderr_hash") != validation.get("stderr_hash"):
                                errors.append("gvisor stderr hash mismatch")

    return VerificationResult(
        status="FAILED" if errors else "LOCAL_VERIFIED",
        mission_status=mission_status,
        anchor_status=anchor_status,
        errors=tuple(errors),
        event_count=event_count,
    )


def _validate_build_week_artifacts(
    artifacts: Any, *, run_root: Path, mission: BuildWeekMission | None
) -> tuple[list[str], list[dict[str, Any]]]:
    if not isinstance(artifacts, list):
        return ["artifacts must be an array"], []
    errors: list[str] = []
    valid: list[dict[str, Any]] = []
    seen: set[str] = set()
    root = run_root.resolve()
    declared = (
        {"artifact/" + item.path: item for item in mission.artifact_contract.artifacts}
        if mission
        else {}
    )
    for index, artifact in enumerate(artifacts):
        label = f"artifact[{index}]"
        shape_errors = _key_errors(label, artifact, ARTIFACT_KEYS_BUILD_WEEK)
        errors.extend(shape_errors)
        if shape_errors:
            continue
        raw_path = artifact["path"]
        path = PurePosixPath(raw_path) if isinstance(raw_path, str) else PurePosixPath("")
        if (
            not isinstance(raw_path, str)
            or not raw_path.startswith("artifact/")
            or path.is_absolute()
            or ".." in path.parts
            or "\\" in raw_path
            or path.as_posix() != raw_path
        ):
            errors.append(f"{label} path is not a canonical artifact path")
            continue
        if raw_path in seen:
            errors.append(f"{label} duplicates artifact path {raw_path}")
            continue
        seen.add(raw_path)
        contract = declared.get(raw_path)
        if mission and contract is None:
            errors.append(f"{label} path is outside the artifact contract")
        if contract and artifact["media_type"] != contract.media_type:
            errors.append(f"{label} media_type does not match the artifact contract")
        if not isinstance(artifact["media_type"], str):
            errors.append(f"{label} media_type must be a string")
        target = root.joinpath(*path.parts)
        try:
            resolved = target.resolve(strict=True)
        except (OSError, ValueError):
            errors.append(f"{label} file is missing: {raw_path}")
            continue
        if not resolved.is_relative_to(root) or target.is_symlink() or not target.is_file():
            errors.append(f"{label} is not a regular in-run file")
            continue
        size = artifact["size"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0:
            errors.append(f"{label} size must be a non-negative integer")
            continue
        try:
            if target.stat().st_size != size:
                errors.append(f"{label} size mismatch")
        except OSError as error:
            errors.append(f"{label} cannot be inspected: {error}")
            continue
        if contract and size > contract.max_bytes:
            errors.append(f"{label} exceeds contract max_bytes")
        try:
            parse_sha256_digest(artifact["sha256"])
        except ValueError as error:
            errors.append(f"{label} has an invalid digest: {error}")
            continue
        try:
            if _hash_file(target) != artifact["sha256"]:
                errors.append(f"{label} sha256 mismatch")
        except OSError as error:
            errors.append(f"{label} cannot be hashed: {error}")
            continue
        valid.append(artifact)

    artifact_root = run_root / "artifact"
    actual_paths: set[str] = set()
    if artifact_root.is_symlink() or not artifact_root.is_dir():
        errors.append("artifact directory is missing or is a symbolic link")
    else:
        for candidate in artifact_root.rglob("*"):
            relative = candidate.relative_to(run_root).as_posix()
            if candidate.is_symlink():
                errors.append(f"artifact tree contains symbolic link: {relative}")
            elif candidate.is_file():
                actual_paths.add(relative)
        if actual_paths != seen:
            errors.append("artifact manifest does not exactly match materialized files")
    if mission:
        required = {"artifact/" + item.path for item in mission.artifact_contract.artifacts if item.required}
        missing = sorted(required - seen)
        if missing:
            errors.append("required artifacts are missing: " + ", ".join(missing))
        if len(valid) > mission.artifact_contract.max_files:
            errors.append("artifacts exceed contract max_files")
        if sum(item.get("size", 0) for item in valid) > mission.artifact_contract.max_total_bytes:
            errors.append("artifacts exceed contract max_total_bytes")
    return errors, valid


def _verify_build_week_loaded(
    bundle: dict[str, Any], *, bundle_path: Path
) -> VerificationResult:
    errors = _key_errors("bundle", bundle, TOP_LEVEL_KEYS_BUILD_WEEK)
    if bundle.get("schema_version") != SCHEMA_VERSION_BUILD_WEEK:
        errors.append(f"unsupported schema_version; expected {SCHEMA_VERSION_BUILD_WEEK}")

    mission_value = bundle.get("mission")
    errors.extend(_key_errors("mission", mission_value, MISSION_KEYS_BUILD_WEEK))
    mission: BuildWeekMission | None = None
    if isinstance(mission_value, dict):
        try:
            mission = parse_build_week_mission(mission_value.get("manifest"))
        except MissionValidationError as error:
            errors.extend(f"mission.manifest: {item}" for item in error.errors)
        try:
            parse_sha256_digest(mission_value.get("manifest_hash"))
        except ValueError as error:
            errors.append(f"mission.manifest_hash is invalid: {error}")
        if mission and mission_value.get("manifest_hash") != mission.manifest_hash:
            errors.append("mission.manifest_hash mismatch")

    provider = bundle.get("provider")
    errors.extend(_key_errors("provider", provider, PROVIDER_KEYS_BUILD_WEEK))
    if isinstance(provider, dict):
        provider_name = provider.get("provider")
        if provider_name not in {"fixture", "openai"}:
            errors.append("provider.provider must be fixture or openai")
        if mission and provider_name != mission.provider and not (
            provider_name in {"fixture", "openai"}
        ):
            errors.append("provider selection is invalid")
        for field in ("requested_model", "resolved_model", "implementation_status"):
            if not isinstance(provider.get(field), str) or not provider.get(field):
                errors.append(f"provider.{field} must be a non-empty string")
        response_id = provider.get("response_id")
        if response_id is not None and (not isinstance(response_id, str) or not response_id):
            errors.append("provider.response_id must be null or a non-empty string")
        usage = provider.get("token_usage")
        errors.extend(_key_errors("provider.token_usage", usage, TOKEN_USAGE_KEYS))
        if isinstance(usage, dict):
            for field in TOKEN_USAGE_KEYS:
                value = usage.get(field)
                if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                    errors.append(f"provider.token_usage.{field} must be a non-negative integer")
        latency = provider.get("latency_ms")
        if not isinstance(latency, int) or isinstance(latency, bool) or latency < 0:
            errors.append("provider.latency_ms must be a non-negative integer")
        for field in ("input_hash", "response_hash"):
            try:
                parse_sha256_digest(provider.get(field))
            except ValueError as error:
                errors.append(f"provider.{field} is invalid: {error}")
        if mission:
            if provider.get("input_hash") != hash_json(mission.provider_input()):
                errors.append("provider.input_hash mismatch")
            if provider_name == "fixture":
                if provider.get("resolved_model") != "fixture-v1":
                    errors.append("fixture resolved_model must be fixture-v1")
                if provider.get("response_id") is not None:
                    errors.append("fixture response_id must be null")
                if provider.get("implementation_status") != "DETERMINISTIC_FIXTURE":
                    errors.append("fixture implementation_status mismatch")
            elif provider_name == "openai" and provider.get("implementation_status") not in {
                "IMPLEMENTED BUT NOT LIVE-VALIDATED",
                "LIVE_API_REQUEST_EXECUTED",
            }:
                errors.append("OpenAI implementation_status mismatch")

    run = bundle.get("run")
    errors.extend(_key_errors("run", run, RUN_KEYS))
    if isinstance(run, dict):
        for field in ("run_id", "sandbox_backend", "security_level", "network_policy"):
            if not isinstance(run.get(field), str) or not run.get(field):
                errors.append(f"run.{field} must be a non-empty string")
        try:
            parsed = uuid.UUID(str(run.get("run_id")))
            if parsed.version != 4 or str(parsed) != run.get("run_id"):
                raise ValueError
        except ValueError:
            errors.append("run.run_id must be a canonical UUIDv4")
        for field in ("started_at", "finished_at"):
            if not _valid_rfc3339(run.get(field)):
                errors.append(f"run.{field} must be an RFC 3339 timestamp")
        duration = run.get("duration_ms")
        if not isinstance(duration, int) or isinstance(duration, bool) or duration < 0:
            errors.append("run.duration_ms must be a non-negative integer")
        if run.get("sandbox_backend") != "controlled-artifact-runtime":
            errors.append("run.sandbox_backend must be controlled-artifact-runtime")
        if run.get("security_level") != "development-only":
            errors.append("run.security_level must be development-only")
        if isinstance(provider, dict):
            expected_network = (
                "fixture-offline" if provider.get("provider") == "fixture" else "provider-api-only"
            )
            if run.get("network_policy") != expected_network:
                errors.append("run.network_policy does not match provider")

    artifact_errors, valid_artifacts = _validate_build_week_artifacts(
        bundle.get("artifacts"), run_root=bundle_path.parent, mission=mission
    )
    errors.extend(artifact_errors)
    if isinstance(provider, dict):
        try:
            reconstructed = {
                "artifacts": [
                    {
                        "path": item["path"].removeprefix("artifact/"),
                        "media_type": item["media_type"],
                        "content": (bundle_path.parent / item["path"]).read_text(encoding="utf-8"),
                    }
                    for item in sorted(valid_artifacts, key=lambda value: value["path"])
                ]
            }
            if provider.get("response_hash") != hash_json(reconstructed):
                errors.append("provider.response_hash does not match materialized artifacts")
        except (OSError, UnicodeError, CanonicalizationError) as error:
            errors.append(f"provider response evidence cannot be reconstructed: {error}")

    acceptance = bundle.get("acceptance")
    errors.extend(_key_errors("acceptance", acceptance, ACCEPTANCE_KEYS))
    mission_status = "UNKNOWN"
    recorded_checks: Any = None
    if isinstance(acceptance, dict):
        mission_status = acceptance.get("status", "UNKNOWN")
        if mission_status not in {"PASSED", "FAILED"}:
            errors.append("acceptance.status must be PASSED or FAILED")
        recorded_checks = acceptance.get("checks")
        if not isinstance(recorded_checks, list):
            errors.append("acceptance.checks must be an array")
        else:
            for index, check in enumerate(recorded_checks):
                errors.extend(_key_errors(f"acceptance.checks[{index}]", check, ACCEPTANCE_CHECK_KEYS))
    if mission:
        reproduced = evaluate_acceptance(mission, bundle_path.parent / "artifact")
        if recorded_checks != reproduced:
            errors.append("acceptance checks do not match independent reproduction")
        expected_status = "PASSED" if all(check["passed"] for check in reproduced) else "FAILED"
        if mission_status != expected_status:
            errors.append("acceptance status does not match independent reproduction")

    verification = bundle.get("verification")
    errors.extend(_key_errors("verification", verification, VERIFICATION_KEYS_BUILD_WEEK))
    if isinstance(verification, dict):
        if verification.get("claimed_status") != "LOCAL_VERIFIED":
            errors.append("verification.claimed_status must be LOCAL_VERIFIED")

    integrity = bundle.get("integrity")
    errors.extend(_key_errors("integrity", integrity, INTEGRITY_KEYS))
    anchor_status = "UNKNOWN"
    if isinstance(integrity, dict):
        anchor_status = integrity.get("anchor_status", "UNKNOWN")
        if integrity.get("canonicalization") != CANONICALIZATION_PROFILE:
            errors.append("integrity.canonicalization profile mismatch")
        if integrity.get("hash_algorithm") != HASH_ALGORITHM:
            errors.append("integrity.hash_algorithm must be sha256")
        if anchor_status != "UNANCHORED":
            errors.append("Build Week proof only permits anchor_status UNANCHORED")
        for field in ("event_merkle_root", "bundle_hash"):
            try:
                parse_sha256_digest(integrity.get(field))
            except ValueError as error:
                errors.append(f"integrity.{field} is invalid: {error}")
        try:
            if integrity.get("bundle_hash") != compute_bundle_hash(bundle):
                errors.append("integrity.bundle_hash mismatch")
        except (BundleFormatError, CanonicalizationError, RecursionError, TypeError, ValueError) as error:
            errors.append(f"bundle cannot be canonicalized: {error}")

    events = bundle.get("events")
    event_count = len(events) if isinstance(events, list) else 0
    errors.extend(verify_event_chain(events))
    if isinstance(events, list):
        if isinstance(integrity, dict) and integrity.get("event_count") != len(events):
            errors.append("integrity.event_count mismatch")
        step_hashes = [event.get("step_hash") for event in events if isinstance(event, dict)]
        if len(step_hashes) == len(events) and all(isinstance(item, str) for item in step_hashes):
            try:
                if isinstance(integrity, dict) and integrity.get("event_merkle_root") != merkle_root_from_step_hashes(step_hashes):
                    errors.append("integrity.event_merkle_root mismatch")
            except ValueError as error:
                errors.append(f"cannot construct Merkle tree: {error}")
        else:
            errors.append("cannot construct Merkle tree from malformed events")

        expected_types = (
            ["runtime.mission_started", "provider.artifact_proposal_received"]
            + ["runtime.artifact_materialized"] * len(valid_artifacts)
            + ["runtime.acceptance_completed"]
        )
        if [event.get("type") if isinstance(event, dict) else None for event in events] != expected_types:
            errors.append("Build Week event sequence mismatch")
        elif mission and isinstance(run, dict) and isinstance(provider, dict):
            if events[0].get("input") != {"mission_id": mission.mission_id, "manifest_hash": mission.manifest_hash}:
                errors.append("mission start input mismatch")
            expected_details = {
                "run_id": run.get("run_id"),
                "sandbox_backend": run.get("sandbox_backend"),
                "security_level": run.get("security_level"),
                "network_policy": run.get("network_policy"),
            }
            if events[0].get("details") != expected_details:
                errors.append("run metadata does not match the hashed start event")
            provider_event = events[1]
            if provider_event.get("details") != provider:
                errors.append("provider metadata does not match the hashed provider event")
            if provider_event.get("input") != {
                "provider": provider.get("provider"),
                "requested_model": provider.get("requested_model"),
                "input_hash": provider.get("input_hash"),
            }:
                errors.append("provider input evidence mismatch")
            if provider_event.get("output") != {
                "artifact_count": len(valid_artifacts),
                "response_hash": provider.get("response_hash"),
            }:
                errors.append("provider output evidence mismatch")
            materialized = events[2:-1]
            if [event.get("output") for event in materialized] != sorted(
                valid_artifacts, key=lambda item: item["path"]
            ):
                errors.append("materialization events do not match artifact evidence")
            if events[-1].get("output") != acceptance:
                errors.append("acceptance does not match the hashed final event")
            if events[-1].get("input") != {"check_count": len(mission.acceptance_checks)}:
                errors.append("acceptance event check_count mismatch")

    return VerificationResult(
        status="FAILED" if errors else "LOCAL_VERIFIED",
        mission_status=mission_status,
        anchor_status=anchor_status,
        errors=tuple(errors),
        event_count=event_count,
    )


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

    if bundle.get("schema_version") == SCHEMA_VERSION_BUILD_WEEK:
        return _verify_build_week_loaded(bundle, bundle_path=bundle_path)
    if bundle.get("schema_version") == SCHEMA_VERSION_V2:
        return _verify_v02_loaded(bundle, bundle_path=bundle_path)

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
