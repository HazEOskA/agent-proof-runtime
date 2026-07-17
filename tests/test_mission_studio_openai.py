from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from agent_proof_runtime.mission_studio import MissionStudioManager
from agent_proof_runtime.mission_studio_openai import (
    ARTIFACT_LIMITS,
    MissionStudioOpenAIError,
    MissionStudioOpenAIProvider,
)
from agent_proof_runtime.mission_control_ui import render_mission_control
from agent_proof_runtime.tamper_lab import run_fingerprint
from agent_proof_runtime.validator import verify_bundle


VALID = {
    "mission_type": "verified_website_build",
    "brief": "Create a polished dark landing page for an AI security company.",
}
EXPECTED_EVENTS = [
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


def website_artifacts() -> list[dict[str, str]]:
    return [
        {
            "path": "site/index.html",
            "media_type": "text/html",
            "content": """<!doctype html>
<html lang="en" data-apr-build="verified-website-build-v1">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Aegis AI</title><link rel="stylesheet" href="styles.css"></head>
<body><main><section data-apr-section="hero"><h1>Secure every AI workflow</h1><a href="#contact">Start</a></section><section data-apr-section="features"><h2>Controls</h2><article><h3>Constrained</h3></article><article><h3>Recorded</h3></article><article><h3>Verified</h3></article></section><section id="contact" data-apr-section="cta"><h2>Build with evidence</h2></section></main></body></html>
""",
        },
        {
            "path": "site/styles.css",
            "media_type": "text/css",
            "content": "body{margin:0;background:#050609;color:#f4f7f8;font:16px Arial,sans-serif}main{width:min(1100px,calc(100% - 32px));margin:auto}section{padding:64px 0}article{padding:24px;border:1px solid #345}@media(max-width:700px){section{padding:40px 0}}\n",
        },
        {
            "path": "site/data.json",
            "media_type": "application/json",
            "content": json.dumps(
                {
                    "schema_version": "apr.verified-website-build.data.v1",
                    "product": "Aegis AI",
                    "features": ["Constrained", "Recorded", "Verified"],
                },
                separators=(",", ":"),
            )
            + "\n",
        },
    ]


def stage_outputs() -> list[dict]:
    artifacts = website_artifacts()
    qa_artifacts = [dict(artifact) for artifact in artifacts]
    qa_artifacts[1]["content"] += (
        ":focus-visible{outline:3px solid #7ff;outline-offset:3px}\n"
    )
    return [
        {
            "summary": "Planned the fixed static website delivery.",
            "site_type": "B2B landing page",
            "target_audience": "AI security teams",
            "primary_goal": "Generate qualified security reviews",
            "required_sections": ["hero", "features", "cta"],
            "content_priorities": ["clarity", "trust", "conversion"],
            "visual_priorities": ["dark", "precise", "responsive"],
            "constraints": ["static", "self-contained", "no JavaScript"],
        },
        {
            "summary": "Prepared model-based audience and design analysis.",
            "audience_insights": ["Needs technical credibility"],
            "visual_direction": "Dark editorial security interface",
            "typography_direction": "System sans-serif with strong hierarchy",
            "layout_direction": "Focused single-page narrative",
            "content_strategy": ["Lead with outcome", "Support with controls"],
            "accessibility_requirements": ["Semantic headings", "Visible focus"],
            "usability_requirements": ["Clear CTA", "Readable mobile layout"],
            "risks_to_avoid": ["Unsupported claims", "External dependencies"],
        },
        {
            "summary": "Built the complete three-file static website.",
            "artifacts": artifacts,
        },
        {
            "summary": "Reviewed and approved the corrected final artifacts.",
            "approved": True,
            "issues": [],
            "corrections_made": ["Added a visible keyboard focus treatment"],
            "artifacts": qa_artifacts,
        },
    ]


class FakeResponses:
    def __init__(self, outputs: list[object]) -> None:
        self.outputs = list(outputs)
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if not self.outputs:
            raise AssertionError("unexpected extra OpenAI call")
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        index = len(self.calls)
        return SimpleNamespace(
            id=f"resp_mock_stage_{index}",
            model="gpt-5.6-mocked",
            output_text=(output if isinstance(output, str) else json.dumps(output)),
            usage=SimpleNamespace(
                input_tokens=100 + index,
                output_tokens=50 + index,
                total_tokens=150 + index * 2,
            ),
            hidden_reasoning="must-never-persist",
            raw_sdk_response="must-never-persist",
        )


def fake_client(outputs: list[object] | None = None) -> tuple[object, FakeResponses]:
    responses = FakeResponses(outputs or stage_outputs())
    return SimpleNamespace(responses=responses), responses


def wait_for_session(manager: MissionStudioManager, created: dict) -> dict:
    session = created
    deadline = time.monotonic() + 8
    while session["state"] not in {"completed", "failed"}:
        if time.monotonic() >= deadline:
            raise AssertionError("Mission Studio session timed out")
        time.sleep(0.01)
        session = manager.get(created["session_id"])
    return session


class MissionStudioOpenAITests(unittest.TestCase):
    def _manager(self, root: Path, client: object | None) -> MissionStudioManager:
        return MissionStudioManager(
            runs_dir=root / "runs",
            run_lock=threading.Lock(),
            stage_delay_seconds=0,
            openai_client=client,
        )

    def test_fixture_modes_remain_deterministic_and_emit_17_events(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager_one = self._manager(root / "one", None)
            manager_two = self._manager(root / "two", None)
            first = wait_for_session(manager_one, manager_one.start(VALID))
            second = wait_for_session(
                manager_two, manager_two.start({**VALID, "provider": "fixture"})
            )
            self.assertEqual(first["provider"], "fixture")
            self.assertEqual(second["provider"], "fixture")
            self.assertEqual(
                [event["type"] for event in first["events"]], EXPECTED_EVENTS
            )
            self.assertEqual(
                [event["type"] for event in second["events"]], EXPECTED_EVENTS
            )
            self.assertEqual(
                [agent["output_hash"] for agent in first["agents"]],
                [agent["output_hash"] for agent in second["agents"]],
            )

    def test_mocked_four_stage_success_reaches_existing_apr_proof_path(self) -> None:
        marker = "sk-test-live-pipeline-must-never-persist"
        client, responses = fake_client()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = self._manager(root, client)
            with patch.dict(
                os.environ,
                {"OPENAI_API_KEY": marker, "APR_OPENAI_MODEL": "gpt-5.6"},
                clear=True,
            ):
                session = wait_for_session(
                    manager,
                    manager.start({**VALID, "provider": "openai"}),
                )

            self.assertEqual(len(responses.calls), 4)
            self.assertEqual(
                [call["text"]["format"]["name"] for call in responses.calls],
                [
                    "apr_mission_studio_planner_v1",
                    "apr_mission_studio_research_v1",
                    "apr_mission_studio_builder_v1",
                    "apr_mission_studio_qa_v1",
                ],
            )
            for call in responses.calls:
                self.assertEqual(call["model"], "gpt-5.6")
                self.assertIs(call["store"], False)
                self.assertEqual(call["tools"], [])
                self.assertEqual(call["text"]["format"]["type"], "json_schema")
                self.assertIs(call["text"]["format"]["strict"], True)
                self.assertNotIn("reasoning", call)
            research_input = json.loads(responses.calls[1]["input"])
            builder_input = json.loads(responses.calls[2]["input"])
            qa_input = json.loads(responses.calls[3]["input"])
            self.assertIn("planner", research_input)
            self.assertIn("research", builder_input)
            self.assertEqual(
                [item["path"] for item in qa_input["builder"]["artifacts"]],
                [item["path"] for item in website_artifacts()],
            )

            self.assertEqual(
                [event["type"] for event in session["events"]], EXPECTED_EVENTS
            )
            self.assertEqual(session["provider"], "openai")
            self.assertEqual(session["mission_status"], "PASSED")
            self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
            self.assertEqual(session["anchor_status"], "UNANCHORED")
            run_dir = root / "runs" / session["apr_run_id"]
            bundle_path = run_dir / "proof-bundle.json"
            bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
            self.assertEqual(bundle["provider"]["provider"], "openai")
            self.assertEqual(bundle["acceptance"]["status"], "PASSED")
            self.assertEqual(
                sum(check["passed"] for check in bundle["acceptance"]["checks"]), 16
            )
            self.assertEqual(len(bundle["artifacts"]), 4)
            self.assertEqual(
                {item["path"] for item in bundle["artifacts"]},
                {
                    "artifact/site/index.html",
                    "artifact/site/styles.css",
                    "artifact/site/data.json",
                    "artifact/studio/trace.json",
                },
            )
            trace = json.loads(
                (run_dir / "artifact" / "studio" / "trace.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(trace["provider"], "openai")
            self.assertEqual(len(trace["stages"]), 4)
            self.assertEqual(
                [stage["response_id"] for stage in trace["stages"]],
                [f"resp_mock_stage_{index}" for index in range(1, 5)],
            )
            self.assertEqual(
                [stage["token_usage"] for stage in trace["stages"]],
                [
                    {
                        "input_tokens": 100 + index,
                        "output_tokens": 50 + index,
                        "total_tokens": 150 + index * 2,
                    }
                    for index in range(1, 5)
                ],
            )
            self.assertEqual(len(trace["handoffs"]), 4)
            self.assertEqual(len(trace["artifacts"]), 3)
            for event in session["events"]:
                if event["type"] in {"agent.builder.completed", "agent.qa.completed"}:
                    self.assertNotIn("artifacts", event["structured_output"])
            serialized_session = json.dumps(session)
            self.assertNotIn("Generate qualified security reviews", serialized_session)
            self.assertNotIn("Needs technical credibility", serialized_session)
            self.assertIn(
                ":focus-visible",
                (run_dir / "artifact" / "site" / "styles.css").read_text(
                    encoding="utf-8"
                ),
            )

            before = run_fingerprint(run_dir)
            for relative in ("site/index.html", "studio/trace.json"):
                copy = root / (relative.replace("/", "-") + "-tampered")
                shutil.copytree(run_dir, copy)
                with (copy / "artifact" / Path(relative)).open("ab") as handle:
                    handle.write(b"\nTAMPERED\n")
                self.assertEqual(
                    verify_bundle(copy / "proof-bundle.json").status, "FAILED"
                )
            self.assertEqual(run_fingerprint(run_dir), before)
            self.assertEqual(verify_bundle(bundle_path).status, "LOCAL_VERIFIED")

            persisted = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in sorted(run_dir.rglob("*"))
                if path.is_file()
            )
            self.assertNotIn(marker, persisted)
            self.assertNotIn("must-never-persist", persisted)
            self.assertNotIn("hidden_reasoning", persisted)
            self.assertNotIn("raw_sdk_response", persisted)
            self.assertNotIn("OPENAI_API_KEY=", persisted)
            self.assertNotIn("environment variables", persisted.casefold())
            self.assertNotIn(str(root.resolve()), persisted)
            self.assertNotIn("Traceback", persisted)

    def test_absent_server_key_fails_closed_without_apr(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            manager = self._manager(root, None)
            with patch.dict(os.environ, {}, clear=True):
                session = wait_for_session(
                    manager,
                    manager.start({**VALID, "provider": "openai"}),
                )
            self.assertEqual(session["state"], "failed")
            self.assertEqual(session["failure_category"], "openai_key_absent")
            self.assertEqual(session["agents"][0]["status"], "failed")
            self.assertEqual(session["events"][-1]["type"], "studio.mission_failed")
            self.assertEqual(
                session["events"][-1]["category"], "openai_key_absent"
            )
            self.assertNotIn("apr.run.started", [e["type"] for e in session["events"]])
            self.assertIsNone(session["apr_run_id"])
            self.assertFalse((root / "runs").exists())

    def test_missing_optional_sdk_has_a_safe_category(self) -> None:
        with patch.dict(os.environ, {"OPENAI_API_KEY": "server-only"}, clear=True):
            with patch.dict(sys.modules, {"openai": None}):
                provider = MissionStudioOpenAIProvider(
                    SimpleNamespace(**{**VALID, "provider": "openai"})
                )
                with self.assertRaises(MissionStudioOpenAIError) as raised:
                    provider.run_stage("planner")
        self.assertEqual(raised.exception.category, "openai_sdk_unavailable")

    def test_malformed_duplicate_and_request_errors_are_safely_categorized(self) -> None:
        for output in ("not json", '{"summary":"one","summary":"two"}'):
            with self.subTest(output=output):
                client, _ = fake_client([output])
                provider = MissionStudioOpenAIProvider(
                    SimpleNamespace(**{**VALID, "provider": "openai"}), client=client
                )
                with self.assertRaises(MissionStudioOpenAIError) as raised:
                    provider.run_stage("planner")
                self.assertEqual(raised.exception.category, "structured_output_invalid")

        unsafe_output = dict(stage_outputs()[0])
        unsafe_output["summary"] = "Traceback (most recent call last): C:\\private\\run"
        client, _ = fake_client([unsafe_output])
        provider = MissionStudioOpenAIProvider(
            SimpleNamespace(**{**VALID, "provider": "openai"}), client=client
        )
        with self.assertRaises(MissionStudioOpenAIError) as unsafe:
            provider.run_stage("planner")
        self.assertEqual(unsafe.exception.category, "stage_contract_rejected")

        client, _ = fake_client(
            [RuntimeError("sk-secret C:\\private\\trace raw response body")]
        )
        with tempfile.TemporaryDirectory() as temporary:
            manager = self._manager(Path(temporary), client)
            session = wait_for_session(
                manager,
                manager.start({**VALID, "provider": "openai"}),
            )
        serialized = json.dumps(session)
        self.assertEqual(session["failure_category"], "openai_request_failed")
        self.assertNotIn("sk-secret", serialized)
        self.assertNotIn("C:\\\\private", serialized)
        self.assertNotIn("RuntimeError", serialized)

    def test_timeout_has_a_safe_category(self) -> None:
        client, _ = fake_client([TimeoutError("secret timeout details")])
        provider = MissionStudioOpenAIProvider(
            SimpleNamespace(**{**VALID, "provider": "openai"}), client=client
        )
        with self.assertRaises(MissionStudioOpenAIError) as raised:
            provider.run_stage("planner")
        self.assertEqual(raised.exception.category, "openai_timeout")

    def test_bad_builder_artifact_contracts_are_rejected_before_qa_or_apr(self) -> None:
        valid = website_artifacts()
        cases: dict[str, list[dict[str, str]]] = {
            "wrong_path": [{**valid[0], "path": "site/other.html"}, *valid[1:]],
            "extra": [*valid, {**valid[2], "path": "site/extra.json"}],
            "missing": valid[:2],
            "wrong_media": [{**valid[0], "media_type": "text/plain"}, *valid[1:]],
            "oversized": [
                valid[0],
                {**valid[1], "content": "x" * (ARTIFACT_LIMITS["site/styles.css"] + 1)},
                valid[2],
            ],
            "executable_html": [
                {
                    **valid[0],
                    "content": valid[0]["content"].replace(
                        "<main>", '<main onmouseover="alert(1)">'
                    ),
                },
                *valid[1:],
            ],
            "external_css": [
                valid[0],
                {
                    **valid[1],
                    "content": valid[1]["content"]
                    + "@import url(https://example.invalid/site.css);",
                },
                valid[2],
            ],
        }
        base = stage_outputs()
        for name, artifacts in cases.items():
            with self.subTest(name=name):
                outputs = [base[0], base[1], {"summary": "bad", "artifacts": artifacts}]
                client, responses = fake_client(outputs)
                provider = MissionStudioOpenAIProvider(
                    SimpleNamespace(**{**VALID, "provider": "openai"}), client=client
                )
                provider.run_stage("planner")
                provider.run_stage("research")
                with self.assertRaises(MissionStudioOpenAIError) as raised:
                    provider.run_stage("builder")
                self.assertEqual(raised.exception.category, "stage_contract_rejected")
                self.assertEqual(len(responses.calls), 3)


class MissionStudioDockerContractTests(unittest.TestCase):
    def test_docker_installs_openai_extra_without_declaring_a_key(self) -> None:
        dockerfile = Path("Dockerfile").read_text(encoding="utf-8")
        self.assertIn("python -m pip install --no-cache-dir '.[openai]'", dockerfile)
        self.assertNotIn("OPENAI_API_KEY", dockerfile)
        self.assertNotIn("APR_OPENAI_MODEL", dockerfile)

    def test_ui_exposes_only_functional_provider_controls(self) -> None:
        html = render_mission_control("csrf-test-token")
        self.assertIn('id="studio-provider"', html)
        self.assertIn('<option value="fixture">FIXTURE</option>', html)
        self.assertIn('<option value="openai" disabled>LIVE GPT-5.6</option>', html)
        self.assertIn("OPENAI KEY ABSENT", html)
        self.assertIn("provider:studioProvider.value", html)
        self.assertNotIn("api_key:", html)


if __name__ == "__main__":
    unittest.main()
