"""Narrow artifact-proposal providers for the Build Week runtime."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Protocol

from .canonical import hash_json
from .mission_v1 import BuildWeekMission

OPENAI_IMPLEMENTATION_STATUS = "IMPLEMENTED BUT NOT LIVE-VALIDATED"
PROPOSAL_SCHEMA_NAME = "apr_artifact_proposal_v1"


class ProviderError(RuntimeError):
    """A provider could not produce a valid artifact proposal."""


class ProviderConfigurationError(ProviderError):
    """The selected provider is not configured."""


class ProviderResponseError(ProviderError):
    """The provider returned an invalid structured response."""


@dataclass(frozen=True)
class ProposedArtifact:
    path: str
    media_type: str
    content: str

    def to_dict(self) -> dict[str, str]:
        return {
            "path": self.path,
            "media_type": self.media_type,
            "content": self.content,
        }


@dataclass(frozen=True)
class ArtifactProposal:
    artifacts: tuple[ProposedArtifact, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"artifacts": [artifact.to_dict() for artifact in self.artifacts]}


@dataclass(frozen=True)
class ProviderResult:
    proposal: ArtifactProposal
    metadata: dict[str, Any]


class ArtifactProvider(Protocol):
    name: str

    def propose(self, mission: BuildWeekMission) -> ProviderResult: ...


def proposal_json_schema(mission: BuildWeekMission) -> dict[str, Any]:
    paths = [item.path for item in mission.artifact_contract.artifacts]
    media_types = list(mission.artifact_contract.allowed_media_types)
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["artifacts"],
        "properties": {
            "artifacts": {
                "type": "array",
                "maxItems": mission.artifact_contract.max_files,
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["path", "media_type", "content"],
                    "properties": {
                        "path": {"type": "string", "enum": paths},
                        "media_type": {"type": "string", "enum": media_types},
                        "content": {"type": "string"},
                    },
                },
            }
        },
    }


def parse_artifact_proposal(value: Any) -> ArtifactProposal:
    if not isinstance(value, dict) or set(value) != {"artifacts"}:
        raise ProviderResponseError("proposal must contain only artifacts")
    artifacts_value = value["artifacts"]
    if not isinstance(artifacts_value, list):
        raise ProviderResponseError("proposal.artifacts must be an array")
    artifacts: list[ProposedArtifact] = []
    for index, artifact in enumerate(artifacts_value):
        label = f"proposal.artifacts[{index}]"
        if not isinstance(artifact, dict) or set(artifact) != {
            "path",
            "media_type",
            "content",
        }:
            raise ProviderResponseError(f"{label} has an invalid shape")
        if not all(isinstance(artifact[field], str) for field in artifact):
            raise ProviderResponseError(f"{label} fields must be strings")
        artifacts.append(
            ProposedArtifact(
                path=artifact["path"],
                media_type=artifact["media_type"],
                content=artifact["content"],
            )
        )
    return ArtifactProposal(tuple(artifacts))


def parse_artifact_proposal_json(text: str) -> ArtifactProposal:
    if not isinstance(text, str) or not text:
        raise ProviderResponseError("provider returned no structured output")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ProviderResponseError(f"structured output has duplicate key: {key}")
            result[key] = value
        return result

    try:
        value = json.loads(text, object_pairs_hook=reject_duplicates)
    except ProviderResponseError:
        raise
    except (json.JSONDecodeError, RecursionError) as error:
        raise ProviderResponseError(f"structured output is invalid JSON: {error}") from error
    return parse_artifact_proposal(value)


def _metadata(
    *,
    provider: str,
    requested_model: str,
    resolved_model: str,
    response_id: str | None,
    usage: dict[str, int],
    latency_ms: int,
    input_hash: str,
    proposal: ArtifactProposal,
    implementation_status: str,
) -> dict[str, Any]:
    normalized_proposal = {
        "artifacts": sorted(
            (artifact.to_dict() for artifact in proposal.artifacts),
            key=lambda artifact: artifact["path"],
        )
    }
    return {
        "provider": provider,
        "requested_model": requested_model,
        "resolved_model": resolved_model,
        "response_id": response_id,
        "token_usage": {
            "input_tokens": int(usage.get("input_tokens", 0)),
            "output_tokens": int(usage.get("output_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        },
        "latency_ms": latency_ms,
        "input_hash": input_hash,
        "response_hash": hash_json(normalized_proposal),
        "implementation_status": implementation_status,
    }


class FixtureProvider:
    name = "fixture"

    def propose(self, mission: BuildWeekMission) -> ProviderResult:
        proposal = ArtifactProposal(
            tuple(
                ProposedArtifact(item.path, item.media_type, item.fixture_content)
                for item in mission.artifact_contract.artifacts
            )
        )
        return ProviderResult(
            proposal=proposal,
            metadata=_metadata(
                provider=self.name,
                requested_model=mission.model,
                resolved_model="fixture-v1",
                response_id=None,
                usage={},
                latency_ms=0,
                input_hash=hash_json(mission.provider_input()),
                proposal=proposal,
                implementation_status="DETERMINISTIC_FIXTURE",
            ),
        )


class OpenAIProvider:
    """Official OpenAI Responses API adapter with strict Structured Outputs.

    The SDK import and API key lookup happen only when this provider is selected.
    Tests inject a fake client and never make a network request.
    """

    name = "openai"

    def __init__(self, client: Any | None = None) -> None:
        self._client = client

    def _client_for(self, mission: BuildWeekMission) -> Any:
        if self._client is not None:
            return self._client
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ProviderConfigurationError(
                "OPENAI_API_KEY is required only when provider=openai"
            )
        try:
            from openai import OpenAI
        except ImportError as error:
            raise ProviderConfigurationError(
                "the optional openai package is required for provider=openai; "
                "install agent-proof-runtime[openai]"
            ) from error
        return OpenAI(api_key=api_key, timeout=mission.limits.provider_timeout_seconds)

    def propose(self, mission: BuildWeekMission) -> ProviderResult:
        live_request = self._client is None
        client = self._client_for(mission)
        requested_model = os.environ.get("APR_OPENAI_MODEL", mission.model)
        provider_input = mission.provider_input()
        started = time.monotonic()
        try:
            response = client.responses.create(
                model=requested_model,
                instructions=(
                    "Return only the requested artifact proposal. Do not propose shell "
                    "commands, tools, filesystem operations, hidden reasoning, or commentary."
                ),
                input=json.dumps(
                    provider_input,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": PROPOSAL_SCHEMA_NAME,
                        "strict": True,
                        "schema": proposal_json_schema(mission),
                    }
                },
                max_output_tokens=mission.limits.max_output_tokens,
                store=False,
            )
        except ProviderError:
            raise
        except Exception as error:
            raise ProviderError(f"OpenAI Responses API request failed: {type(error).__name__}") from error
        latency_ms = max(0, int((time.monotonic() - started) * 1000))
        output_text = getattr(response, "output_text", None)
        proposal = parse_artifact_proposal_json(output_text)
        usage_value = getattr(response, "usage", None)
        usage = {
            "input_tokens": getattr(usage_value, "input_tokens", 0),
            "output_tokens": getattr(usage_value, "output_tokens", 0),
            "total_tokens": getattr(usage_value, "total_tokens", 0),
        }
        metadata = _metadata(
            provider=self.name,
            requested_model=requested_model,
            resolved_model=str(getattr(response, "model", requested_model)),
            response_id=str(getattr(response, "id", "")) or None,
            usage=usage,
            latency_ms=latency_ms,
            input_hash=hash_json(provider_input),
            proposal=proposal,
            implementation_status=(
                "LIVE_API_REQUEST_EXECUTED"
                if live_request
                else OPENAI_IMPLEMENTATION_STATUS
            ),
        )
        return ProviderResult(proposal=proposal, metadata=metadata)


def provider_for(name: str, *, openai_client: Any | None = None) -> ArtifactProvider:
    if name == "fixture":
        return FixtureProvider()
    if name == "openai":
        return OpenAIProvider(openai_client)
    raise ProviderConfigurationError(f"unsupported provider: {name}")
