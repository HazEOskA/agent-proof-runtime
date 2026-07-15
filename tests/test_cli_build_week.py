from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from agent_proof_runtime.cli import main
from agent_proof_runtime.validator import verify_bundle


class BuildWeekCliTests(unittest.TestCase):
    def test_validation_provider_mission_and_verification_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            value = json.loads(
                Path("examples/build-week-mission.json").read_text(encoding="utf-8")
            )
            invalid = root / "invalid.json"
            invalid_value = dict(value)
            invalid_value["unexpected"] = True
            invalid.write_text(json.dumps(invalid_value), encoding="utf-8")
            with redirect_stderr(StringIO()):
                self.assertEqual(
                    main(["run", str(invalid), "--output", str(root / "invalid-run")]),
                    2,
                )

            failed = root / "failed.json"
            value["acceptance_checks"][2]["text"] = "text fixture does not contain"
            failed.write_text(json.dumps(value), encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(["run", str(failed), "--output", str(root / "failed-run")]),
                    4,
                )
            faithfully_failed = verify_bundle(root / "failed-run" / "proof-bundle.json")
            self.assertEqual(faithfully_failed.status, "LOCAL_VERIFIED")
            self.assertEqual(faithfully_failed.mission_status, "FAILED")

            artifact = root / "failed-run" / "artifact" / "site" / "index.html"
            artifact.write_text("tampered", encoding="utf-8")
            with redirect_stdout(StringIO()):
                self.assertEqual(
                    main(["verify", str(root / "failed-run" / "proof-bundle.json")]),
                    1,
                )


if __name__ == "__main__":
    unittest.main()
