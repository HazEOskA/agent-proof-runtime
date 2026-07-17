from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_proof_runtime.build_week_runtime import (
    run_build_week_mission,
    validate_proposal,
)
from agent_proof_runtime.canonical import hash_json
from agent_proof_runtime.mission_studio import (
    ARTIFACT_PATHS,
    MEDIA_TYPES,
    MissionStudioFixtureProvider,
    MissionStudioManager,
    MissionStudioRequest,
    MissionStudioValidationError,
)
from agent_proof_runtime.mission_v1 import load_build_week_mission
from agent_proof_runtime.tamper_lab import run_fingerprint
from agent_proof_runtime.validator import verify_bundle


MANIFEST = Path("examples/verified-website-build.json")
VALID = {
    "mission_type": "verified_website_build",
    "brief": "Create a dark landing page for an AI security company.",
}


class MissionStudioRequestTests(unittest.TestCase):
    def test_exact_request_keys_are_accepted_and_whitespace_is_normalized(self) -> None:
        request = MissionStudioRequest.parse(
            {
                "mission_type": "verified_website_build",
                "brief": "  Create\r\n a\t dark   verified website.  ",
            }
        )
        self.assertEqual(request.brief, "Create a dark verified website.")
        self.assertEqual(
            request.to_dict(),
            {
                "mission_type": "verified_website_build",
                "brief": "Create a dark verified website.",
                "provider": "fixture",
            },
        )

    def test_unknown_and_missing_fields_are_rejected(self) -> None:
        for value in (
            {**VALID, "extra": True},
            {**VALID, "api_key": "never-accepted"},
            {"mission_type": "verified_website_build"},
            {"brief": VALID["brief"]},
            [],
        ):
            with self.subTest(value=value):
                with self.assertRaises(MissionStudioValidationError):
                    MissionStudioRequest.parse(value)

    def test_invalid_mission_type_and_non_string_brief_are_rejected(self) -> None:
        with self.assertRaises(MissionStudioValidationError):
            MissionStudioRequest.parse({**VALID, "mission_type": "arbitrary"})
        with self.assertRaises(MissionStudioValidationError):
            MissionStudioRequest.parse({**VALID, "brief": 123})
        with self.assertRaises(MissionStudioValidationError):
            MissionStudioRequest.parse({**VALID, "provider": "other"})

    def test_provider_defaults_to_fixture_and_explicit_modes_are_supported(self) -> None:
        implicit = MissionStudioRequest.parse(VALID)
        fixture = MissionStudioRequest.parse({**VALID, "provider": "fixture"})
        live = MissionStudioRequest.parse({**VALID, "provider": "openai"})
        self.assertEqual(implicit.provider, "fixture")
        self.assertEqual(fixture.provider, "fixture")
        self.assertEqual(live.provider, "openai")

    def test_blank_short_oversized_nul_and_controls_are_rejected(self) -> None:
        invalid_briefs = (
            "",
            "short",
            "x" * 2001,
            "A valid-looking brief\x00with NUL",
            "A valid-looking brief\x08with control",
            "A valid-looking brief\x7fwith delete",
        )
        for brief in invalid_briefs:
            with self.subTest(brief=repr(brief[:30])):
                with self.assertRaises(MissionStudioValidationError):
                    MissionStudioRequest.parse({**VALID, "brief": brief})


class MissionStudioProviderTests(unittest.TestCase):
    def test_provider_is_deterministic_and_matches_the_exact_contract(self) -> None:
        first_request = MissionStudioRequest.parse(VALID)
        second_request = MissionStudioRequest.parse(
            {**VALID, "brief": " Create  a dark landing page for an AI security company. "}
        )
        first = MissionStudioFixtureProvider(first_request)
        second = MissionStudioFixtureProvider(second_request)
        self.assertEqual(first.proposal.to_dict(), second.proposal.to_dict())
        self.assertEqual(first.stages, second.stages)
        self.assertEqual(first.handoffs, second.handoffs)
        self.assertEqual(
            tuple(artifact.path for artifact in first.proposal.artifacts),
            ARTIFACT_PATHS,
        )
        self.assertEqual(len(first.proposal.artifacts), 4)
        self.assertEqual(
            tuple(artifact.media_type for artifact in first.proposal.artifacts),
            tuple(MEDIA_TYPES[path] for path in ARTIFACT_PATHS),
        )
        self.assertEqual(
            [stage["stage_id"] for stage in first.stages],
            ["planner", "research", "builder", "qa"],
        )
        self.assertEqual(
            [handoff["destination_stage"] for handoff in first.handoffs],
            ["research", "builder", "qa", "apr"],
        )
        for stage in first.stages:
            self.assertEqual(stage["output_hash"], hash_json(stage["output"]))

        trace = json.loads(first.proposal.artifacts[3].content)
        self.assertNotIn("timestamp", json.dumps(trace))
        self.assertNotIn("session_id", json.dumps(trace))

    def test_user_html_and_script_text_are_escaped(self) -> None:
        request = MissionStudioRequest.parse(
            {
                **VALID,
                "brief": "Create a website for <script>alert('x')</script> & partners.",
            }
        )
        provider = MissionStudioFixtureProvider(request)
        index = provider.proposal.artifacts[0].content
        self.assertNotIn("<script>", index)
        self.assertIn("&lt;script&gt;alert(&#x27;x&#x27;)&lt;/script&gt;", index)
        self.assertIn("&amp; partners", index)
        self.assertNotIn("javascript:", index.lower())

    def test_provider_passes_existing_proposal_validation_without_api_key(self) -> None:
        mission = load_build_week_mission(MANIFEST)
        provider = MissionStudioFixtureProvider(MissionStudioRequest.parse(VALID))
        with patch.dict(os.environ, {}, clear=True):
            result = provider.propose(mission)
            validate_proposal(mission, result.proposal)
        self.assertEqual(result.metadata["provider"], "fixture")

    def test_fixture_run_uses_no_shell_or_subprocess(self) -> None:
        mission = load_build_week_mission(MANIFEST)
        provider = MissionStudioFixtureProvider(MissionStudioRequest.parse(VALID))
        with tempfile.TemporaryDirectory() as temporary:
            with (
                patch.object(subprocess, "run") as run,
                patch.object(subprocess, "Popen") as popen,
                patch.object(subprocess, "check_output") as check_output,
                patch.dict(os.environ, {}, clear=True),
            ):
                result = run_build_week_mission(
                    mission,
                    Path(temporary) / "run",
                    provider_name="fixture",
                    provider=provider,
                )
            run.assert_not_called()
            popen.assert_not_called()
            check_output.assert_not_called()
            self.assertEqual(result.verification.status, "LOCAL_VERIFIED")


class MissionStudioIntegrationTests(unittest.TestCase):
    def _tamper_copy(self, run_dir: Path, relative: str, root: Path) -> str:
        copy = root / (relative.replace("/", "-") + "-copy")
        shutil.copytree(run_dir, copy)
        with (copy / "artifact" / Path(relative)).open("ab") as handle:
            handle.write(b"\nTAMPERED\n")
        return verify_bundle(copy / "proof-bundle.json").status

    def test_complete_run_proof_tamper_and_original_preservation(self) -> None:
        mission = load_build_week_mission(MANIFEST)
        provider = MissionStudioFixtureProvider(MissionStudioRequest.parse(VALID))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run_dir = root / "original"
            with patch.dict(os.environ, {}, clear=True):
                result = run_build_week_mission(
                    mission,
                    run_dir,
                    provider_name="fixture",
                    provider=provider,
                )
            self.assertEqual(result.mission_status, "PASSED")
            self.assertEqual(result.verification.status, "LOCAL_VERIFIED")
            self.assertEqual(result.verification.anchor_status, "UNANCHORED")
            bundle = json.loads(result.bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(
                {item["path"] for item in bundle["artifacts"]},
                {"artifact/" + path for path in ARTIFACT_PATHS},
            )
            self.assertEqual(len(list((run_dir / "artifact").rglob("*.*"))), 4)
            before = run_fingerprint(run_dir)
            self.assertEqual(
                self._tamper_copy(run_dir, "site/index.html", root), "FAILED"
            )
            self.assertEqual(
                self._tamper_copy(run_dir, "studio/trace.json", root), "FAILED"
            )
            self.assertEqual(run_fingerprint(run_dir), before)
            self.assertEqual(
                verify_bundle(run_dir / "proof-bundle.json").status,
                "LOCAL_VERIFIED",
            )
            persisted = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in sorted(run_dir.rglob("*"))
                if path.is_file()
            )
            self.assertNotIn("sk-", persisted)
            self.assertNotIn("OPENAI_API_KEY=", persisted)
            self.assertNotIn(str(Path.cwd().resolve()), persisted)
            self.assertNotIn("chain-of-thought", persisted.casefold())
            self.assertNotIn("raw_model_response", persisted.casefold())


class MissionStudioFailureTests(unittest.TestCase):
    def test_failure_event_exposes_only_a_safe_operator_category(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            manager = MissionStudioManager(
                runs_dir=Path(temporary) / "runs",
                run_lock=threading.Lock(),
                stage_delay_seconds=0,
            )
            with patch(
                "agent_proof_runtime.mission_studio.resources.files",
                side_effect=FileNotFoundError("C:\\sensitive\\absolute\\manifest.json"),
            ):
                created = manager.start(VALID)
                session = created
                deadline = time.monotonic() + 3
                while session["state"] not in {"completed", "failed"}:
                    self.assertLess(time.monotonic(), deadline)
                    time.sleep(0.01)
                    session = manager.get(created["session_id"])

            self.assertEqual(session["state"], "failed")
            self.assertEqual(session["proof_status"], "FAILED")
            self.assertEqual(session["failure_category"], "manifest_unavailable")
            failure = session["events"][-1]
            self.assertEqual(
                failure,
                {
                    "id": failure["id"],
                    "type": "studio.mission_failed",
                    "timestamp": failure["timestamp"],
                    "category": "manifest_unavailable",
                },
            )
            serialized = json.dumps(session)
            self.assertNotIn("FileNotFoundError", serialized)
            self.assertNotIn("C:\\\\sensitive", serialized)
            self.assertNotIn("Traceback", serialized)


if __name__ == "__main__":
    unittest.main()
