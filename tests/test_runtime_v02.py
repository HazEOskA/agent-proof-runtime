from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.runtime import run_mission
from agent_proof_runtime.validator import verify_bundle


class MissionRuntimeTests(unittest.TestCase):
    def test_mission_run_produces_v02_verified_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_mission("missions/demo.json", Path(temporary) / "run")
            bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["schema_version"], "apr.proof-bundle.v0.2")
            self.assertEqual(bundle["mission"]["spec"]["mission_id"], "builtin-demo")
            self.assertEqual(result.mission_status, "PASSED")
            self.assertTrue(result.verification.valid, result.verification.errors)

    def test_mission_spec_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_mission("missions/demo.json", Path(temporary) / "run")
            bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
            bundle["mission"]["spec"]["mission_id"] = "forged-mission"
            result.bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("spec_hash mismatch" in error for error in verification.errors))

    def test_v02_validation_check_is_independently_reproduced(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_mission("missions/demo.json", Path(temporary) / "run")
            bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
            bundle["validation"]["checks"][0]["passed"] = False
            result.bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(
                any("independently reproduced" in error for error in verification.errors)
            )

    def test_empty_event_chain_cannot_be_a_valid_v02_proof(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_mission("missions/demo.json", Path(temporary) / "run")
            bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
            bundle["events"] = []
            bundle["artifacts"] = []
            result.bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("must contain" in error for error in verification.errors))
            self.assertTrue(any("requires" in error for error in verification.errors))


if __name__ == "__main__":
    unittest.main()
