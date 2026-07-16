from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.mission import MissionValidationError
from agent_proof_runtime.mission_v1 import load_build_week_mission, parse_build_week_mission


EXAMPLE = Path("examples/build-week-mission.json")


def example_value() -> dict:
    return json.loads(EXAMPLE.read_text(encoding="utf-8"))


class BuildWeekManifestTests(unittest.TestCase):
    def test_checked_in_manifest_is_strict_and_versioned(self) -> None:
        mission = load_build_week_mission(EXAMPLE)
        self.assertEqual(mission.mission_id, "build-week-demo")
        self.assertEqual(mission.model, "gpt-5.6")
        self.assertEqual(len(mission.acceptance_checks), 6)
        self.assertTrue(mission.manifest_hash.startswith("sha256:"))

    def assert_invalid(self, value: dict, fragment: str) -> None:
        with self.assertRaises(MissionValidationError) as caught:
            parse_build_week_mission(value)
        self.assertIn(fragment, "; ".join(caught.exception.errors))

    def test_unknown_top_level_field_is_rejected(self) -> None:
        value = example_value()
        value["shell"] = "rm -rf /"
        self.assert_invalid(value, "unknown keys: shell")

    def test_absolute_and_parent_paths_are_rejected(self) -> None:
        for hostile in ("/tmp/result.txt", "../result.txt", "site/../../result.txt"):
            with self.subTest(path=hostile):
                value = example_value()
                value["artifact_contract"]["artifacts"][0]["path"] = hostile
                self.assert_invalid(value, "canonical relative POSIX path")

    def test_duplicate_artifact_paths_are_rejected(self) -> None:
        value = example_value()
        value["artifact_contract"]["artifacts"][1]["path"] = "site/index.html"
        self.assert_invalid(value, "duplicates artifact path")

    def test_invalid_limits_and_malformed_check_are_rejected(self) -> None:
        value = example_value()
        value["limits"]["provider_timeout_seconds"] = 0
        value["acceptance_checks"][0]["command"] = "pytest"
        self.assert_invalid(value, "between 1 and 300")
        self.assert_invalid(value, "unknown keys: command")

    def test_unsafe_media_type_and_reasoning_persistence_are_rejected(self) -> None:
        value = example_value()
        value["artifact_contract"]["allowed_media_types"][0] = "application/x-executable"
        value["analysis_policy"]["persist_reasoning"] = True
        self.assert_invalid(value, "unsafe media types")
        self.assert_invalid(value, "persist_reasoning must be false")

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mission.json"
            raw = EXAMPLE.read_text(encoding="utf-8").replace(
                '"schema_version": "apr.mission.v1",',
                '"schema_version": "apr.mission.v1",\n  "schema_version": "apr.mission.v1",',
                1,
            )
            path.write_text(raw, encoding="utf-8")
            with self.assertRaises(MissionValidationError) as caught:
                load_build_week_mission(path)
            self.assertIn("duplicate JSON key", str(caught.exception))

    def test_oversized_input_is_rejected_before_json_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "mission.json"
            path.write_text(" " * (1024 * 1024 + 1), encoding="utf-8")
            with self.assertRaises(MissionValidationError) as caught:
                load_build_week_mission(path)
            self.assertIn("1 MiB", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
