from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESOURCE_PATH = "agent_proof_runtime/data/verified-website-build.json"


class MissionStudioPackagingTests(unittest.TestCase):
    def test_built_wheel_contains_manifest_and_completes_packaged_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            shutil.copytree(
                PROJECT_ROOT,
                source,
                ignore=shutil.ignore_patterns(
                    ".git",
                    ".runs",
                    "__pycache__",
                    "*.pyc",
                    "*.egg-info",
                    "build",
                    "dist",
                ),
            )
            wheel_dir = root / "wheel"
            wheel_dir.mkdir()
            build = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "wheel",
                    "--no-deps",
                    "--wheel-dir",
                    str(wheel_dir),
                    str(source),
                ],
                cwd=root,
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            wheels = list(wheel_dir.glob("*.whl"))
            self.assertEqual(len(wheels), 1)
            wheel = wheels[0]

            with zipfile.ZipFile(wheel) as archive:
                self.assertIn(RESOURCE_PATH, archive.namelist())
                self.assertEqual(
                    json.loads(archive.read(RESOURCE_PATH)),
                    json.loads(
                        (source / "examples" / "verified-website-build.json").read_bytes()
                    ),
                )

            run_root = root / "packaged-run"
            run_root.mkdir()
            script = textwrap.dedent(
                """
                import json
                import sys
                import time
                from pathlib import Path

                wheel = sys.argv[1]
                root = Path(sys.argv[2])
                sys.path.insert(0, wheel)

                import agent_proof_runtime
                from agent_proof_runtime.mission_control import MissionControl, MissionControlConfig

                control = MissionControl(
                    MissionControlConfig(root / "missions", root / "runs")
                )
                session = control.start_studio(
                    {
                        "mission_type": "verified_website_build",
                        "brief": "Create a packaged dark landing page for an AI security company.",
                    }
                )
                deadline = time.monotonic() + 8
                while session["state"] not in {"completed", "failed"}:
                    if time.monotonic() >= deadline:
                        raise AssertionError("packaged Mission Studio session timed out")
                    time.sleep(0.02)
                    session = control.studio(session["session_id"])

                event_types = [event["type"] for event in session["events"]]
                expected = [
                    "studio.mission_accepted",
                    "agent.planner.started",
                    "agent.planner.completed",
                    "handoff.planner_to_research",
                    "agent.research.started",
                    "agent.research.completed",
                    "handoff.research_to_builder",
                    "agent.builder.started",
                    "agent.builder.completed",
                    "handoff.builder_to_qa",
                    "agent.qa.started",
                    "agent.qa.completed",
                    "handoff.qa_to_apr",
                    "apr.run.started",
                    "apr.contract_enforced",
                    "apr.run.completed",
                    "verifier.completed",
                ]
                assert event_types == expected, event_types
                assert session["mission_status"] == "PASSED", session
                assert session["proof_status"] == "LOCAL_VERIFIED", session
                assert session["anchor_status"] == "UNANCHORED", session
                assert wheel in agent_proof_runtime.__file__, agent_proof_runtime.__file__
                print(
                    json.dumps(
                        {
                            "module_file": agent_proof_runtime.__file__,
                            "event_count": len(event_types),
                            "contract_enforced": "apr.contract_enforced" in event_types,
                            "mission_status": session["mission_status"],
                            "proof_status": session["proof_status"],
                            "anchor_status": session["anchor_status"],
                        }
                    )
                )
                """
            )
            packaged = subprocess.run(
                [sys.executable, "-c", script, str(wheel), str(run_root)],
                cwd=run_root,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            self.assertEqual(
                packaged.returncode, 0, packaged.stdout + packaged.stderr
            )
            result = json.loads(packaged.stdout)
            self.assertEqual(result["event_count"], 17)
            self.assertTrue(result["contract_enforced"])
            self.assertEqual(result["mission_status"], "PASSED")
            self.assertEqual(result["proof_status"], "LOCAL_VERIFIED")
            self.assertEqual(result["anchor_status"], "UNANCHORED")


if __name__ == "__main__":
    unittest.main()
