"""Tests for the server-side model gateway."""

from __future__ import annotations

import io
import json
import os
import unittest
import urllib.error
from typing import Any
from unittest import mock

from agent_proof_runtime.model_gateway import (
    OPENROUTER_ID,
    STATUS_AUTH_FAILED,
    STATUS_CONFIGURED,
    STATUS_NOT_CONFIGURED,
    STATUS_RATE_LIMITED,
    ModelGatewayError,
    OpenRouterClient,
    ProviderNotConfigured,
    model_client,
    provider_status,
    status_for_category,
)

SECRET = "super-secret-test-key-12345"


def _response(payload: dict[str, Any]) -> Any:
    body = json.dumps(payload).encode("utf-8")

    class _Handle(io.BytesIO):
        def __enter__(self) -> "_Handle":
            return self

        def __exit__(self, *args: Any) -> None:
            self.close()

    return _Handle(body)


class ProviderStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = {
            key: os.environ.pop(key, None)
            for key in ("OPENROUTER_API_KEY", "APR_OPENROUTER_MODEL", "OPENROUTER_BASE_URL")
        }

    def tearDown(self) -> None:
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def test_absent_credential_reports_not_configured(self) -> None:
        status = provider_status(OPENROUTER_ID)
        self.assertEqual(status["status"], STATUS_NOT_CONFIGURED)
        self.assertEqual(status["provider"], OPENROUTER_ID)

    def test_present_credential_reports_configured_not_connected(self) -> None:
        os.environ["OPENROUTER_API_KEY"] = SECRET
        status = provider_status(OPENROUTER_ID)
        self.assertEqual(status["status"], STATUS_CONFIGURED)
        self.assertNotIn(SECRET, json.dumps(status))

    def test_status_never_contains_the_credential(self) -> None:
        os.environ["OPENROUTER_API_KEY"] = SECRET
        os.environ["APR_OPENROUTER_MODEL"] = "vendor/model"
        payload = json.dumps(provider_status(OPENROUTER_ID, "LAST_CALL_OK"))
        self.assertNotIn(SECRET, payload)
        self.assertIn("vendor/model", payload)

    def test_configuration_is_read_from_the_environment(self) -> None:
        os.environ["OPENROUTER_API_KEY"] = SECRET
        os.environ["APR_OPENROUTER_MODEL"] = "vendor/model"
        os.environ["OPENROUTER_BASE_URL"] = "https://example.invalid/api/v1/"
        client = OpenRouterClient()
        self.assertEqual(client.requested_model(), "vendor/model")
        self.assertEqual(client.base_url(), "https://example.invalid/api/v1")

    def test_missing_credential_is_a_configuration_error(self) -> None:
        with self.assertRaises(ProviderNotConfigured) as caught:
            OpenRouterClient().generate(
                system="s", user="u", max_output_tokens=16, timeout_seconds=1
            )
        self.assertEqual(caught.exception.category, "provider_not_configured")

    def test_unknown_provider_has_no_adapter(self) -> None:
        with self.assertRaises(ProviderNotConfigured):
            model_client("nvidia-nim")


class OpenRouterErrorMappingTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = os.environ.get("OPENROUTER_API_KEY")
        os.environ["OPENROUTER_API_KEY"] = SECRET

    def tearDown(self) -> None:
        if self._saved is None:
            os.environ.pop("OPENROUTER_API_KEY", None)
        else:
            os.environ["OPENROUTER_API_KEY"] = self._saved

    def _generate_with(self, error: Exception) -> ModelGatewayError:
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ModelGatewayError) as caught:
                OpenRouterClient().generate(
                    system="s", user="u", max_output_tokens=16, timeout_seconds=1
                )
        return caught.exception

    @staticmethod
    def _http(status: int) -> urllib.error.HTTPError:
        return urllib.error.HTTPError(
            "https://openrouter.ai/api/v1/chat/completions", status, "err", {}, None  # type: ignore[arg-type]
        )

    def test_auth_failure_is_mapped(self) -> None:
        for status in (401, 403):
            error = self._generate_with(self._http(status))
            self.assertEqual(error.category, "openrouter_auth_failed")
            self.assertEqual(status_for_category(error.category), STATUS_AUTH_FAILED)

    def test_rate_limit_is_mapped(self) -> None:
        error = self._generate_with(self._http(429))
        self.assertEqual(error.category, "openrouter_rate_limited")
        self.assertEqual(status_for_category(error.category), STATUS_RATE_LIMITED)

    def test_server_error_is_mapped(self) -> None:
        self.assertEqual(self._generate_with(self._http(503)).category, "openrouter_server_error")

    def test_other_status_is_a_request_failure(self) -> None:
        self.assertEqual(self._generate_with(self._http(400)).category, "openrouter_request_failed")

    def test_timeout_is_mapped(self) -> None:
        self.assertEqual(self._generate_with(TimeoutError()).category, "openrouter_timeout")

    def test_connection_failure_is_mapped(self) -> None:
        error = self._generate_with(urllib.error.URLError("unreachable"))
        self.assertEqual(error.category, "openrouter_connection_failed")

    def test_no_error_message_carries_the_credential(self) -> None:
        for error in (
            self._http(401),
            self._http(429),
            self._http(500),
            TimeoutError(),
            urllib.error.URLError("unreachable"),
        ):
            mapped = self._generate_with(error)
            self.assertNotIn(SECRET, str(mapped))

    def test_truncated_answer_is_rejected(self) -> None:
        payload = {
            "id": "x",
            "model": "m",
            "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}],
        }
        with mock.patch("urllib.request.urlopen", return_value=_response(payload)):
            with self.assertRaises(ModelGatewayError):
                OpenRouterClient().generate(
                    system="s", user="u", max_output_tokens=16, timeout_seconds=1
                )

    def test_successful_answer_is_returned_with_usage(self) -> None:
        payload = {
            "id": "gen-1",
            "model": "vendor/model",
            "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 3, "completion_tokens": 4, "total_tokens": 7},
        }
        with mock.patch("urllib.request.urlopen", return_value=_response(payload)) as opener:
            result = OpenRouterClient().generate(
                system="s", user="u", max_output_tokens=16, timeout_seconds=5
            )
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.resolved_model, "vendor/model")
        self.assertEqual(result.usage["total_tokens"], 7)
        # The credential travels in a header, never in the URL.
        request = opener.call_args.args[0]
        self.assertNotIn(SECRET, request.full_url)

    def test_injected_transport_is_not_reported_as_live(self) -> None:
        client = OpenRouterClient(transport=lambda payload: {"choices": []})
        self.assertFalse(client.live)
        self.assertTrue(OpenRouterClient().live)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
