from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from agent_proof_runtime.build_week_runtime import run_build_week_mission
from agent_proof_runtime.bundle import compute_bundle_hash, load_bundle, write_bundle
from agent_proof_runtime.tamper_lab import TAMPER_CASES, run_fingerprint, run_tamper_case
from agent_proof_runtime.validator import verify_bundle
from agent_proof_runtime.build_week_runtime import ArtifactPolicyError
from agent_proof_runtime.providers import ArtifactProposal, ProposedArtifact, ProviderResult


EXAMPLE = Path("examples/build-week-mission.json")


class BuildWeekRuntimeTests(unittest.TestCase):
    def test_provider_cannot_escape_contract_and_no_run_is_created(self) -> None:
        class HostileProvider:
            name = "fixture"

            def propose(self, mission):
                return ProviderResult(
                    proposal=ArtifactProposal(
                        (ProposedArtifact("../escape.txt", "text/plain", "hostile"),)
                    ),
                    metadata={},
                )

        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with self.assertRaises(ArtifactPolicyError):
                run_build_week_mission(EXAMPLE, output, provider=HostileProvider())
            self.assertFalse(output.exists())

    def test_fixture_run_contains_complete_versioned_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run = Path(temporary) / "run"
            result = run_build_week_mission(EXAMPLE, run, provider_name="fixture")
            self.assertEqual(result.verification.status, "LOCAL_VERIFIED")
            bundle = load_bundle(result.bundle_path)
            self.assertEqual(bundle["schema_version"], "apr.proof-bundle.v1")
            self.assertEqual(bundle["provider"]["provider"], "fixture")
            self.assertEqual(bundle["mission"]["manifest_hash"], bundle["events"][0]["input"]["manifest_hash"])
            self.assertEqual(len(bundle["acceptance"]["checks"]), 6)
            self.assertEqual(bundle["verification"]["claimed_status"], "LOCAL_VERIFIED")

    def test_fixture_reproducibility_covers_artifacts_checks_and_provider_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = run_build_week_mission(EXAMPLE, Path(temporary) / "one")
            second = run_build_week_mission(EXAMPLE, Path(temporary) / "two")
            one = load_bundle(first.bundle_path)
            two = load_bundle(second.bundle_path)
            self.assertEqual(one["artifacts"], two["artifacts"])
            self.assertEqual(one["acceptance"], two["acceptance"])
            self.assertEqual(one["provider"], two["provider"])

    def test_independent_verifier_rejects_forged_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_build_week_mission(EXAMPLE, Path(temporary) / "run")
            bundle = load_bundle(result.bundle_path)
            bundle["acceptance"]["checks"][0]["passed"] = False
            bundle["integrity"]["bundle_hash"] = compute_bundle_hash(bundle)
            write_bundle(result.bundle_path, bundle)
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(any("independent reproduction" in error for error in verification.errors))

    def test_invalid_utf8_tampering_returns_failed_instead_of_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_build_week_mission(EXAMPLE, Path(temporary) / "run")
            artifact = result.output_dir / "artifact" / "site" / "index.html"
            artifact.write_bytes(b"\xff\xfe")
            verification = verify_bundle(result.bundle_path)
            self.assertEqual(verification.status, "FAILED")
            self.assertTrue(verification.errors)

    def test_all_tamper_cases_fail_and_preserve_original(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            result = run_build_week_mission(EXAMPLE, Path(temporary) / "run")
            before = run_fingerprint(result.output_dir)
            for case in TAMPER_CASES:
                with self.subTest(case=case):
                    tampered = run_tamper_case(result.output_dir, case)
                    self.assertEqual(tampered["status"], "FAILED")
                    self.assertTrue(tampered["errors"])
                    self.assertTrue(tampered["original_preserved"])
            self.assertEqual(run_fingerprint(result.output_dir), before)
            self.assertTrue(verify_bundle(result.bundle_path).valid)


if __name__ == "__main__":
    unittest.main()
