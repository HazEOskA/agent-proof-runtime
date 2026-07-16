"""Version-aware mission loading without changing legacy parsers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from .mission import MAX_MISSION_BYTES, MISSION_SCHEMA_VERSION, MissionSpec, MissionValidationError, load_mission
from .mission_v1 import BuildWeekMission, MISSION_SCHEMA_VERSION_V1, load_build_week_mission

DeclaredMission = Union[MissionSpec, BuildWeekMission]


def mission_schema(path: str | Path) -> str:
    manifest = Path(path)
    try:
        if manifest.stat().st_size > MAX_MISSION_BYTES:
            raise MissionValidationError(["mission exceeds the 1 MiB size limit"])
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except MissionValidationError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise MissionValidationError([f"invalid mission JSON: {error}"]) from error
    if not isinstance(value, dict):
        raise MissionValidationError(["mission root must be an object"])
    version = value.get("schema_version")
    if version not in {MISSION_SCHEMA_VERSION, MISSION_SCHEMA_VERSION_V1}:
        raise MissionValidationError(
            [
                "schema_version must be one of "
                f"{MISSION_SCHEMA_VERSION}, {MISSION_SCHEMA_VERSION_V1}"
            ]
        )
    return version


def load_declared_mission(path: str | Path) -> DeclaredMission:
    version = mission_schema(path)
    if version == MISSION_SCHEMA_VERSION_V1:
        return load_build_week_mission(path)
    return load_mission(path)
