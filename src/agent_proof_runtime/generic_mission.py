"""Generic Sensei missions for Agent Proof Runtime.

A generic mission turns a free-form prompt into a validated plan, then into an
ordinary ``apr.mission.v1`` manifest. From that point the existing runtime,
event chain, Merkle root, Proof Bundle, acceptance evaluator and independent
verifier do all the work: there is no second proof system.

What this module proves and what it does not:

* it proves that a stage ran, that an artifact was materialized, that the
  artifact matches its recorded digest, that declared handoffs happened, and
  that deterministic acceptance checks passed;
* it does not prove that a model's answer is correct, useful or true. No check
  in the allowlist asks a model to grade anything.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from dataclasses import dataclass
from typing import Any

from .canonical import hash_json
from .mission import MissionValidationError
from .mission_v1 import BuildWeekMission, parse_build_week_mission
from .model_gateway import ModelClient, ModelGatewayError
from .providers import ArtifactProposal, ProposedArtifact, ProviderResult

MISSION_TYPE = "generic_v1"
PLAN_VERSION = "generic-mission-plan-v1"
PLAN_ARTIFACT_PATH = "mission/plan.json"
MAX_STAGES = 4
MAX_PROMPT_CHARS = 4000
MIN_PROMPT_CHARS = 10
STAGE_MAX_BYTES = 24 * 1024
PLAN_MAX_BYTES = 16 * 1024

STAGE_ID = re.compile(r"^[a-z][a-z0-9_]{1,31}$")
ROLE = re.compile(r"^[A-Z][A-Z0-9 _-]{1,31}$")

OUTPUT_TYPES = {
    "text": ("text/plain", "txt"),
    "markdown": ("text/markdown", "md"),
    "json": ("application/json", "json"),
}

# Only deterministic checks Agent Proof Runtime can actually reproduce.
# A planner may select from this list and may not invent anything else.
ACCEPTANCE_ALLOWLIST = {
    "artifact_present": frozenset({"type"}),
    "nonempty_text": frozenset({"type"}),
    "min_length": frozenset({"type", "min_bytes"}),
    "json_parseable": frozenset({"type"}),
    "json_required_keys": frozenset({"type", "keys"}),
}

VERIFICATION_SCOPE = ("execution", "artifact_integrity", "contract_acceptance")


class GenericPlanError(ValueError):
    """A mission plan violates the fixed GenericMissionPlanV1 contract."""

    def __init__(self, message: str, category: str = "planner_contract_invalid"):
        self.category = category
        super().__init__(message)


@dataclass(frozen=True)
class PlanStage:
    stage_id: str
    role: str
    instruction: str
    output_type: str
    acceptance: tuple[dict[str, Any], ...]
    inputs: tuple[str, ...]

    @property
    def media_type(self) -> str:
        return OUTPUT_TYPES[self.output_type][0]

    def artifact_path(self, index: int) -> str:
        return f"stage/{index + 1:02d}-{self.stage_id}.{OUTPUT_TYPES[self.output_type][1]}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.stage_id,
            "role": self.role,
            "instruction": self.instruction,
            "expected_output": {"type": self.output_type},
            "acceptance": [dict(item) for item in self.acceptance],
            "inputs": list(self.inputs),
        }


@dataclass(frozen=True)
class GenericMissionPlan:
    title: str
    goal: str
    stages: tuple[PlanStage, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": PLAN_VERSION,
            "title": self.title,
            "goal": self.goal,
            "stages": [stage.to_dict() for stage in self.stages],
        }


def normalized_prompt(value: Any) -> str:
    if not isinstance(value, str):
        raise GenericPlanError("prompt must be a string", "request_invalid")
    for character in value:
        if ord(character) < 32 and character not in {"\t", "\n", "\r"}:
            raise GenericPlanError("prompt contains a control character", "request_invalid")
        if ord(character) == 127:
            raise GenericPlanError("prompt contains a control character", "request_invalid")
    normalized = re.sub(r"\s+", " ", value.replace("\r\n", "\n")).strip()
    if len(normalized) < MIN_PROMPT_CHARS:
        raise GenericPlanError(
            f"prompt must contain at least {MIN_PROMPT_CHARS} characters", "request_invalid"
        )
    if len(normalized) > MAX_PROMPT_CHARS:
        raise GenericPlanError(
            f"prompt must contain at most {MAX_PROMPT_CHARS} characters", "request_invalid"
        )
    return normalized


def _text(value: Any, *, label: str, minimum: int, maximum: int) -> str:
    if not isinstance(value, str):
        raise GenericPlanError(f"{label} must be a string")
    cleaned = re.sub(r"\s+", " ", value).strip()
    if not minimum <= len(cleaned) <= maximum:
        raise GenericPlanError(f"{label} must be {minimum}-{maximum} characters")
    for character in cleaned:
        if ord(character) < 32 or ord(character) == 127:
            raise GenericPlanError(f"{label} contains a control character")
    return cleaned


def _acceptance_entry(value: Any, *, label: str, output_type: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GenericPlanError(f"{label} must be an object")
    check_type = value.get("type")
    expected = ACCEPTANCE_ALLOWLIST.get(check_type) if isinstance(check_type, str) else None
    if expected is None:
        raise GenericPlanError(f"{label}.type is not in the acceptance allowlist")
    if frozenset(value) != expected:
        raise GenericPlanError(f"{label} has unexpected fields for {check_type}")
    if check_type in {"json_parseable", "json_required_keys"} and output_type != "json":
        raise GenericPlanError(f"{label} requires an expected_output type of json")
    if check_type == "min_length":
        min_bytes = value.get("min_bytes")
        if not isinstance(min_bytes, int) or isinstance(min_bytes, bool):
            raise GenericPlanError(f"{label}.min_bytes must be an integer")
        if not 1 <= min_bytes <= STAGE_MAX_BYTES:
            raise GenericPlanError(f"{label}.min_bytes must be 1-{STAGE_MAX_BYTES}")
    if check_type == "json_required_keys":
        keys = value.get("keys")
        if (
            not isinstance(keys, list)
            or not 1 <= len(keys) <= 16
            or not all(isinstance(item, str) and 1 <= len(item) <= 64 for item in keys)
        ):
            raise GenericPlanError(f"{label}.keys must be 1-16 non-empty strings")
        if len(set(keys)) != len(keys):
            raise GenericPlanError(f"{label}.keys cannot contain duplicates")
    return {key: value[key] for key in sorted(value)}


def parse_mission_plan(value: Any, *, max_stages: int = MAX_STAGES) -> GenericMissionPlan:
    """Validate a planner response. A planner is never trusted."""

    if not isinstance(value, dict):
        raise GenericPlanError("plan must be a JSON object")
    allowed = {"version", "title", "goal", "stages"}
    if not allowed <= set(value) or set(value) - allowed:
        raise GenericPlanError("plan must contain exactly version, title, goal and stages")
    if value["version"] != PLAN_VERSION:
        raise GenericPlanError(f"plan.version must be {PLAN_VERSION}")
    title = _text(value["title"], label="plan.title", minimum=3, maximum=120)
    goal = _text(value["goal"], label="plan.goal", minimum=10, maximum=1000)

    stages_value = value["stages"]
    bound = max(1, min(max_stages, MAX_STAGES))
    if not isinstance(stages_value, list) or not 1 <= len(stages_value) <= bound:
        raise GenericPlanError(f"plan.stages must contain between 1 and {bound} stages")

    stages: list[PlanStage] = []
    seen: list[str] = []
    for index, raw in enumerate(stages_value):
        label = f"plan.stages[{index}]"
        if not isinstance(raw, dict):
            raise GenericPlanError(f"{label} must be an object")
        known = {"id", "role", "instruction", "expected_output", "acceptance", "inputs"}
        required = {"id", "role", "instruction", "expected_output", "acceptance"}
        if not required <= set(raw) or set(raw) - known:
            raise GenericPlanError(f"{label} has an invalid shape")

        stage_id = raw["id"]
        if not isinstance(stage_id, str) or not STAGE_ID.fullmatch(stage_id):
            raise GenericPlanError(f"{label}.id must match [a-z][a-z0-9_]{{1,31}}")
        if stage_id in seen:
            raise GenericPlanError(f"{label}.id is duplicated")

        role = raw["role"]
        if not isinstance(role, str) or not ROLE.fullmatch(role):
            raise GenericPlanError(f"{label}.role must be an uppercase label")
        instruction = _text(raw["instruction"], label=f"{label}.instruction", minimum=8, maximum=800)

        expected_output = raw["expected_output"]
        if not isinstance(expected_output, dict) or set(expected_output) != {"type"}:
            raise GenericPlanError(f"{label}.expected_output must contain only type")
        output_type = expected_output["type"]
        if output_type not in OUTPUT_TYPES:
            raise GenericPlanError(f"{label}.expected_output.type is not supported")

        acceptance_value = raw["acceptance"]
        if not isinstance(acceptance_value, list) or not 1 <= len(acceptance_value) <= 6:
            raise GenericPlanError(f"{label}.acceptance must contain 1-6 checks")
        acceptance = [
            _acceptance_entry(item, label=f"{label}.acceptance[{position}]", output_type=output_type)
            for position, item in enumerate(acceptance_value)
        ]
        if len({item["type"] for item in acceptance}) != len(acceptance):
            raise GenericPlanError(f"{label}.acceptance cannot repeat a check type")

        inputs_value = raw.get("inputs", [])
        if not isinstance(inputs_value, list) or len(inputs_value) > MAX_STAGES:
            raise GenericPlanError(f"{label}.inputs must be an array of earlier stage ids")
        for item in inputs_value:
            if not isinstance(item, str) or item not in seen:
                raise GenericPlanError(f"{label}.inputs must reference earlier stage ids")
        if len(set(inputs_value)) != len(inputs_value):
            raise GenericPlanError(f"{label}.inputs cannot contain duplicates")
        # A stage with no declared input still receives the previous artifact,
        # so the world shows a real chain rather than four detached stages.
        inputs = tuple(inputs_value) if inputs_value else ((seen[-1],) if seen else ())

        seen.append(stage_id)
        stages.append(
            PlanStage(
                stage_id=stage_id,
                role=role,
                instruction=instruction,
                output_type=output_type,
                acceptance=tuple(acceptance),
                inputs=inputs,
            )
        )
    return GenericMissionPlan(title=title, goal=goal, stages=tuple(stages))


def parse_plan_json(text: Any) -> GenericMissionPlan:
    if not isinstance(text, str) or not text.strip():
        raise GenericPlanError("the planner returned no output", "planner_invalid_json")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = item
        return result

    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```[a-zA-Z]*\n?", "", candidate)
        candidate = re.sub(r"\n?```$", "", candidate).strip()
    try:
        value = json.loads(candidate, object_pairs_hook=reject_duplicates)
    except (json.JSONDecodeError, ValueError, RecursionError) as error:
        raise GenericPlanError(
            f"the planner response is not valid JSON: {error}", "planner_invalid_json"
        ) from None
    return parse_mission_plan(value)


PLANNER_SYSTEM_PROMPT = f"""You design an execution plan for a verifiable agent runtime.
Return ONE JSON object and nothing else. No prose, no markdown fence.

Shape:
{{"version":"{PLAN_VERSION}","title":"...","goal":"...","stages":[
 {{"id":"lower_snake","role":"UPPERCASE ROLE","instruction":"what this stage must produce",
  "expected_output":{{"type":"text|markdown|json"}},
  "acceptance":[{{"type":"artifact_present"}},{{"type":"nonempty_text"}}],
  "inputs":["earlier_stage_id"]}}]}}

Rules:
- between 1 and {{max_stages}} stages, in execution order
- ids are unique, lower_snake, and inputs may only reference earlier stages
- acceptance entries may ONLY use: artifact_present, nonempty_text,
  min_length (with min_bytes), json_parseable, json_required_keys (with keys)
- json_parseable and json_required_keys require expected_output type json
- never invent an acceptance type, never claim a result, never request tools,
  shell access, file access or network access
- the plan describes work only; the runtime decides what is proven"""


def planner_user_prompt(prompt: str, max_stages: int) -> str:
    return json.dumps(
        {"task": prompt, "max_stages": max_stages},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def fixture_plan(prompt: str, max_stages: int) -> GenericMissionPlan:
    """Deterministic plan used by the offline fixture path.

    This is a fixture, not a model answer. It exists so the whole generic
    pipeline can be tested without a network or a credential.
    """

    catalogue = (
        ("analyze", "ANALYST", "Przeanalizuj zadanie i wypisz najważniejsze obserwacje.", "text"),
        ("critique", "CRITIC", "Wskaż trzy najważniejsze problemy wynikające z analizy.", "text"),
        ("rewrite", "REWRITER", "Przygotuj poprawioną wersję na podstawie wskazanych problemów.", "text"),
        ("review", "REVIEWER", "Podsumuj wprowadzone zmiany i oceń kompletność pracy.", "markdown"),
    )
    bound = max(1, min(max_stages, MAX_STAGES))
    selected = catalogue[:bound]
    stages = tuple(
        PlanStage(
            stage_id=stage_id,
            role=role,
            instruction=instruction,
            output_type=output_type,
            acceptance=(
                {"type": "artifact_present"},
                {"type": "nonempty_text"},
            )
            + (({"type": "min_length", "min_bytes": 80},) if position == len(selected) - 1 else ()),
            inputs=(selected[position - 1][0],) if position else (),
        )
        for position, (stage_id, role, instruction, output_type) in enumerate(selected)
    )
    return GenericMissionPlan(
        title="Misja fixture (deterministyczna)",
        goal=f"Wykonaj zadanie operatora w kontrolowanych etapach: {prompt}"[:1000],
        stages=stages,
    )


def fixture_stage_output(plan: GenericMissionPlan, stage: PlanStage, prompt: str) -> str:
    """Deterministic stage content. Derived from the prompt, never from a model."""

    if stage.output_type == "json":
        return json.dumps(
            {
                "stage": stage.stage_id,
                "role": stage.role,
                "prompt_hash": _digest(prompt),
                "note": "deterministic fixture output",
            },
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
    heading = "# " if stage.output_type == "markdown" else ""
    return (
        f"{heading}{stage.role}\n\n"
        f"Zadanie operatora: {prompt}\n\n"
        f"Instrukcja etapu: {stage.instruction}\n\n"
        f"Cel misji: {plan.goal}\n\n"
        "To jest deterministyczny wynik fixture. Nie pochodzi od modelu i nie jest "
        "twierdzeniem o poprawności merytorycznej. Agent Proof Runtime dowodzi tu "
        "wyłącznie wykonania etapu, integralności artefaktu i spełnienia "
        "zadeklarowanych, deterministycznych warunków akceptacji.\n"
    )


def build_manifest(
    plan: GenericMissionPlan,
    *,
    prompt: str,
    provider: str,
    model: str,
    mission_id: str | None = None,
    timeout_seconds: int = 60,
    max_output_tokens: int = 4096,
) -> BuildWeekMission:
    """Turn a validated plan into an ordinary apr.mission.v1 manifest.

    Everything downstream — runtime, chain, Merkle root, bundle, verifier —
    then treats a generic mission exactly like any other mission.
    """

    identifier = mission_id or f"generic-{uuid.uuid4().hex[:12]}"
    plan_payload = _plan_artifact(plan, prompt)
    artifacts: list[dict[str, Any]] = [
        {
            "path": PLAN_ARTIFACT_PATH,
            "media_type": "application/json",
            "max_bytes": PLAN_MAX_BYTES,
            "required": True,
            "fixture_content": plan_payload,
        }
    ]
    checks: list[dict[str, Any]] = [
        {"id": "plan_present", "type": "file_exists", "path": PLAN_ARTIFACT_PATH},
        {"id": "plan_json_valid", "type": "json_valid", "path": PLAN_ARTIFACT_PATH},
        {
            "id": "plan_keys_present",
            "type": "json_required_keys",
            "path": PLAN_ARTIFACT_PATH,
            "keys": ["version", "title", "goal", "stages", "prompt", "prompt_hash"],
        },
    ]
    media_types: set[str] = {"application/json"}

    for index, stage in enumerate(plan.stages):
        path = stage.artifact_path(index)
        media_types.add(stage.media_type)
        artifacts.append(
            {
                "path": path,
                "media_type": stage.media_type,
                "max_bytes": STAGE_MAX_BYTES,
                "required": True,
                "fixture_content": fixture_stage_output(plan, stage, prompt),
            }
        )
        for check in stage.acceptance:
            checks.append(_mapped_check(stage, index, path, check))

    checks.append(
        {
            "id": "artifact_count",
            "type": "file_count",
            "minimum": len(artifacts),
            "maximum": len(artifacts),
        }
    )

    manifest = {
        "schema_version": "apr.mission.v1",
        "mission_id": identifier,
        "title": plan.title,
        "goal": plan.goal,
        "provider": provider,
        "model": model,
        "artifact_contract": {
            "artifacts": artifacts,
            "max_files": len(artifacts),
            "max_total_bytes": PLAN_MAX_BYTES + STAGE_MAX_BYTES * len(plan.stages),
            "allowed_media_types": sorted(media_types),
        },
        "limits": {
            "provider_timeout_seconds": timeout_seconds,
            "max_output_tokens": max_output_tokens,
        },
        "acceptance_checks": checks,
        "analysis_policy": {"persist_reasoning": False, "allow_reasoning_summary": False},
    }
    try:
        return parse_build_week_mission(manifest)
    except MissionValidationError as error:
        raise GenericPlanError(
            "the plan does not produce a valid mission manifest: " + "; ".join(error.errors)
        ) from None


def _mapped_check(
    stage: PlanStage, index: int, path: str, check: dict[str, Any]
) -> dict[str, Any]:
    """Map an allowlisted plan check onto an existing runtime check type."""

    prefix = f"s{index + 1}_{stage.stage_id}"[:52]
    kind = check["type"]
    if kind == "artifact_present":
        return {"id": f"{prefix}_present", "type": "file_exists", "path": path}
    if kind == "nonempty_text":
        return {"id": f"{prefix}_nonempty", "type": "minimum_size", "path": path, "min_bytes": 1}
    if kind == "min_length":
        return {
            "id": f"{prefix}_minlen",
            "type": "minimum_size",
            "path": path,
            "min_bytes": int(check["min_bytes"]),
        }
    if kind == "json_parseable":
        return {"id": f"{prefix}_json", "type": "json_valid", "path": path}
    if kind == "json_required_keys":
        return {
            "id": f"{prefix}_jsonkeys",
            "type": "json_required_keys",
            "path": path,
            "keys": list(check["keys"]),
        }
    raise GenericPlanError(f"unsupported acceptance check: {kind}")


def _plan_artifact(plan: GenericMissionPlan, prompt: str) -> str:
    payload = dict(plan.to_dict())
    payload["prompt"] = prompt
    payload["prompt_hash"] = _digest(prompt)
    payload["verification_scope"] = list(VERIFICATION_SCOPE)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sanitize_stage_text(value: str, *, media_type: str) -> str:
    """Accept a model answer as an artifact body, or reject it outright."""

    if not isinstance(value, str) or not value.strip():
        raise GenericPlanError("the stage produced no output", "stage_failed")
    cleaned = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    for character in cleaned:
        if ord(character) < 32 and character not in {"\t", "\n"}:
            raise GenericPlanError("the stage output contains a control character", "stage_failed")
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    if media_type == "application/json":
        try:
            json.loads(cleaned)
        except (json.JSONDecodeError, RecursionError):
            raise GenericPlanError(
                "the stage promised JSON and did not return JSON", "stage_failed"
            ) from None
    body = cleaned + "\n"
    if len(body.encode("utf-8")) > STAGE_MAX_BYTES:
        raise GenericPlanError("the stage output exceeds its declared size", "stage_failed")
    return body


STAGE_SYSTEM_PROMPT = """You are one stage of a verifiable agent runtime.
Produce only the artifact content for your stage. No preamble, no markdown
fence, no commentary about being an AI. Never claim that your output has been
verified: a separate runtime decides that."""


class GenericStageProvider:
    """Runs plan stages and hands the finished artifacts to the APR runtime.

    ``propose`` returns every artifact at once, which is the contract the
    existing Build Week runtime already expects. Stage calls happen earlier,
    driven by the session so the world can show each one as it lands.
    """

    def __init__(
        self,
        *,
        plan: GenericMissionPlan,
        prompt: str,
        provider_name: str,
        client: ModelClient | None = None,
    ) -> None:
        self.plan = plan
        self.prompt = prompt
        self.name = provider_name
        self.client = client
        self.outputs: dict[str, str] = {}
        self.usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        self.latency_ms = 0
        self.resolved_model = "fixture-v1"
        self.response_id: str | None = None
        self.live_request = False

    def _stage_index(self, stage_id: str) -> int:
        for index, stage in enumerate(self.plan.stages):
            if stage.stage_id == stage_id:
                return index
        raise GenericPlanError(f"unknown stage: {stage_id}")

    def stage_user_prompt(self, stage: PlanStage) -> str:
        sections = [
            f"CEL MISJI:\n{self.plan.goal}",
            f"ZADANIE OPERATORA:\n{self.prompt}",
            f"TWOJA ROLA: {stage.role}",
            f"TWOJE ZADANIE:\n{stage.instruction}",
            f"WYMAGANY FORMAT WYJŚCIA: {stage.output_type}",
        ]
        for source in stage.inputs:
            if source in self.outputs:
                sections.append(f"ARTEFAKT ETAPU {source}:\n{self.outputs[source]}")
        return "\n\n".join(sections)

    def run_stage(self, stage_id: str) -> dict[str, Any]:
        index = self._stage_index(stage_id)
        stage = self.plan.stages[index]
        if self.client is None:
            body = fixture_stage_output(self.plan, stage, self.prompt)
        else:
            try:
                response = self.client.generate(
                    system=STAGE_SYSTEM_PROMPT,
                    user=self.stage_user_prompt(stage),
                    max_output_tokens=4096,
                    timeout_seconds=60,
                    json_only=stage.output_type == "json",
                )
            except ModelGatewayError:
                raise
            body = sanitize_stage_text(response.text, media_type=stage.media_type)
            self.resolved_model = response.resolved_model
            self.response_id = response.response_id or self.response_id
            self.latency_ms += response.latency_ms
            self.live_request = bool(getattr(self.client, "live", False))
            for key in self.usage:
                self.usage[key] += int(response.usage.get(key, 0))
        self.outputs[stage_id] = body
        return {
            "stage_id": stage_id,
            "role": stage.role,
            "artifact_path": stage.artifact_path(index),
            "output_hash": _digest(body),
            "size": len(body.encode("utf-8")),
        }

    def proposal(self) -> ArtifactProposal:
        artifacts = [
            ProposedArtifact(
                PLAN_ARTIFACT_PATH, "application/json", _plan_artifact(self.plan, self.prompt)
            )
        ]
        for index, stage in enumerate(self.plan.stages):
            body = self.outputs.get(stage.stage_id)
            if body is None:
                raise GenericPlanError(f"stage {stage.stage_id} produced no artifact", "stage_failed")
            artifacts.append(
                ProposedArtifact(stage.artifact_path(index), stage.media_type, body)
            )
        return ArtifactProposal(tuple(artifacts))

    def propose(self, mission: BuildWeekMission) -> ProviderResult:
        proposal = self.proposal()
        normalized = {
            "artifacts": sorted(
                (artifact.to_dict() for artifact in proposal.artifacts),
                key=lambda item: item["path"],
            )
        }
        implementation_status = (
            "DETERMINISTIC_FIXTURE"
            if self.client is None
            else ("LIVE_API_REQUEST_EXECUTED" if self.live_request
                  else "IMPLEMENTED BUT NOT LIVE-VALIDATED")
        )
        return ProviderResult(
            proposal=proposal,
            metadata={
                "provider": self.name,
                "requested_model": mission.model,
                "resolved_model": self.resolved_model,
                "response_id": self.response_id,
                "token_usage": dict(self.usage),
                "latency_ms": self.latency_ms,
                "input_hash": hash_json(mission.provider_input()),
                "response_hash": hash_json(normalized),
                "implementation_status": implementation_status,
            },
        )
