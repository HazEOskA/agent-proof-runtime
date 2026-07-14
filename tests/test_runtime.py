from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.runtime import RunDirectoryExists, run_demo
from agent_proof_runtime.validator import verify_bundle


class RuntimeTests(unittest.TestCase):
    def test_demo_produces_artifact_bundle_report_and_verified_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            result = run_demo(output)

            self.assertEqual(result.mission_status, "PASSED")
            self.assertEqual(result.verification.status, "LOCAL_VERIFIED")
            self.assertEqual(result.verification.anchor_status, "UNANCHORED")
            self.assertTrue((output / "artifact" / "hello.txt").is_file())
            self.assertTrue(result.bundle_path.is_file())
            self.assertTrue(result.report_path.is_file())
            self.assertIn("Execution receipt", result.report_path.read_text(encoding="utf-8"))

            independent = verify_bundle(result.bundle_path)
            self.assertTrue(independent.valid, independent.errors)

    def test_existing_run_directory_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            output.mkdir()
            marker = output / "belongs-to-user.txt"
            marker.write_text("keep", encoding="utf-8")
            with self.assertRaises(RunDirectoryExists):
                run_demo(output)
            self.assertEqual(marker.read_text(encoding="utf-8"), "keep")


if __name__ == "__main__":
    unittest.main()
