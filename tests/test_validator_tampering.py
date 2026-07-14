from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.runtime import run_demo
from agent_proof_runtime.validator import verify_bundle


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class TamperingTests(unittest.TestCase):
    def test_artifact_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            (result.output_dir / "artifact" / "hello.txt").write_text(
                "tampered\n", encoding="utf-8"
            )
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("sha256 mismatch" in error for error in verification.errors))

    def test_event_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["events"][1]["output"]["bytes_written"] = 999
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(
                any("output_hash mismatch" in error for error in verification.errors)
            )

    def test_run_metadata_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["run"]["run_id"] = "forged-run-id"
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(
                any("bundle_hash mismatch" in error for error in verification.errors)
            )
            self.assertTrue(
                any("hashed start event" in error for error in verification.errors)
            )

    def test_artifact_path_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["artifacts"][0]["path"] = "../outside.txt"
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(
                any("canonical relative POSIX path" in error for error in verification.errors)
            )

    def test_unknown_top_level_field_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["trust_me"] = True
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("unknown keys" in error for error in verification.errors))

    def test_forged_passed_check_is_independently_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["events"][-1]["details"]["worker_return_code"] = 9
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(
                any("independently reproduced" in error for error in verification.errors)
            )

    def test_malformed_check_name_returns_failed_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_demo(Path(temporary) / "run")
            bundle = _read(result.bundle_path)
            bundle["validation"]["checks"][0]["name"] = []
            _write(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("invalid name" in error for error in verification.errors))

    def test_duplicate_json_key_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            bundle_path = Path(temporary) / "proof-bundle.json"
            bundle_path.write_text(
                '{"schema_version":"one","schema_version":"two"}',
                encoding="utf-8",
            )
            verification = verify_bundle(bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("duplicate JSON key" in error for error in verification.errors))


if __name__ == "__main__":
    unittest.main()
