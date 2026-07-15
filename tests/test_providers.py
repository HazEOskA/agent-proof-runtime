from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from contextlib import redirect_stderr
from io import StringIO

from agent_proof_runtime.build_week_runtime import run_build_week_mission
from agent_proof_runtime.cli import main
from agent_proof_runtime.mission_v1 import load_build_week_mission
from agent_proof_runtime.providers import (
    FixtureProvider,
    OpenAIProvider,
    ProviderConfigurationError,
    ProviderResponseError,
    parse_artifact_proposal_json,
)


EXAMPLE = Path("examples/build-week-mission.json")


class FakeResponses:
    def __init__(self, response: object) -> None:
        self.response = response
        self.calls: list[dict] = []

    def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        return self.response


def fake_openai_client(secret_marker: str = "must-never-persist") -> tuple[object, FakeResponses]:
    mission = load_build_week_mission(EXAMPLE)
    proposal = {
        "artifacts": [
            {
                "path": item.path,
                "media_type": item.media_type,
                "content": item.fixture_content,
            }
            for item in mission.artifact_contract.artifacts
        ]
    }
    response = SimpleNamespace(
        id="resp_mock_build_week",
        model="gpt-5.6-2026-07-01",
        output_text=json.dumps(proposal),
        usage=SimpleNamespace(input_tokens=120, output_tokens=80, total_tokens=200),
        hidden_reasoning=secret_marker,
        raw_internal_payload=secret_marker,
    )
    responses = FakeResponses(response)
    return SimpleNamespace(responses=responses), responses


class ProviderTests(unittest.TestCase):
    def test_fixture_is_deterministic_and_has_live_shape(self) -> None:
        mission = load_build_week_mission(EXAMPLE)
        first = FixtureProvider().propose(mission)
        second = FixtureProvider().propose(mission)
        self.assertEqual(first, second)
        self.assertEqual(
            set(first.metadata),
            {
                "provider", "requested_model", "resolved_model", "response_id",
                "token_usage", "latency_ms", "input_hash", "response_hash",
                "implementation_status",
            },
        )

    def test_mocked_openai_uses_responses_structured_output(self) -> None:
        mission = load_build_week_mission(EXAMPLE)
        client, responses = fake_openai_client()
        with patch.dict(os.environ, {"APR_OPENAI_MODEL": "gpt-5.6"}, clear=True):
            result = OpenAIProvider(client).propose(mission)
        self.assertEqual(result.metadata["provider"], "openai")
        self.assertEqual(
            result.metadata["implementation_status"],
            "IMPLEMENTED BUT NOT LIVE-VALIDATED",
        )
        call = responses.calls[0]
        self.assertEqual(call["model"], "gpt-5.6")
        self.assertFalse(call["store"])
        self.assertTrue(call["text"]["format"]["strict"])
        self.assertEqual(call["text"]["format"]["type"], "json_schema")
        self.assertNotIn("reasoning", call)

    def test_structured_output_parser_rejects_unknown_and_duplicate_fields(self) -> None:
        with self.assertRaises(ProviderResponseError):
            parse_artifact_proposal_json('{"artifacts":[],"command":"ls"}')
        with self.assertRaises(ProviderResponseError):
            parse_artifact_proposal_json('{"artifacts":[],"artifacts":[]}')

    def test_openai_key_is_required_only_when_openai_is_selected(self) -> None:
        mission = load_build_week_mission(EXAMPLE)
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(FixtureProvider().propose(mission).metadata["provider"], "fixture")
            with self.assertRaises(ProviderConfigurationError):
                OpenAIProvider().propose(mission)

    def test_provider_secrets_and_hidden_reasoning_are_never_persisted(self) -> None:
        marker = "sk-test-do-not-persist-9f68c3"
        client, _ = fake_openai_client(marker)
        provider = OpenAIProvider(client)
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with patch.dict(os.environ, {"OPENAI_API_KEY": marker}, clear=True):
                result = run_build_week_mission(
                    EXAMPLE, output, provider_name="openai", provider=provider
                )
            self.assertTrue(result.verification.valid)
            persisted = "\n".join(
                path.read_text(encoding="utf-8")
                for path in output.rglob("*")
                if path.is_file()
            )
            self.assertNotIn(marker, persisted)
            self.assertNotIn("hidden_reasoning", persisted)
            self.assertNotIn("raw_internal_payload", persisted)

    def test_cli_absent_key_is_provider_failure_and_creates_no_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with patch.dict(os.environ, {}, clear=True):
                with redirect_stderr(StringIO()):
                    code = main(
                        ["run", str(EXAMPLE), "--provider", "openai", "--output", str(output)]
                    )
            self.assertEqual(code, 3)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
