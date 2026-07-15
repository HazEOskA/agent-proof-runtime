"""Deterministic, shell-free acceptance checks shared with the verifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .mission_v1 import BuildWeekMission


def _target(artifact_root: Path, relative: str) -> Path | None:
    root = artifact_root.resolve()
    target = artifact_root.joinpath(*relative.split("/"))
    if target.is_symlink():
        return None
    try:
        resolved = target.resolve(strict=True)
    except (OSError, ValueError):
        return None
    if not resolved.is_relative_to(root) or not target.is_file():
        return None
    return target


def _regular_files(artifact_root: Path) -> list[Path]:
    if not artifact_root.is_dir() or artifact_root.is_symlink():
        return []
    root = artifact_root.resolve()
    files: list[Path] = []
    for candidate in artifact_root.rglob("*"):
        if candidate.is_symlink() or not candidate.is_file():
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, ValueError):
            continue
        if resolved.is_relative_to(root):
            files.append(candidate)
    return sorted(files, key=lambda item: item.relative_to(artifact_root).as_posix())


def _load_json_object(path: Path) -> tuple[bool, Any]:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    try:
        return True, json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError, RecursionError):
        return False, None


def evaluate_acceptance(
    mission: BuildWeekMission, artifact_root: Path
) -> list[dict[str, Any]]:
    """Evaluate the manifest's allowlisted checks without executing code."""

    results: list[dict[str, Any]] = []
    for check in mission.acceptance_checks:
        check_type = check["type"]
        expected: Any
        actual: Any
        passed = False

        if check_type == "file_count":
            expected = {"minimum": check["minimum"], "maximum": check["maximum"]}
            actual = {"count": len(_regular_files(artifact_root))}
            passed = check["minimum"] <= actual["count"] <= check["maximum"]
        else:
            target = _target(artifact_root, check["path"])
            if check_type == "file_exists":
                expected = {"exists": True}
                actual = {"exists": target is not None}
                passed = actual["exists"]
            elif check_type == "contains_text":
                expected = {"text": check["text"]}
                contains = False
                if target is not None:
                    try:
                        contains = check["text"] in target.read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        pass
                actual = {"contains": contains}
                passed = contains
            elif check_type == "json_valid":
                expected = {"valid": True}
                valid, _ = _load_json_object(target) if target is not None else (False, None)
                actual = {"valid": valid}
                passed = valid
            elif check_type == "json_required_keys":
                expected = {"keys": list(check["keys"])}
                valid, value = _load_json_object(target) if target is not None else (False, None)
                present = (
                    [key for key in check["keys"] if key in value]
                    if valid and isinstance(value, dict)
                    else []
                )
                missing = [key for key in check["keys"] if key not in present]
                actual = {"present": present, "missing": missing}
                passed = valid and isinstance(value, dict) and not missing
            elif check_type == "maximum_size":
                expected = {"max_bytes": check["max_bytes"]}
                size = target.stat().st_size if target is not None else None
                actual = {"size": size}
                passed = size is not None and size <= check["max_bytes"]
            else:  # The strict manifest parser makes this unreachable.
                expected = {}
                actual = {"error": "unsupported check"}

        results.append(
            {
                "id": check["id"],
                "type": check_type,
                "passed": bool(passed),
                "expected": expected,
                "actual": actual,
            }
        )
    return results
