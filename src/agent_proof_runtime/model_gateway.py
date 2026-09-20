"""Minimal server-side model gateway.

The browser never talks to a model provider: the 3D control plane asks Agent
Proof Runtime, and Agent Proof Runtime asks the provider. Credentials are read
from the process environment here and nowhere else.

The gateway speaks the OpenAI-compatible chat-completions dialect over the
standard library, so selecting a live provider adds no runtime dependency to
the package.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

OPENROUTER_ID = "openrouter"
OPENROUTER_DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_DEFAULT_MODEL = "openrouter/auto"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

# Provider status as reported to an operator. CONFIGURED means a credential is
# present, never that a request has succeeded.
STATUS_NOT_CONFIGURED = "NOT_CONFIGURED"
STATUS_CONFIGURED = "CONFIGURED"
STATUS_LAST_CALL_OK = "LAST_CALL_OK"
STATUS_ERROR = "ERROR"
STATUS_RATE_LIMITED = "RATE_LIMITED"
STATUS_AUTH_FAILED = "AUTH_FAILED"


class ModelGatewayError(RuntimeError):
    """A model request failed. Never carries credential material."""

    def __init__(self, message: str, category: str, *, status: int | None = None):
        self.category = category
        self.status = status
        super().__init__(message)


class ProviderNotConfigured(ModelGatewayError):
    def __init__(self, message: str):
        super().__init__(message, "provider_not_configured")


@dataclass(frozen=True)
class ModelResponse:
    text: str
    resolved_model: str
    response_id: str | None
    usage: dict[str, int]
    latency_ms: int


class ModelClient(Protocol):
    id: str

    live: bool

    def configured(self) -> bool: ...

    def requested_model(self) -> str: ...

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int,
        timeout_seconds: int,
        json_only: bool = False,
    ) -> ModelResponse: ...


def _usage(value: Any) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}

    def count(name: str) -> int:
        raw = source.get(name)
        return raw if isinstance(raw, int) and not isinstance(raw, bool) and raw >= 0 else 0

    return {
        "input_tokens": count("prompt_tokens"),
        "output_tokens": count("completion_tokens"),
        "total_tokens": count("total_tokens"),
    }


class OpenRouterClient:
    """OpenRouter adapter built on the standard library.

    Error messages are derived from the HTTP status and the exception class
    only, so a credential can never reach a log, an event, or a bundle.
    """

    id = OPENROUTER_ID

    def __init__(self, *, transport: Any | None = None) -> None:
        # Tests inject a transport; nothing else may reach the network.
        self._transport = transport
        # Evidence must not claim a live API request that never happened.
        self.live = transport is None

    def _api_key(self) -> str:
        key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        if not key:
            raise ProviderNotConfigured(
                "OPENROUTER_API_KEY is required only when provider=openrouter"
            )
        return key

    def configured(self) -> bool:
        return bool(os.environ.get("OPENROUTER_API_KEY", "").strip()) or self._transport is not None

    def base_url(self) -> str:
        return os.environ.get("OPENROUTER_BASE_URL", OPENROUTER_DEFAULT_BASE_URL).rstrip("/")

    def requested_model(self) -> str:
        return os.environ.get("APR_OPENROUTER_MODEL", OPENROUTER_DEFAULT_MODEL).strip() or (
            OPENROUTER_DEFAULT_MODEL
        )

    def _post(self, payload: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
        if self._transport is not None:
            return self._transport(payload)
        api_key = self._api_key()
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url()}/chat/completions",
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "X-Title": "Agent Proof Runtime",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = response.read(MAX_RESPONSE_BYTES + 1)
        except urllib.error.HTTPError as error:
            status = int(error.code)
            if status in {401, 403}:
                raise ModelGatewayError(
                    "the OpenRouter credentials were rejected",
                    "openrouter_auth_failed",
                    status=status,
                ) from None
            if status == 429:
                raise ModelGatewayError(
                    "the OpenRouter request was rate limited",
                    "openrouter_rate_limited",
                    status=status,
                ) from None
            if status >= 500:
                raise ModelGatewayError(
                    "OpenRouter returned a server error",
                    "openrouter_server_error",
                    status=status,
                ) from None
            raise ModelGatewayError(
                "the OpenRouter request was rejected",
                "openrouter_request_failed",
                status=status,
            ) from None
        except TimeoutError:
            raise ModelGatewayError(
                "the OpenRouter request timed out", "openrouter_timeout"
            ) from None
        except urllib.error.URLError as error:
            category = (
                "openrouter_timeout"
                if isinstance(error.reason, TimeoutError)
                else "openrouter_connection_failed"
            )
            raise ModelGatewayError(
                "the OpenRouter connection failed", category
            ) from None
        except OSError:
            raise ModelGatewayError(
                "the OpenRouter connection failed", "openrouter_connection_failed"
            ) from None
        if len(raw) > MAX_RESPONSE_BYTES:
            raise ModelGatewayError(
                "the OpenRouter response exceeded the accepted size",
                "openrouter_request_failed",
            )
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            raise ModelGatewayError(
                "the OpenRouter response was not valid JSON", "openrouter_request_failed"
            ) from None
        if not isinstance(value, dict):
            raise ModelGatewayError(
                "the OpenRouter response had an unexpected shape",
                "openrouter_request_failed",
            )
        return value

    def generate(
        self,
        *,
        system: str,
        user: str,
        max_output_tokens: int,
        timeout_seconds: int,
        json_only: bool = False,
    ) -> ModelResponse:
        requested = self.requested_model()
        payload: dict[str, Any] = {
            "model": requested,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_output_tokens,
            "temperature": 0,
        }
        if json_only:
            payload["response_format"] = {"type": "json_object"}
        started = time.monotonic()
        value = self._post(payload, timeout_seconds)
        latency_ms = max(0, int((time.monotonic() - started) * 1000))

        choices = value.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise ModelGatewayError(
                "the OpenRouter response contained no choice",
                "openrouter_request_failed",
            )
        message = choices[0].get("message")
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise ModelGatewayError(
                "the OpenRouter response contained no text",
                "openrouter_request_failed",
            )
        finish_reason = choices[0].get("finish_reason")
        if finish_reason == "length":
            raise ModelGatewayError(
                "the OpenRouter response exceeded its output budget",
                "openrouter_request_failed",
            )
        response_id = value.get("id")
        resolved = value.get("model")
        return ModelResponse(
            text=text,
            resolved_model=resolved if isinstance(resolved, str) and resolved else requested,
            response_id=response_id if isinstance(response_id, str) and response_id else None,
            usage=_usage(value.get("usage")),
            latency_ms=latency_ms,
        )


def model_client(provider: str, *, transport: Any | None = None) -> ModelClient:
    if provider == OPENROUTER_ID:
        return OpenRouterClient(transport=transport)
    raise ProviderNotConfigured(
        f"provider {provider} has no model gateway adapter in this build"
    )


def provider_status(provider: str, last_call: str | None = None) -> dict[str, Any]:
    """Operator-facing provider status. Never reports a call that did not run."""

    if provider == OPENROUTER_ID:
        client = OpenRouterClient()
        configured = client.configured()
        return {
            "provider": OPENROUTER_ID,
            "model": client.requested_model(),
            "base_url": client.base_url(),
            "status": (last_call if configured and last_call else
                       STATUS_CONFIGURED if configured else STATUS_NOT_CONFIGURED),
        }
    return {"provider": provider, "model": None, "base_url": None, "status": STATUS_NOT_CONFIGURED}


CATEGORY_STATUS = {
    "openrouter_auth_failed": STATUS_AUTH_FAILED,
    "openrouter_rate_limited": STATUS_RATE_LIMITED,
    "provider_not_configured": STATUS_NOT_CONFIGURED,
}


def status_for_category(category: str) -> str:
    return CATEGORY_STATUS.get(category, STATUS_ERROR)
