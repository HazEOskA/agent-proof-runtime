from __future__ import annotations

import json
import shutil
import tempfile
import threading
import unittest
from http import HTTPStatus
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_proof_runtime.mission_control import (
    MissionControl,
    MissionControlConfig,
    MissionControlError,
    build_server,
    discover_missions,
    discover_runs,
)


DOCTOR_UNAVAILABLE = {
    "backend": "docker-gvisor",
    "available": False,
    "checks": [
        {"name": "docker_executable", "passed": False, "detail": "not found"},
        {"name": "runsc_runtime", "passed": False, "detail": "not checked"},
    ],
}


def _copy_demo(destination: Path) -> None:
    destination.mkdir(parents=True)
    shutil.copyfile("missions/demo.json", destination / "demo.json")


class MissionControlStateTests(unittest.TestCase):
    def test_discovers_and_runs_existing_mission_spec(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions = root / "missions"
            runs = root / "runs"
            _copy_demo(missions)
            control = MissionControl(
                MissionControlConfig(missions_dir=missions, runs_dir=runs, port=0)
            )

            with patch(
                "agent_proof_runtime.mission_control._doctor_summary",
                return_value=DOCTOR_UNAVAILABLE,
            ):
                initial = control.state()
            self.assertEqual(initial["missions"][0]["mission_id"], "builtin-demo")
            self.assertEqual(initial["runs"], [])

            result = control.run("demo.json")
            self.assertEqual(result["mission_status"], "PASSED")
            self.assertEqual(result["proof_status"], "LOCAL_VERIFIED")
            self.assertEqual(result["anchor_status"], "UNANCHORED")
            self.assertEqual(len(discover_runs(runs)), 1)

            verified = control.verify(result["run_id"])
            self.assertEqual(verified["proof_status"], "LOCAL_VERIFIED")
            self.assertEqual(
                control.public_file(f"/runs/{result['run_id']}/report.html").name,
                "report.html",
            )
            artifact = control.public_file(
                f"/runs/{result['run_id']}/artifact/hello.txt"
            ).read_text(encoding="utf-8")
            self.assertIn("sandbox run completed", artifact)

    def test_remote_bind_requires_explicit_operator_choice(self) -> None:
        with self.assertRaisesRegex(MissionControlError, "non-loopback"):
            MissionControl(
                MissionControlConfig(
                    missions_dir=Path("missions"),
                    runs_dir=Path(".runs"),
                    host="0.0.0.0",
                )
            )

    def test_manifest_path_escape_and_symlink_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions = root / "missions"
            missions.mkdir()
            outside = root / "outside.json"
            shutil.copyfile("missions/demo.json", outside)
            (missions / "linked.json").symlink_to(outside)
            control = MissionControl(
                MissionControlConfig(missions_dir=missions, runs_dir=root / "runs")
            )

            with self.assertRaisesRegex(MissionControlError, "canonical relative"):
                control.run("../outside.json")
            with self.assertRaisesRegex(MissionControlError, "symbolic links"):
                control.run("linked.json")
            self.assertEqual(discover_missions(missions), [])

    def test_public_files_are_strictly_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            run = root / "runs" / "valid-run"
            run.mkdir(parents=True)
            (run / "proof-bundle.json").write_text("{}", encoding="utf-8")
            secret = run / "secret.txt"
            secret.write_text("not public", encoding="utf-8")
            control = MissionControl(
                MissionControlConfig(missions_dir=root / "missions", runs_dir=root / "runs")
            )
            with self.assertRaisesRegex(MissionControlError, "file not found"):
                control.public_file("/runs/valid-run/secret.txt")
            with self.assertRaises(MissionControlError):
                control.public_file("/runs/valid-run/artifact/../../secret.txt")

    def test_corrupt_and_symlinked_bundles_do_not_break_history(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runs = root / "runs"
            corrupt = runs / "corrupt-run"
            corrupt.mkdir(parents=True)
            (corrupt / "proof-bundle.json").write_text(
                '{"run": []}', encoding="utf-8"
            )
            outside = root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            linked = runs / "linked-run"
            linked.mkdir()
            (linked / "proof-bundle.json").symlink_to(outside)

            history = discover_runs(runs)
            self.assertEqual(len(history), 2)
            self.assertTrue(all(item["proof_status"] == "FAILED" for item in history))
            linked_result = next(item for item in history if item["run_id"] == "linked-run")
            self.assertIn("symbolic link", linked_result["errors"][0])


class MissionControlHttpTests(unittest.TestCase):
    def test_dashboard_state_token_and_run_route(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions = root / "missions"
            _copy_demo(missions)
            with patch(
                "agent_proof_runtime.mission_control._doctor_summary",
                return_value=DOCTOR_UNAVAILABLE,
            ):
                server, control = build_server(
                    MissionControlConfig(
                        missions_dir=missions,
                        runs_dir=root / "runs",
                        port=0,
                    )
                )
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                port = server.server_address[1]
                base = f"http://127.0.0.1:{port}"
                try:
                    with urlopen(base + "/", timeout=5) as response:
                        document = response.read().decode("utf-8")
                        dashboard_csp = response.headers["Content-Security-Policy"]
                    self.assertIn("APR Mission Control", document)
                    self.assertIn(control.csrf_token, document)
                    self.assertIn("script-src 'unsafe-inline'", dashboard_csp)

                    with urlopen(base + "/api/state", timeout=5) as response:
                        state = json.loads(response.read())
                    self.assertTrue(state["ok"])
                    self.assertEqual(state["missions"][0]["mission_id"], "builtin-demo")

                    body = json.dumps({"mission_path": "demo.json"}).encode("utf-8")
                    missing_token = Request(
                        base + "/api/runs",
                        data=body,
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(HTTPError) as denied:
                        urlopen(missing_token, timeout=5)
                    self.assertEqual(denied.exception.code, HTTPStatus.FORBIDDEN)

                    wrong_type = Request(
                        base + "/api/runs",
                        data=body,
                        headers={
                            "Content-Type": "text/plain",
                            "X-APR-Token": control.csrf_token,
                        },
                        method="POST",
                    )
                    with self.assertRaises(HTTPError) as unsupported:
                        urlopen(wrong_type, timeout=5)
                    self.assertEqual(
                        unsupported.exception.code, HTTPStatus.UNSUPPORTED_MEDIA_TYPE
                    )

                    fake_run = {
                        "run_id": "fake-run",
                        "mission_id": "builtin-demo",
                        "proof_status": "LOCAL_VERIFIED",
                    }
                    authorized = Request(
                        base + "/api/runs",
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "X-APR-Token": control.csrf_token,
                        },
                        method="POST",
                    )
                    with patch.object(control, "run", return_value=fake_run) as run:
                        with urlopen(authorized, timeout=5) as response:
                            created = json.loads(response.read())
                            self.assertEqual(response.status, HTTPStatus.CREATED)
                    run.assert_called_once_with("demo.json")
                    self.assertEqual(created["run"], fake_run)

                    hostile = HTTPConnection("127.0.0.1", port, timeout=5)
                    hostile.request(
                        "GET", "/api/state", headers={"Host": "attacker.example"}
                    )
                    hostile_response = hostile.getresponse()
                    hostile_response.read()
                    hostile.close()
                    self.assertEqual(hostile_response.status, HTTPStatus.FORBIDDEN)

                    fake_run_dir = root / "runs" / "fake-run"
                    fake_run_dir.mkdir(parents=True)
                    (fake_run_dir / "report.html").write_text(
                        "<script>throw new Error('must not run')</script>",
                        encoding="utf-8",
                    )
                    with urlopen(base + "/runs/fake-run/report.html", timeout=5) as response:
                        response.read()
                        report_csp = response.headers["Content-Security-Policy"]
                    self.assertIn("script-src 'none'", report_csp)
                    self.assertIn("sandbox", report_csp)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
