"""Strict Build Week mission manifest.

The v1 manifest describes desired artifacts and deterministic acceptance checks.
It never grants a provider permission to execute host commands.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import CanonicalizationError, canonicalize, hash_json
from .mission import MissionValidationError

MISSION_SCHEMA_VERSION_V1 = "apr.mission.v1"
MAX_MISSION_BYTES_V1 = 1024 * 1024
MISSION_ID = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
SAFE_MEDIA_TYPES = frozenset(
    {
        "application/json",
        "application/javascript",
        "text/css",
        "text/html",
        "text/markdown",
        "text/plain",
    }
)

TOP_LEVEL_KEYS = frozenset(
    {
        "schema_version",
        "mission_id",
        "title",
        "goal",
        "provider",
        "model",
        "artifact_contract",
        "limits",
        "acceptance_checks",
        "analysis_policy",
    }
)
CONTRACT_KEYS = frozenset(
    {"artifacts", "max_files", "max_total_bytes", "allowed_media_types"}
)
ARTIFACT_KEYS = frozenset(
    {"path", "media_type", "max_bytes", "required", "fixture_content"}
)
LIMIT_KEYS = frozenset({"provider_timeout_seconds", "max_output_tokens"})
ANALYSIS_KEYS = frozenset({"persist_reasoning", "allow_reasoning_summary"})
CHECK_KEYS = {
    "file_exists": frozenset({"id", "type", "path"}),
    "file_count": frozenset({"id", "type", "minimum", "maximum"}),
    "contains_text": frozenset({"id", "type", "path", "text"}),
    "json_valid": frozenset({"id", "type", "path"}),
    "json_required_keys": frozenset({"id", "type", "path", "keys"}),
    "maximum_size": frozenset({"id", "type", "path", "max_bytes"}),
}


@dataclass(frozen=True)
class ArtifactContractEntry:
    path: str
    media_type: str
    max_bytes: int
    required: bool
    fixture_content: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "max_bytes": self.max_bytes,
            "required": self.required,
            "fixture_content": self.fixture_content,
        }

    def provider_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "max_bytes": self.max_bytes,
            "required": self.required,
        }


@dataclass(frozen=True)
class ArtifactContract:
    artifacts: tuple[ArtifactContractEntry, ...]
    max_files: int
    max_total_bytes: int
    allowed_media_types: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifacts": [item.to_dict() for item in self.artifacts],
            "max_files": self.max_files,
            "max_total_bytes": self.max_total_bytes,
            "allowed_media_types": list(self.allowed_media_types),
        }

    def provider_dict(self) -> dict[str, Any]:
        return {
            "artifacts": [item.provider_dict() for item in self.artifacts],
            "max_files": self.max_files,
            "max_total_bytes": self.max_total_bytes,
            "allowed_media_types": list(self.allowed_media_types),
        }


@dataclass(frozen=True)
class ProviderLimits:
    provider_timeout_seconds: int
    max_output_tokens: int

    def to_dict(self) -> dict[str, int]:
        return {
            "provider_timeout_seconds": self.provider_timeout_seconds,
            "max_output_tokens": self.max_output_tokens,
        }


@dataclass(frozen=True)
class BuildWeekMission:
    mission_id: str
    title: str
    goal: str
    provider: str
    model: str
    artifact_contract: ArtifactContract
    limits: ProviderLimits
    acceptance_checks: tuple[dict[str, Any], ...]
    analysis_policy: dict[str, bool]
    manifest_path: Path | None = None

    @property
    def manifest_hash(self) -> str:
        return hash_json(self.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": MISSION_SCHEMA_VERSION_V1,
            "mission_id": self.mission_id,
            "title": self.title,
            "goal": self.goal,
            "provider": self.provider,
            "model": self.model,
            "artifact_contract": self.artifact_contract.to_dict(),
            "limits": self.limits.to_dict(),
            "acceptance_checks": [dict(check) for check in self.acceptance_checks],
            "analysis_policy": dict(self.analysis_policy),
        }

    def provider_input(self) -> dict[str, Any]:
        """Safe model input. Fixture answers are intentionally excluded."""

        return {
            "schema_version": MISSION_SCHEMA_VERSION_V1,
            "mission_id": self.mission_id,
            "title": self.title,
            "goal": self.goal,
            "model": self.model,
            "artifact_contract": self.artifact_contract.provider_dict(),
            "acceptance_checks": [dict(check) for check in self.acceptance_checks],
            "analysis_policy": dict(self.analysis_policy),
        }


def _keys(label: str, value: Any, expected: frozenset[str], errors: list[str]) -> bool:
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


def _integer(
    value: Any, *, label: str, minimum: int, maximum: int, errors: list[str]
) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        errors.append(f"{label} must be an integer")
        return minimum
    if not minimum <= value <= maximum:
        errors.append(f"{label} must be between {minimum} and {maximum}")
    return value


def _text(
    value: Any, *, label: str, minimum: int, maximum: int, errors: list[str]
) -> str:
    if not isinstance(value, str) or not minimum <= len(value) <= maximum:
        errors.append(f"{label} must contain between {minimum} and {maximum} characters")
        return ""
    if "\x00" in value:
        errors.append(f"{label} cannot contain NUL")
    return value


def canonical_artifact_path(value: Any, *, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value or len(value) > 240:
        errors.append(f"{label} must be a non-empty path of at most 240 characters")
        return ""
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or ".." in path.parts
        or "." in path.parts
        or "\\" in value
        or path.as_posix() != value
        or len(path.parts) > 16
    ):
        errors.append(f"{label} must be a canonical relative POSIX path")
    return value


def parse_build_week_mission(
    value: Any, *, manifest_path: Path | None = None
) -> BuildWeekMission:
    errors: list[str] = []
    if not _keys("mission", value, TOP_LEVEL_KEYS, errors):
        raise MissionValidationError(errors)
    try:
        canonicalize(value)
    except (CanonicalizationError, RecursionError) as error:
        errors.append(f"mission is outside the canonical JSON profile: {error}")

    if value.get("schema_version") != MISSION_SCHEMA_VERSION_V1:
        errors.append(f"schema_version must be {MISSION_SCHEMA_VERSION_V1}")
    mission_id = value.get("mission_id")
    if not isinstance(mission_id, str) or not MISSION_ID.fullmatch(mission_id):
        errors.append("mission_id must match [a-z0-9][a-z0-9-]{2,63}")
        mission_id = "invalid"
    title = _text(value.get("title"), label="title", minimum=3, maximum=160, errors=errors)
    goal = _text(value.get("goal"), label="goal", minimum=10, maximum=4000, errors=errors)
    provider = value.get("provider")
    if provider not in {"fixture", "openai"}:
        errors.append("provider must be fixture or openai")
        provider = "invalid"
    model = _text(value.get("model"), label="model", minimum=1, maximum=128, errors=errors)

    contract_value = value.get("artifact_contract")
    entries: list[ArtifactContractEntry] = []
    max_files = 1
    max_total_bytes = 1
    allowed_media_types: tuple[str, ...] = ()
    if _keys("artifact_contract", contract_value, CONTRACT_KEYS, errors):
        max_files = _integer(
            contract_value["max_files"],
            label="artifact_contract.max_files",
            minimum=1,
            maximum=100,
            errors=errors,
        )
        max_total_bytes = _integer(
            contract_value["max_total_bytes"],
            label="artifact_contract.max_total_bytes",
            minimum=1,
            maximum=5 * 1024 * 1024,
            errors=errors,
        )
        media_value = contract_value["allowed_media_types"]
        if (
            not isinstance(media_value, list)
            or not media_value
            or not all(isinstance(item, str) for item in media_value)
        ):
            errors.append("artifact_contract.allowed_media_types must be a non-empty string array")
        else:
            if len(set(media_value)) != len(media_value):
                errors.append("artifact_contract.allowed_media_types cannot contain duplicates")
            unsafe = sorted(set(media_value) - SAFE_MEDIA_TYPES)
            if unsafe:
                errors.append("artifact_contract contains unsafe media types: " + ", ".join(unsafe))
            allowed_media_types = tuple(media_value)

        artifacts_value = contract_value["artifacts"]
        if not isinstance(artifacts_value, list) or not artifacts_value:
            errors.append("artifact_contract.artifacts must be a non-empty array")
        else:
            seen_paths: set[str] = set()
            for index, artifact in enumerate(artifacts_value):
                label = f"artifact_contract.artifacts[{index}]"
                if not _keys(label, artifact, ARTIFACT_KEYS, errors):
                    continue
                path = canonical_artifact_path(
                    artifact["path"], label=f"{label}.path", errors=errors
                )
                if path in seen_paths:
                    errors.append(f"{label}.path duplicates artifact path {path}")
                seen_paths.add(path)
                media_type = artifact["media_type"]
                if not isinstance(media_type, str) or media_type not in SAFE_MEDIA_TYPES:
                    errors.append(f"{label}.media_type is not allowed")
                    media_type = "text/plain"
                elif allowed_media_types and media_type not in allowed_media_types:
                    errors.append(f"{label}.media_type is outside allowed_media_types")
                artifact_max = _integer(
                    artifact["max_bytes"],
                    label=f"{label}.max_bytes",
                    minimum=1,
                    maximum=1024 * 1024,
                    errors=errors,
                )
                required = artifact["required"]
                if not isinstance(required, bool):
                    errors.append(f"{label}.required must be boolean")
                    required = True
                content = artifact["fixture_content"]
                if not isinstance(content, str):
                    errors.append(f"{label}.fixture_content must be a string")
                    content = ""
                elif len(content.encode("utf-8")) > artifact_max:
                    errors.append(f"{label}.fixture_content exceeds max_bytes")
                entries.append(
                    ArtifactContractEntry(path, media_type, artifact_max, required, content)
                )
            if len(artifacts_value) > max_files:
                errors.append("artifact_contract.artifacts exceeds max_files")
            fixture_total = sum(len(item.fixture_content.encode("utf-8")) for item in entries)
            if fixture_total > max_total_bytes:
                errors.append("fixture artifact content exceeds max_total_bytes")

    limits_value = value.get("limits")
    limits = ProviderLimits(30, 2048)
    if _keys("limits", limits_value, LIMIT_KEYS, errors):
        limits = ProviderLimits(
            provider_timeout_seconds=_integer(
                limits_value["provider_timeout_seconds"],
                label="limits.provider_timeout_seconds",
                minimum=1,
                maximum=300,
                errors=errors,
            ),
            max_output_tokens=_integer(
                limits_value["max_output_tokens"],
                label="limits.max_output_tokens",
                minimum=128,
                maximum=32768,
                errors=errors,
            ),
        )

    checks_value = value.get("acceptance_checks")
    checks: list[dict[str, Any]] = []
    if not isinstance(checks_value, list) or not 1 <= len(checks_value) <= 100:
        errors.append("acceptance_checks must contain between 1 and 100 checks")
    else:
        ids: set[str] = set()
        paths = {entry.path for entry in entries}
        for index, check in enumerate(checks_value):
            label = f"acceptance_checks[{index}]"
            check_type = check.get("type") if isinstance(check, dict) else None
            expected = CHECK_KEYS.get(check_type)
            if expected is None:
                errors.append(f"{label}.type is not supported")
                continue
            if not _keys(label, check, expected, errors):
                continue
            check_id = check["id"]
            if (
                not isinstance(check_id, str)
                or not re.fullmatch(r"[a-z][a-z0-9_-]{1,63}", check_id)
            ):
                errors.append(f"{label}.id has an invalid format")
            elif check_id in ids:
                errors.append(f"{label}.id is duplicated")
            ids.add(check_id)
            if "path" in check:
                check_path = canonical_artifact_path(
                    check["path"], label=f"{label}.path", errors=errors
                )
                if check_path not in paths:
                    errors.append(f"{label}.path is not declared in artifact_contract")
            if check_type == "file_count":
                minimum = _integer(
                    check["minimum"], label=f"{label}.minimum", minimum=0,
                    maximum=max_files, errors=errors
                )
                maximum = _integer(
                    check["maximum"], label=f"{label}.maximum", minimum=0,
                    maximum=max_files, errors=errors
                )
                if minimum > maximum:
                    errors.append(f"{label}.minimum cannot exceed maximum")
            elif check_type == "contains_text":
                _text(check["text"], label=f"{label}.text", minimum=1, maximum=4096, errors=errors)
            elif check_type == "json_required_keys":
                required_keys = check["keys"]
                if (
                    not isinstance(required_keys, list)
                    or not required_keys
                    or not all(isinstance(item, str) and item for item in required_keys)
                ):
                    errors.append(f"{label}.keys must be a non-empty string array")
                elif len(set(required_keys)) != len(required_keys):
                    errors.append(f"{label}.keys cannot contain duplicates")
            elif check_type == "maximum_size":
                _integer(
                    check["max_bytes"], label=f"{label}.max_bytes", minimum=1,
                    maximum=max_total_bytes, errors=errors
                )
            checks.append(dict(check))

    analysis_value = value.get("analysis_policy")
    analysis_policy = {"persist_reasoning": False, "allow_reasoning_summary": False}
    if _keys("analysis_policy", analysis_value, ANALYSIS_KEYS, errors):
        for field in sorted(ANALYSIS_KEYS):
            if not isinstance(analysis_value[field], bool):
                errors.append(f"analysis_policy.{field} must be boolean")
            elif analysis_value[field]:
                errors.append(f"analysis_policy.{field} must be false")
        analysis_policy = dict(analysis_value)

    if errors:
        raise MissionValidationError(errors)
    return BuildWeekMission(
        mission_id=mission_id,
        title=title,
        goal=goal,
        provider=provider,
        model=model,
        artifact_contract=ArtifactContract(
            artifacts=tuple(entries),
            max_files=max_files,
            max_total_bytes=max_total_bytes,
            allowed_media_types=allowed_media_types,
        ),
        limits=limits,
        acceptance_checks=tuple(checks),
        analysis_policy=analysis_policy,
        manifest_path=manifest_path,
    )


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise MissionValidationError([f"duplicate JSON key: {key}"])
        result[key] = value
    return result


def load_build_week_mission(path: str | Path) -> BuildWeekMission:
    manifest_path = Path(path)
    try:
        size = manifest_path.stat().st_size
    except OSError as error:
        raise MissionValidationError([f"cannot read mission: {error}"]) from error
    if size > MAX_MISSION_BYTES_V1:
        raise MissionValidationError(["mission exceeds the 1 MiB size limit"])
    try:
        value = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except MissionValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise MissionValidationError([f"invalid mission JSON: {error}"]) from error
    return parse_build_week_mission(value, manifest_path=manifest_path.resolve())
