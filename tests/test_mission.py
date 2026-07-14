from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.mission import (
    MISSION_SCHEMA_VERSION,
    MissionValidationError,
    load_mission,
    parse_mission,
)


def _valid_demo() -> dict:
    return {
        "schema_version": MISSION_SCHEMA_VERSION,
        "mission_id": "test-demo",
        "backend": "local-demo",
        "workload": {"kind": "builtin-demo"},
        "limits": {
            "timeout_seconds": 5,
            "memory_mb": 256,
            "cpu_millis": 1000,
            "pids": 64,
        },
        "network": {"mode": "none"},
        "artifacts": {"required": True, "max_files": 100, "max_bytes": 5242880},
    }


class MissionSpecTests(unittest.TestCase):
    def test_demo_manifest_loads_and_has_stable_hash(self) -> None:
        spec = load_mission("missions/demo.json")
        self.assertEqual(spec.backend, "local-demo")
        self.assertEqual(spec.workload.kind, "builtin-demo")
        self.assertEqual(spec.to_dict()["schema_version"], MISSION_SCHEMA_VERSION)
        self.assertEqual(spec.spec_hash, load_mission("missions/demo.json").spec_hash)

    def test_gvisor_example_has_pinned_image_and_existing_source(self) -> None:
        spec = load_mission("missions/gvisor-python.example.json")
        self.assertEqual(spec.backend, "gvisor")
        self.assertIn("@sha256:", spec.workload.image or "")
        self.assertTrue(spec.source_dir and spec.source_dir.is_dir())

    def test_unknown_field_is_rejected(self) -> None:
        mission = _valid_demo()
        mission["trust_me"] = True
        with self.assertRaisesRegex(MissionValidationError, "unknown keys"):
            parse_mission(mission)

    def test_float_limit_is_rejected(self) -> None:
        mission = _valid_demo()
        mission["limits"]["memory_mb"] = 256.0
        with self.assertRaises(MissionValidationError) as raised:
            parse_mission(mission)
        self.assertTrue(any("integer" in error for error in raised.exception.errors))

    def test_local_backend_cannot_run_arbitrary_command(self) -> None:
        mission = _valid_demo()
        mission["workload"] = {
            "kind": "container-command",
            "image": "python@sha256:" + ("0" * 64),
            "command": ["python", "agent.py"],
            "source": "workload",
        }
        with self.assertRaises(MissionValidationError) as raised:
            parse_mission(mission)
        self.assertTrue(
            any("local-demo only accepts" in error for error in raised.exception.errors)
        )

    def test_unpinned_image_is_rejected(self) -> None:
        mission = _valid_demo()
        mission["backend"] = "gvisor"
        mission["workload"] = {
            "kind": "container-command",
            "image": "python:latest",
            "command": ["python", "agent.py"],
            "source": "workload",
        }
        with self.assertRaises(MissionValidationError) as raised:
            parse_mission(mission)
        self.assertTrue(any("pinned" in error for error in raised.exception.errors))

    def test_parent_source_path_is_rejected(self) -> None:
        mission = _valid_demo()
        mission["backend"] = "gvisor"
        mission["workload"] = {
            "kind": "container-command",
            "image": "python@sha256:" + ("0" * 64),
            "command": ["python", "agent.py"],
            "source": "../host",
        }
        with self.assertRaises(MissionValidationError) as raised:
            parse_mission(mission)
        self.assertTrue(any("canonical relative" in error for error in raised.exception.errors))

    def test_missing_source_directory_is_rejected_when_loading(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            mission = _valid_demo()
            mission["backend"] = "gvisor"
            mission["workload"] = {
                "kind": "container-command",
                "image": "python@sha256:" + ("0" * 64),
                "command": ["python", "agent.py"],
                "source": "missing",
            }
            path = root / "mission.json"
            path.write_text(json.dumps(mission), encoding="utf-8")
            with self.assertRaises(MissionValidationError) as raised:
                load_mission(path)
            self.assertTrue(any("does not exist" in error for error in raised.exception.errors))

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mission.json"
            path.write_text('{"schema_version":"one","schema_version":"two"}')
            with self.assertRaisesRegex(MissionValidationError, "duplicate JSON key"):
                load_mission(path)


if __name__ == "__main__":
    unittest.main()
