"""Strict declarative mission contract for Agent Proof Runtime v0.2."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import CanonicalizationError, canonicalize, hash_json

MISSION_SCHEMA_VERSION = "apr.mission.v0.2"
MAX_MISSION_BYTES = 1024 * 1024
PINNED_IMAGE = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9._/:\-]*@sha256:[0-9a-f]{64}$"
)
MISSION_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")

MISSION_KEYS = frozenset(
    {
        "schema_version",
        "mission_id",
        "backend",
        "workload",
        "limits",
        "network",
        "artifacts",
    }
)
LIMIT_KEYS = frozenset({"timeout_seconds", "memory_mb", "cpu_millis", "pids"})
ARTIFACT_KEYS = frozenset({"required", "max_files", "max_bytes"})


class MissionValidationError(ValueError):
    def __init__(self, errors: list[str] | tuple[str, ...]):
        self.errors = tuple(errors)
        super().__init__("; ".join(self.errors))


@dataclass(frozen=True)
class ResourceLimits:
    timeout_seconds: int
    memory_mb: int
    cpu_millis: int
    pids: int


@dataclass(frozen=True)
class ArtifactPolicy:
    required: bool
    max_files: int
    max_bytes: int


@dataclass(frozen=True)
class Workload:
    kind: str
    image: str | None = None
    command: tuple[str, ...] = ()
    source: str | None = None


@dataclass(frozen=True)
class MissionSpec:
    mission_id: str
    backend: str
    workload: Workload
    limits: ResourceLimits
    network_mode: str
    artifacts: ArtifactPolicy
    manifest_path: Path | None = None

    @property
    def source_dir(self) -> Path | None:
        if self.workload.source is None:
            return None
        base = self.manifest_path.parent if self.manifest_path else Path.cwd()
        return (base / self.workload.source).resolve()

    @property
    def spec_hash(self) -> str:
        return hash_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        if self.workload.kind == "builtin-demo":
            workload: dict[str, Any] = {"kind": "builtin-demo"}
        else:
            workload = {
                "kind": "container-command",
                "image": self.workload.image,
                "command": list(self.workload.command),
                "source": self.workload.source,
            }
        return {
            "schema_version": MISSION_SCHEMA_VERSION,
            "mission_id": self.mission_id,
            "backend": self.backend,
            "workload": workload,
            "limits": {
                "timeout_seconds": self.limits.timeout_seconds,
                "memory_mb": self.limits.memory_mb,
                "cpu_millis": self.limits.cpu_millis,
                "pids": self.limits.pids,
            },
            "network": {"mode": self.network_mode},
            "artifacts": {
                "required": self.artifacts.required,
                "max_files": self.artifacts.max_files,
                "max_bytes": self.artifacts.max_bytes,
            },
        }


def _object_keys(
    label: str, value: Any, expected: frozenset[str], errors: list[str]
) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    actual = frozenset(value)
    missing = sorted(expected - actual)
    unknown = sorted(actual - expected)
    if missing:
        errors.append(f"{label} is missing keys: {', '.join(missing)}")
    if unknown:
        errors.append(f"{label} has unknown keys: {', '.join(unknown)}")
    return not missing and not unknown


def _bounded_integer(
    value: Any, *, label: str, minimum: int, maximum: int, errors: list[str]
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{label} must be an integer")
        return minimum
    if not minimum <= value <= maximum:
        errors.append(f"{label} must be between {minimum} and {maximum}")
    return value


def _validate_source(value: Any, errors: list[str]) -> str | None:
    if not isinstance(value, str) or not value:
        errors.append("workload.source must be a non-empty string")
        return None
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or "\\" in value
        or path.as_posix() != value
    ):
        errors.append("workload.source must be a canonical relative POSIX path")
    return value


def parse_mission(
    value: Any,
    *,
    manifest_path: Path | None = None,
    check_source: bool = False,
) -> MissionSpec:
    errors: list[str] = []
    if not _object_keys("mission", value, MISSION_KEYS, errors):
        raise MissionValidationError(errors)

    try:
        canonicalize(value)
    except (CanonicalizationError, RecursionError) as error:
        errors.append(f"mission is outside the canonical JSON profile: {error}")

    if value.get("schema_version") != MISSION_SCHEMA_VERSION:
        errors.append(f"schema_version must be {MISSION_SCHEMA_VERSION}")

    mission_id = value.get("mission_id")
    if not isinstance(mission_id, str) or not MISSION_ID.fullmatch(mission_id):
        errors.append("mission_id must match [a-z0-9][a-z0-9-]{2,63}")

    backend = value.get("backend")
    if backend not in {"local-demo", "gvisor"}:
        errors.append("backend must be local-demo or gvisor")

    workload_value = value.get("workload")
    workload = Workload(kind="invalid")
    if isinstance(workload_value, dict):
        kind = workload_value.get("kind")
        if kind == "builtin-demo":
            _object_keys("workload", workload_value, frozenset({"kind"}), errors)
            workload = Workload(kind="builtin-demo")
        elif kind == "container-command":
            expected = frozenset({"kind", "image", "command", "source"})
            _object_keys("workload", workload_value, expected, errors)
            image = workload_value.get("image")
            if not isinstance(image, str) or not PINNED_IMAGE.fullmatch(image):
                errors.append("workload.image must be pinned with @sha256:<64 lowercase hex>")
                image = None
            command_value = workload_value.get("command")
            command: tuple[str, ...] = ()
            if not isinstance(command_value, list) or not 1 <= len(command_value) <= 64:
                errors.append("workload.command must contain between 1 and 64 arguments")
            elif not all(
                isinstance(argument, str)
                and argument
                and "\x00" not in argument
                and len(argument) <= 1024
                for argument in command_value
            ):
                errors.append("workload.command arguments must be non-empty safe strings")
            else:
                command = tuple(command_value)
            source = _validate_source(workload_value.get("source"), errors)
            workload = Workload(
                kind="container-command",
                image=image,
                command=command,
                source=source,
            )
        else:
            errors.append("workload.kind must be builtin-demo or container-command")
    else:
        errors.append("workload must be an object")

    limits_value = value.get("limits")
    limits = ResourceLimits(30, 256, 1000, 64)
    if _object_keys("limits", limits_value, LIMIT_KEYS, errors):
        limits = ResourceLimits(
            timeout_seconds=_bounded_integer(
                limits_value["timeout_seconds"],
                label="limits.timeout_seconds",
                minimum=1,
                maximum=300,
                errors=errors,
            ),
            memory_mb=_bounded_integer(
                limits_value["memory_mb"],
                label="limits.memory_mb",
                minimum=64,
                maximum=4096,
                errors=errors,
            ),
            cpu_millis=_bounded_integer(
                limits_value["cpu_millis"],
                label="limits.cpu_millis",
                minimum=100,
                maximum=4000,
                errors=errors,
            ),
            pids=_bounded_integer(
                limits_value["pids"],
                label="limits.pids",
                minimum=8,
                maximum=512,
                errors=errors,
            ),
        )

    network_value = value.get("network")
    network_mode = "invalid"
    if _object_keys("network", network_value, frozenset({"mode"}), errors):
        network_mode = network_value.get("mode")
        if network_mode != "none":
            errors.append("v0.2 requires network.mode to be none")

    artifacts_value = value.get("artifacts")
    artifacts = ArtifactPolicy(True, 100, 5 * 1024 * 1024)
    if _object_keys("artifacts", artifacts_value, ARTIFACT_KEYS, errors):
        required = artifacts_value["required"]
        if not isinstance(required, bool):
            errors.append("artifacts.required must be boolean")
            required = True
        artifacts = ArtifactPolicy(
            required=required,
            max_files=_bounded_integer(
                artifacts_value["max_files"],
                label="artifacts.max_files",
                minimum=1,
                maximum=1000,
                errors=errors,
            ),
            max_bytes=_bounded_integer(
                artifacts_value["max_bytes"],
                label="artifacts.max_bytes",
                minimum=1024,
                maximum=100 * 1024 * 1024,
                errors=errors,
            ),
        )

    if backend == "local-demo" and workload.kind != "builtin-demo":
        errors.append("local-demo only accepts the builtin-demo workload")
    if backend == "gvisor" and workload.kind != "container-command":
        errors.append("gvisor requires a container-command workload")

    resolved_manifest = manifest_path.resolve() if manifest_path else None
    spec = MissionSpec(
        mission_id=mission_id if isinstance(mission_id, str) else "invalid",
        backend=backend if isinstance(backend, str) else "invalid",
        workload=workload,
        limits=limits,
        network_mode=network_mode if isinstance(network_mode, str) else "invalid",
        artifacts=artifacts,
        manifest_path=resolved_manifest,
    )
    if check_source and workload.source:
        source_dir = spec.source_dir
        if source_dir is None or not source_dir.is_dir():
            errors.append(f"workload.source directory does not exist: {workload.source}")

    if errors:
        raise MissionValidationError(errors)
    return spec


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MissionValidationError([f"duplicate JSON key: {key}"])
        result[key] = value
    return result


def load_mission(path: str | Path) -> MissionSpec:
    mission_path = Path(path)
    try:
        if mission_path.stat().st_size > MAX_MISSION_BYTES:
            raise MissionValidationError(["mission exceeds the 1 MiB size limit"])
        value = json.loads(
            mission_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except MissionValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise MissionValidationError([f"invalid mission JSON: {error}"]) from error
    return parse_mission(value, manifest_path=mission_path, check_source=True)


def builtin_demo_mission() -> MissionSpec:
    return parse_mission(
        {
            "schema_version": MISSION_SCHEMA_VERSION,
            "mission_id": "builtin-demo",
            "backend": "local-demo",
            "workload": {"kind": "builtin-demo"},
            "limits": {
                "timeout_seconds": 5,
                "memory_mb": 256,
                "cpu_millis": 1000,
                "pids": 64,
            },
            "network": {"mode": "none"},
            "artifacts": {
                "required": True,
                "max_files": 100,
                "max_bytes": 5 * 1024 * 1024,
            },
        }
    )
