"""Tests for generic Sensei missions.

A generic mission must reach a proof through the existing runtime, chain,
bundle and independent verifier — never through a parallel proof path, and
never by letting a planner or a model decide that something is verified.
"""

from __future__ import annotations

import json
import os
import threading
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from agent_proof_runtime.acceptance import evaluate_acceptance
from agent_proof_runtime.build_week_runtime import run_build_week_mission
from agent_proof_runtime.generic_mission import (
    MAX_STAGES,
    PLAN_ARTIFACT_PATH,
    PLAN_VERSION,
    VERIFICATION_SCOPE,
    GenericPlanError,
    GenericStageProvider,
    build_manifest,
    fixture_plan,
    normalized_prompt,
    parse_mission_plan,
    parse_plan_json,
)
from agent_proof_runtime.mission_studio import (
    MissionStudioManager,
    MissionStudioRequest,
    MissionStudioValidationError,
)
from agent_proof_runtime.validator import verify_bundle

SECRET = "super-secret-test-key-12345"
PROMPT = (
    "Przeanalizuj ponizszy tekst, wskaz trzy najwazniejsze problemy, "
    "przygotuj ulepszona wersje i krotkie podsumowanie zmian."
)


def plan_value(**overrides: Any) -> dict[str, Any]:
    value: dict[str, Any] = {
        "version": PLAN_VERSION,
        "title": "Analiza tekstu",
        "goal": "Znajdz problemy w tekscie i popraw go.",
        "stages": [
            {
                "id": "analyze",
                "role": "ANALYST",
                "instruction": "Wypisz obserwacje o tekscie.",
                "expected_output": {"type": "text"},
                "acceptance": [{"type": "artifact_present"}, {"type": "nonempty_text"}],
            }
        ],
    }
    value.update(overrides)
    return value


def drain(manager: MissionStudioManager, session_id: str, limit: int = 400) -> dict[str, Any]:
    for _ in range(limit):
        session = manager.get(session_id)
        if session["state"] in {"completed", "failed"}:
            return session
        time.sleep(0.02)
    raise AssertionError("the session never reached a terminal state")


class PlanContractTest(unittest.TestCase):
    def test_a_minimal_plan_is_accepted(self) -> None:
        plan = parse_mission_plan(plan_value())
        self.assertEqual(plan.title, "Analiza tekstu")
        self.assertEqual(len(plan.stages), 1)
        self.assertEqual(plan.stages[0].role, "ANALYST")

    def test_between_one_and_four_stages_are_accepted(self) -> None:
        for count in range(1, MAX_STAGES + 1):
            stages = [
                {
                    "id": f"stage_{index}",
                    "role": f"ROLE {index}",
                    "instruction": "Wykonaj zadanie etapu.",
                    "expected_output": {"type": "text"},
                    "acceptance": [{"type": "nonempty_text"}],
                }
                for index in range(count)
            ]
            self.assertEqual(len(parse_mission_plan(plan_value(stages=stages)).stages), count)

    def test_more_than_four_stages_are_rejected(self) -> None:
        stages = [
            {
                "id": f"stage_{index}",
                "role": "ROLE",
                "instruction": "Wykonaj zadanie etapu.",
                "expected_output": {"type": "text"},
                "acceptance": [{"type": "nonempty_text"}],
            }
            for index in range(MAX_STAGES + 1)
        ]
        with self.assertRaises(GenericPlanError):
            parse_mission_plan(plan_value(stages=stages))

    def test_max_agents_narrows_the_accepted_plan(self) -> None:
        stages = [
            {
                "id": f"stage_{index}",
                "role": "ROLE",
                "instruction": "Wykonaj zadanie etapu.",
                "expected_output": {"type": "text"},
                "acceptance": [{"type": "nonempty_text"}],
            }
            for index in range(3)
        ]
        with self.assertRaises(GenericPlanError):
            parse_mission_plan(plan_value(stages=stages), max_stages=2)

    def test_an_invented_acceptance_check_is_rejected(self) -> None:
        for invented in (
            {"type": "llm_judge"},
            {"type": "semantic_correctness"},
            {"type": "is_true"},
            {"type": "shell_command", "command": "rm -rf /"},
        ):
            stages = [dict(plan_value()["stages"][0], acceptance=[invented])]
            with self.assertRaises(GenericPlanError) as caught:
                parse_mission_plan(plan_value(stages=stages))
            self.assertEqual(caught.exception.category, "planner_contract_invalid")

    def test_json_checks_require_a_json_stage(self) -> None:
        stages = [dict(plan_value()["stages"][0], acceptance=[{"type": "json_parseable"}])]
        with self.assertRaises(GenericPlanError):
            parse_mission_plan(plan_value(stages=stages))

    def test_invalid_shapes_are_rejected(self) -> None:
        cases: list[dict[str, Any]] = [
            plan_value(version="other-version"),
            plan_value(title="x"),
            plan_value(goal="short"),
            plan_value(stages=[]),
            plan_value(extra="field"),
        ]
        for case in cases:
            with self.assertRaises(GenericPlanError):
                parse_mission_plan(case)

    def test_duplicate_stage_ids_are_rejected(self) -> None:
        stage = plan_value()["stages"][0]
        with self.assertRaises(GenericPlanError):
            parse_mission_plan(plan_value(stages=[stage, dict(stage)]))

    def test_inputs_may_only_reference_earlier_stages(self) -> None:
        stages = [
            dict(plan_value()["stages"][0], inputs=["later"]),
            {
                "id": "later",
                "role": "REVIEWER",
                "instruction": "Sprawdz wynik poprzedniego etapu.",
                "expected_output": {"type": "text"},
                "acceptance": [{"type": "nonempty_text"}],
            },
        ]
        with self.assertRaises(GenericPlanError):
            parse_mission_plan(plan_value(stages=stages))

    def test_invalid_planner_json_is_categorized(self) -> None:
        with self.assertRaises(GenericPlanError) as caught:
            parse_plan_json("not json at all")
        self.assertEqual(caught.exception.category, "planner_invalid_json")

    def test_a_fenced_plan_is_still_read(self) -> None:
        text = "```json\n" + json.dumps(plan_value()) + "\n```"
        self.assertEqual(parse_plan_json(text).title, "Analiza tekstu")

    def test_prompt_bounds_are_enforced(self) -> None:
        with self.assertRaises(GenericPlanError):
            normalized_prompt("krotki")
        with self.assertRaises(GenericPlanError):
            normalized_prompt("x" * 5000)
        self.assertEqual(normalized_prompt("  wykonaj   to zadanie  "), "wykonaj to zadanie")


class ManifestTest(unittest.TestCase):
    def test_a_plan_becomes_an_ordinary_apr_manifest(self) -> None:
        plan = parse_mission_plan(plan_value())
        mission = build_manifest(plan, prompt=PROMPT, provider="fixture", model="fixture-v1")
        paths = [item.path for item in mission.artifact_contract.artifacts]
        self.assertEqual(paths, [PLAN_ARTIFACT_PATH, "stage/01-analyze.txt"])
        self.assertTrue(mission.manifest_hash.startswith("sha256:"))

    def test_allowlisted_checks_map_onto_existing_runtime_checks(self) -> None:
        stages = [
            {
                "id": "report",
                "role": "REPORTER",
                "instruction": "Zwroc raport w formacie JSON.",
                "expected_output": {"type": "json"},
                "acceptance": [
                    {"type": "artifact_present"},
                    {"type": "min_length", "min_bytes": 20},
                    {"type": "json_parseable"},
                    {"type": "json_required_keys", "keys": ["summary"]},
                ],
            }
        ]
        mission = build_manifest(
            parse_mission_plan(plan_value(stages=stages)),
            prompt=PROMPT,
            provider="fixture",
            model="fixture-v1",
        )
        mapped = {check["type"] for check in mission.acceptance_checks}
        self.assertLessEqual(
            {"file_exists", "minimum_size", "json_valid", "json_required_keys", "file_count"},
            mapped,
        )
        self.assertNotIn("llm_judge", mapped)

    def test_the_plan_artifact_records_the_prompt_and_scope(self) -> None:
        plan = parse_mission_plan(plan_value())
        mission = build_manifest(plan, prompt=PROMPT, provider="fixture", model="fixture-v1")
        entry = next(
            item for item in mission.artifact_contract.artifacts if item.path == PLAN_ARTIFACT_PATH
        )
        payload = json.loads(entry.fixture_content)
        self.assertEqual(payload["prompt"], PROMPT)
        self.assertEqual(payload["verification_scope"], list(VERIFICATION_SCOPE))


class FixtureExecutionTest(unittest.TestCase):
    def test_a_fixture_mission_reaches_a_real_verified_proof(self) -> None:
        prompt = normalized_prompt(PROMPT)
        plan = fixture_plan(prompt, MAX_STAGES)
        mission = build_manifest(plan, prompt=prompt, provider="fixture", model="fixture-v1")
        provider = GenericStageProvider(
            plan=plan, prompt=prompt, provider_name="fixture", client=None
        )
        for stage in plan.stages:
            provider.run_stage(stage.stage_id)
        with TemporaryDirectory() as directory:
            run = Path(directory) / "run"
            result = run_build_week_mission(
                mission, run, provider_name="fixture", provider=provider
            )
            self.assertEqual(result.mission_status, "PASSED")
            # The independent verifier, not the runtime, decides this.
            verification = verify_bundle(run / "proof-bundle.json")
            self.assertEqual(verification.status, "LOCAL_VERIFIED")
            self.assertEqual(verification.errors, ())
            bundle = json.loads((run / "proof-bundle.json").read_text(encoding="utf-8"))
            self.assertEqual(len(bundle["artifacts"]), MAX_STAGES + 1)
            self.assertTrue(all(check["passed"] for check in bundle["acceptance"]["checks"]))

    def test_a_missing_stage_artifact_is_refused_before_a_run(self) -> None:
        prompt = normalized_prompt(PROMPT)
        plan = fixture_plan(prompt, 2)
        provider = GenericStageProvider(
            plan=plan, prompt=prompt, provider_name="fixture", client=None
        )
        provider.run_stage(plan.stages[0].stage_id)
        with self.assertRaises(GenericPlanError):
            provider.proposal()

    def test_an_empty_stage_answer_fails_acceptance(self) -> None:
        prompt = normalized_prompt(PROMPT)
        plan = parse_mission_plan(plan_value())
        mission = build_manifest(plan, prompt=prompt, provider="fixture", model="fixture-v1")
        with TemporaryDirectory() as directory:
            artifact_root = Path(directory) / "artifact"
            (artifact_root / "stage").mkdir(parents=True)
            (artifact_root / "stage" / "01-analyze.txt").write_text("", encoding="utf-8")
            results = {item["id"]: item["passed"] for item in evaluate_acceptance(mission, artifact_root)}
        self.assertFalse(results["s1_analyze_nonempty"])


class StudioRequestTest(unittest.TestCase):
    def test_the_existing_mission_type_still_parses(self) -> None:
        request = MissionStudioRequest.parse(
            {"mission_type": "verified_website_build", "brief": "Zbuduj strone produktu."}
        )
        self.assertEqual(request.mission_type, "verified_website_build")
        self.assertEqual(request.provider, "fixture")

    def test_a_generic_request_parses(self) -> None:
        request = MissionStudioRequest.parse(
            {"mission_type": "generic_v1", "prompt": PROMPT, "max_agents": 3}
        )
        self.assertEqual(request.mission_type, "generic_v1")
        self.assertEqual(request.max_agents, 3)

    def test_invalid_generic_requests_are_rejected(self) -> None:
        cases: list[dict[str, Any]] = [
            {"mission_type": "generic_v1"},
            {"mission_type": "generic_v1", "prompt": "short"},
            {"mission_type": "generic_v1", "prompt": PROMPT, "max_agents": 0},
            {"mission_type": "generic_v1", "prompt": PROMPT, "max_agents": 9},
            {"mission_type": "generic_v1", "prompt": PROMPT, "provider": "openai"},
            {"mission_type": "generic_v1", "prompt": PROMPT, "unknown": 1},
        ]
        for case in cases:
            with self.assertRaises(MissionStudioValidationError):
                MissionStudioRequest.parse(case)


class GenericSessionTest(unittest.TestCase):
    def setUp(self) -> None:
        self._directory = TemporaryDirectory()
        self.runs = Path(self._directory.name)

    def tearDown(self) -> None:
        self._directory.cleanup()

    def _manager(self, transport: Any | None = None) -> MissionStudioManager:
        return MissionStudioManager(
            runs_dir=self.runs,
            run_lock=threading.Lock(),
            stage_delay_seconds=0.0,
            model_transport=transport,
        )

    def test_a_fixture_session_produces_real_events_and_a_real_proof(self) -> None:
        manager = self._manager()
        started = manager.start({"mission_type": "generic_v1", "prompt": PROMPT})
        session = drain(manager, started["session_id"])

        self.assertEqual(session["state"], "completed")
        self.assertEqual(session["mission_status"], "PASSED")
        self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
        self.assertEqual(session["anchor_status"], "UNANCHORED")

        types = [event["type"] for event in session["events"]]
        self.assertIn("studio.plan_requested", types)
        self.assertIn("studio.plan_accepted", types)
        self.assertIn("apr.run.started", types)
        self.assertIn("apr.contract_enforced", types)
        self.assertIn("apr.run.completed", types)
        self.assertIn("verifier.completed", types)

        # Dynamic roles come from the plan, not from a hardcoded pipeline.
        roles = [agent["stage_name"] for agent in session["agents"]]
        self.assertEqual(roles, ["ANALYST", "CRITIC", "REWRITER", "REVIEWER"])
        self.assertTrue(all(agent["status"] == "completed" for agent in session["agents"]))

        # Handoffs follow the plan's own edges.
        handoffs = [item for item in types if item.startswith("handoff.")]
        self.assertEqual(
            handoffs,
            [
                "handoff.analyze_to_critique",
                "handoff.critique_to_rewrite",
                "handoff.rewrite_to_review",
                "handoff.review_to_apr",
            ],
        )

        run = self.runs / session["apr_run_id"]
        self.assertEqual(verify_bundle(run / "proof-bundle.json").status, "LOCAL_VERIFIED")
        self.assertTrue((run / "artifact" / PLAN_ARTIFACT_PATH).is_file())

    def test_execution_and_proof_are_recorded_separately(self) -> None:
        manager = self._manager()
        started = manager.start({"mission_type": "generic_v1", "prompt": PROMPT})
        session = drain(manager, started["session_id"])
        events = {event["type"]: event for event in session["events"]}
        # apr.run.completed carries no proof verdict; verifier.completed does.
        self.assertNotIn("status", events["apr.run.completed"])
        self.assertEqual(events["verifier.completed"]["status"], "LOCAL_VERIFIED")
        self.assertLess(
            [event["type"] for event in session["events"]].index("apr.run.completed"),
            [event["type"] for event in session["events"]].index("verifier.completed"),
        )

    def test_a_single_stage_plan_runs(self) -> None:
        manager = self._manager()
        started = manager.start(
            {"mission_type": "generic_v1", "prompt": PROMPT, "max_agents": 1}
        )
        session = drain(manager, started["session_id"])
        self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
        self.assertEqual(len(session["agents"]), 1)

    def test_the_existing_mission_type_still_runs(self) -> None:
        manager = self._manager()
        started = manager.start(
            {"mission_type": "verified_website_build", "brief": "Zbuduj strone produktu APR."}
        )
        session = drain(manager, started["session_id"])
        self.assertEqual(session["mission_status"], "PASSED")
        self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
        self.assertEqual(len(session["agents"]), 7)

    def test_a_rejected_plan_fails_the_mission_without_a_run(self) -> None:
        def transport(payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "id": "x",
                "model": "m",
                "choices": [
                    {"message": {"content": json.dumps({"version": "wrong"})}, "finish_reason": "stop"}
                ],
            }

        os.environ["OPENROUTER_API_KEY"] = SECRET
        try:
            manager = self._manager(transport)
            started = manager.start(
                {"mission_type": "generic_v1", "prompt": PROMPT, "provider": "openrouter"}
            )
            session = drain(manager, started["session_id"])
        finally:
            os.environ.pop("OPENROUTER_API_KEY", None)
        self.assertEqual(session["state"], "failed")
        self.assertEqual(session["failure_category"], "planner_contract_invalid")
        self.assertIsNone(session["apr_run_id"])
        self.assertEqual(session["proof_status"], "FAILED")

    def test_an_unconfigured_provider_fails_before_any_call(self) -> None:
        saved = os.environ.pop("OPENROUTER_API_KEY", None)
        try:
            manager = self._manager()
            started = manager.start(
                {"mission_type": "generic_v1", "prompt": PROMPT, "provider": "openrouter"}
            )
            session = drain(manager, started["session_id"])
        finally:
            if saved is not None:
                os.environ["OPENROUTER_API_KEY"] = saved
        self.assertEqual(session["state"], "failed")
        self.assertEqual(session["failure_category"], "provider_not_configured")

    def test_a_model_backed_session_runs_and_leaks_no_credential(self) -> None:
        plan = {
            "version": PLAN_VERSION,
            "title": "Analiza tekstu",
            "goal": "Znajdz problemy i przygotuj podsumowanie.",
            "stages": [
                {
                    "id": "analyze",
                    "role": "ANALYST",
                    "instruction": "Wypisz obserwacje o tekscie.",
                    "expected_output": {"type": "text"},
                    "acceptance": [{"type": "artifact_present"}, {"type": "nonempty_text"}],
                },
                {
                    "id": "summary",
                    "role": "REVIEWER",
                    "instruction": "Podsumuj zmiany w formacie JSON.",
                    "expected_output": {"type": "json"},
                    "acceptance": [
                        {"type": "json_parseable"},
                        {"type": "json_required_keys", "keys": ["changes"]},
                    ],
                    "inputs": ["analyze"],
                },
            ],
        }

        def transport(payload: dict[str, Any]) -> dict[str, Any]:
            system = payload["messages"][0]["content"]
            if "execution plan" in system:
                text = json.dumps(plan)
            elif payload.get("response_format"):
                text = json.dumps({"changes": ["skrocono akapit", "poprawiono tytul"]})
            else:
                text = "Obserwacje etapu analizy. " * 4
            return {
                "id": "gen-1",
                "model": "vendor/model",
                "choices": [{"message": {"content": text}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 6, "total_tokens": 11},
            }

        os.environ["OPENROUTER_API_KEY"] = SECRET
        try:
            manager = self._manager(transport)
            started = manager.start(
                {"mission_type": "generic_v1", "prompt": PROMPT, "provider": "openrouter"}
            )
            session = drain(manager, started["session_id"])
            run = self.runs / str(session["apr_run_id"])
            bundle_text = (run / "proof-bundle.json").read_text(encoding="utf-8")
            session_text = json.dumps(session, ensure_ascii=False)
            artifact_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in sorted((run / "artifact").rglob("*"))
                if path.is_file()
            )
            status_text = json.dumps(manager.last_provider_call)
        finally:
            os.environ.pop("OPENROUTER_API_KEY", None)

        self.assertEqual(session["state"], "completed")
        self.assertEqual(session["proof_status"], "LOCAL_VERIFIED")
        self.assertEqual([agent["stage_name"] for agent in session["agents"]], ["ANALYST", "REVIEWER"])
        self.assertEqual(
            [event["type"] for event in session["events"] if event["type"].startswith("handoff.")],
            ["handoff.analyze_to_summary", "handoff.summary_to_apr"],
        )
        bundle = json.loads(bundle_text)
        self.assertEqual(bundle["provider"]["provider"], "openrouter")
        # An injected transport is not a live API request and must not say so.
        self.assertEqual(
            bundle["provider"]["implementation_status"], "IMPLEMENTED BUT NOT LIVE-VALIDATED"
        )
        for blob in (bundle_text, session_text, artifact_text, status_text):
            self.assertNotIn(SECRET, blob)

    def test_a_provider_failure_is_mapped_and_carries_no_credential(self) -> None:
        from agent_proof_runtime.model_gateway import ModelGatewayError

        def transport(payload: dict[str, Any]) -> dict[str, Any]:
            raise ModelGatewayError(
                "the OpenRouter request was rate limited", "openrouter_rate_limited", status=429
            )

        os.environ["OPENROUTER_API_KEY"] = SECRET
        try:
            manager = self._manager(transport)
            started = manager.start(
                {"mission_type": "generic_v1", "prompt": PROMPT, "provider": "openrouter"}
            )
            session = drain(manager, started["session_id"])
            status = dict(manager.last_provider_call)
        finally:
            os.environ.pop("OPENROUTER_API_KEY", None)
        self.assertEqual(session["failure_category"], "openrouter_rate_limited")
        self.assertEqual(status["openrouter"], "RATE_LIMITED")
        self.assertNotIn(SECRET, json.dumps(session, ensure_ascii=False))
        self.assertIsNone(session["apr_run_id"])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
