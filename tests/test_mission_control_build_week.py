from __future__ import annotations

import json
import os
import tempfile
import threading
import unittest
from http import HTTPStatus
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_proof_runtime.mission_control import (
    MissionControl,
    MissionControlConfig,
    MissionControlError,
    build_server,
)
from agent_proof_runtime.tamper_lab import run_fingerprint
from agent_proof_runtime.validator import verify_bundle


DOCTOR_UNAVAILABLE = {
    "backend": "docker-gvisor",
    "available": False,
    "checks": [{"name": "docker", "passed": False, "detail": "not installed"}],
}


def copy_manifest(destination: Path, *, provider: str = "fixture") -> None:
    destination.mkdir(parents=True, exist_ok=True)
    value = json.loads(Path("examples/build-week-mission.json").read_text(encoding="utf-8"))
    value["provider"] = provider
    (destination / "build-week.json").write_text(
        json.dumps(value, ensure_ascii=False), encoding="utf-8"
    )


class MissionControlBuildWeekTests(unittest.TestCase):
    def test_fixture_run_detail_and_all_tamper_cases_preserve_original(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_manifest(root / "missions")
            control = MissionControl(
                MissionControlConfig(root / "missions", root / "runs", port=0)
            )
            run = control.run("build-week.json")
            detail = control.detail(run["run_id"])
            self.assertEqual(detail["summary"]["provider"], "fixture")
            self.assertEqual(detail["evidence"]["schema_version"], "apr.proof-bundle.v1")
            run_dir = root / "runs" / run["run_id"]
            before = run_fingerprint(run_dir)
            for case in ("artifact", "event", "metadata"):
                result = control.tamper(run["run_id"], case)
                self.assertEqual(result["status"], "FAILED")
                self.assertTrue(result["original_preserved"])
            self.assertEqual(run_fingerprint(run_dir), before)
            self.assertTrue(verify_bundle(run_dir / "proof-bundle.json").valid)

    def test_openai_mission_without_key_returns_service_unavailable_and_no_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_manifest(root / "missions", provider="openai")
            control = MissionControl(
                MissionControlConfig(root / "missions", root / "runs", port=0)
            )
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(MissionControlError) as caught:
                    control.run("build-week.json")
            self.assertEqual(caught.exception.status, HTTPStatus.SERVICE_UNAVAILABLE)
            self.assertFalse((root / "runs").exists() and any((root / "runs").iterdir()))

    def test_health_detail_and_tamper_http_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            copy_manifest(root / "missions")
            with patch(
                "agent_proof_runtime.mission_control._doctor_summary",
                return_value=DOCTOR_UNAVAILABLE,
            ):
                server, control = build_server(
                    MissionControlConfig(root / "missions", root / "runs", port=0)
                )
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_address[1]}"
                try:
                    with urlopen(base + "/health", timeout=5) as response:
                        health = json.loads(response.read())
                    self.assertEqual(health["status"], "healthy")

                    run = control.run("build-week.json")
                    with urlopen(base + "/api/runs/" + run["run_id"], timeout=5) as response:
                        detail = json.loads(response.read())
                    self.assertEqual(detail["evidence"]["provider"]["provider"], "fixture")

                    body = json.dumps(
                        {"run_id": run["run_id"], "case": "metadata"}
                    ).encode("utf-8")
                    request = Request(
                        base + "/api/tamper",
                        data=body,
                        headers={
                            "Content-Type": "application/json",
                            "X-APR-Token": control.csrf_token,
                        },
                        method="POST",
                    )
                    with urlopen(request, timeout=5) as response:
                        tampered = json.loads(response.read())
                    self.assertEqual(tampered["result"]["status"], "FAILED")
                    self.assertTrue(tampered["result"]["original_preserved"])
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
