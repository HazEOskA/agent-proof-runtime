from __future__ import annotations

import json
import shutil
import tempfile
import threading
import time
import unittest
from http import HTTPStatus
from http.client import HTTPConnection
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_proof_runtime.mission_control import (
    MAX_REQUEST_BYTES,
    MissionControlConfig,
    build_server,
)


DOCTOR_UNAVAILABLE = {
    "backend": "docker-gvisor",
    "available": False,
    "checks": [{"name": "docker", "passed": False, "detail": "not installed"}],
}
VALID = {
    "mission_type": "verified_website_build",
    "brief": "Create a dark landing page for an AI security company.",
}


class MissionStudioHttpTests(unittest.TestCase):
    def _post(self, url: str, value: object, token: str, content_type: str = "application/json"):
        return urlopen(
            Request(
                url,
                data=json.dumps(value).encode("utf-8"),
                headers={"Content-Type": content_type, "X-APR-Token": token},
                method="POST",
            ),
            timeout=5,
        )

    def test_security_polling_completion_and_existing_routes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            missions = root / "missions"
            missions.mkdir()
            shutil.copyfile(
                "examples/verified-website-build.json",
                missions / "verified-website-build.json",
            )
            with patch(
                "agent_proof_runtime.mission_control._doctor_summary",
                return_value=DOCTOR_UNAVAILABLE,
            ):
                server, control = build_server(
                    MissionControlConfig(missions, root / "runs", port=0)
                )
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_address[1]}"
                try:
                    with urlopen(base + "/health", timeout=5) as response:
                        self.assertEqual(response.status, HTTPStatus.OK)
                    with urlopen(base + "/api/state", timeout=5) as response:
                        state = json.loads(response.read())
                    self.assertTrue(state["ok"])

                    missing_token = Request(
                        base + "/api/studio/start",
                        data=json.dumps(VALID).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with self.assertRaises(HTTPError) as denied:
                        urlopen(missing_token, timeout=5)
                    self.assertEqual(denied.exception.code, HTTPStatus.FORBIDDEN)
                    denied.exception.read()
                    denied.exception.close()

                    with self.assertRaises(HTTPError) as wrong_token:
                        self._post(base + "/api/studio/start", VALID, "wrong-token")
                    self.assertEqual(wrong_token.exception.code, HTTPStatus.FORBIDDEN)
                    wrong_token.exception.read()
                    wrong_token.exception.close()

                    with self.assertRaises(HTTPError) as wrong_type:
                        self._post(
                            base + "/api/studio/start",
                            VALID,
                            control.csrf_token,
                            "text/plain",
                        )
                    self.assertEqual(
                        wrong_type.exception.code, HTTPStatus.UNSUPPORTED_MEDIA_TYPE
                    )
                    wrong_type.exception.read()
                    wrong_type.exception.close()

                    oversized = HTTPConnection(
                        "127.0.0.1", server.server_address[1], timeout=5
                    )
                    oversized.putrequest("POST", "/api/studio/start")
                    oversized.putheader("Content-Type", "application/json")
                    oversized.putheader("X-APR-Token", control.csrf_token)
                    oversized.putheader("Content-Length", str(MAX_REQUEST_BYTES + 1))
                    oversized.endheaders()
                    oversized_response = oversized.getresponse()
                    oversized_response.read()
                    self.assertEqual(
                        oversized_response.status, HTTPStatus.BAD_REQUEST
                    )
                    oversized.close()

                    with self.assertRaises(HTTPError) as unknown_field:
                        self._post(
                            base + "/api/studio/start",
                            {**VALID, "extra": True},
                            control.csrf_token,
                        )
                    self.assertEqual(unknown_field.exception.code, HTTPStatus.BAD_REQUEST)
                    unknown_field.exception.read()
                    unknown_field.exception.close()

                    with self.assertRaises(HTTPError) as browser_key:
                        self._post(
                            base + "/api/studio/start",
                            {**VALID, "api_key": "browser-key-is-forbidden"},
                            control.csrf_token,
                        )
                    self.assertEqual(browser_key.exception.code, HTTPStatus.BAD_REQUEST)
                    browser_key.exception.read()
                    browser_key.exception.close()

                    with self.assertRaises(HTTPError) as invalid_id:
                        urlopen(base + "/api/studio/../bad", timeout=5)
                    self.assertIn(
                        invalid_id.exception.code,
                        {HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND},
                    )
                    invalid_id.exception.read()
                    invalid_id.exception.close()
                    with self.assertRaises(HTTPError) as missing:
                        urlopen(base + "/api/studio/studio-" + "0" * 32, timeout=5)
                    self.assertEqual(missing.exception.code, HTTPStatus.NOT_FOUND)
                    missing.exception.read()
                    missing.exception.close()

                    with self._post(
                        base + "/api/studio/start", VALID, control.csrf_token
                    ) as response:
                        self.assertEqual(response.status, HTTPStatus.CREATED)
                        created = json.loads(response.read())
                    session_id = created["session"]["session_id"]
                    deadline = time.monotonic() + 8
                    session = created["session"]
                    while session["state"] not in {"completed", "failed"}:
                        self.assertLess(time.monotonic(), deadline)
                        time.sleep(0.05)
                        with urlopen(
                            base + "/api/studio/" + session_id, timeout=5
                        ) as response:
                            session = json.loads(response.read())["session"]
                    self.assertEqual(session["state"], "completed")
                    self.assertEqual(session["provider"], "fixture")
                    self.assertIsNotNone(session["apr_run_id"])
                    self.assertEqual(session["mission_status"], "PASSED")
                    self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
                    self.assertEqual(session["anchor_status"], "UNANCHORED")
                    artifact_base = base + "/runs/" + session["apr_run_id"] + "/artifact/site/"
                    with urlopen(artifact_base + "index.html", timeout=5) as response:
                        self.assertEqual(response.status, HTTPStatus.OK)
                        artifact_csp = response.headers["Content-Security-Policy"]
                        self.assertIn("style-src 'self' 'unsafe-inline'", artifact_csp)
                        self.assertIn("sandbox allow-same-origin", artifact_csp)
                    with urlopen(artifact_base + "styles.css", timeout=5) as response:
                        self.assertEqual(response.status, HTTPStatus.OK)
                        self.assertEqual(
                            response.headers.get_content_type(), "text/css"
                        )
                    event_types = [item["type"] for item in session["events"]]
                    for expected in (
                        "studio.mission_accepted",
                        "agent.planner.completed",
                        "handoff.planner_to_research",
                        "agent.research.completed",
                        "handoff.research_to_content",
                        "agent.content.completed",
                        "handoff.content_to_html_builder",
                        "agent.html_builder.completed",
                        "handoff.html_builder_to_css_builder",
                        "agent.css_builder.completed",
                        "handoff.css_builder_to_data_builder",
                        "agent.data_builder.completed",
                        "handoff.data_builder_to_qa",
                        "agent.qa.completed",
                        "handoff.qa_to_apr",
                        "apr.run.started",
                        "apr.run.completed",
                        "verifier.completed",
                    ):
                        self.assertIn(expected, event_types)

                    run_body = {"mission_path": "verified-website-build.json"}
                    with self._post(
                        base + "/api/runs", run_body, control.csrf_token
                    ) as response:
                        self.assertEqual(response.status, HTTPStatus.CREATED)
                        ordinary = json.loads(response.read())["run"]
                    with self._post(
                        base + "/api/verify",
                        {"run_id": ordinary["run_id"]},
                        control.csrf_token,
                    ) as response:
                        verified = json.loads(response.read())["run"]
                    self.assertEqual(verified["proof_status"], "LOCAL_VERIFIED")
                    with self._post(
                        base + "/api/tamper",
                        {"run_id": ordinary["run_id"], "case": "artifact"},
                        control.csrf_token,
                    ) as response:
                        tampered = json.loads(response.read())["result"]
                    self.assertEqual(tampered["status"], "FAILED")
                    with urlopen(
                        base + "/api/runs/" + ordinary["run_id"], timeout=5
                    ) as response:
                        detail = json.loads(response.read())
                    self.assertTrue(detail["ok"])
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
