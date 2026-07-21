"""Deterministic upstream orchestration for APR Mission Studio.

The upstream stages produce a constrained artifact proposal. Agent Proof Runtime
remains the only runtime, evidence recorder, trust gate, and proof generator.
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import re
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from importlib import resources
from pathlib import Path
from typing import Any

from .build_week_runtime import (
    ArtifactPolicyError,
    run_build_week_mission,
    validate_proposal,
)
from .canonical import hash_json
from .mission import MissionValidationError
from .mission_v1 import BuildWeekMission, load_build_week_mission
from .mission_studio_openai import (
    MissionStudioOpenAIError,
    MissionStudioOpenAIProvider,
    configured_openai_model,
)
from .providers import (
    ArtifactProposal,
    ProposedArtifact,
    ProviderError,
    ProviderResult,
)

MISSION_TYPE = "verified_website_build"
STUDIO_SESSION = re.compile(r"^studio-[0-9a-f]{32}$")
STAGES = (
    ("planner", "Mission Planner Agent", "planning"),
    ("research", "Research Agent", "researching"),
    ("content", "Content Architect Agent", "architecting_content"),
    ("html_builder", "HTML Builder Agent", "building_markup"),
    ("css_builder", "CSS Designer Agent", "styling"),
    ("data_builder", "Data Builder Agent", "building_data"),
    ("qa", "QA Agent", "qa"),
)
ARTIFACT_PATHS = (
    "site/index.html",
    "site/styles.css",
    "site/data.json",
    "studio/trace.json",
)
MEDIA_TYPES = {
    "site/index.html": "text/html",
    "site/styles.css": "text/css",
    "site/data.json": "application/json",
    "studio/trace.json": "application/json",
}
PACKAGED_MANIFEST = ("data", "verified-website-build.json")
LOGGER = logging.getLogger(__name__)
FAILURE_MESSAGES = {
    "manifest_unavailable": "The packaged Mission Studio manifest is unavailable.",
    "manifest_invalid": "The packaged Mission Studio manifest is invalid.",
    "artifact_contract_rejected": "APR rejected the proposed artifact contract.",
    "provider_failed": "The deterministic artifact provider failed.",
    "openai_key_absent": "Live mode is unavailable because the server API key is absent.",
    "openai_sdk_unavailable": "Live mode is unavailable because the OpenAI SDK is not installed.",
    "openai_request_failed": "The OpenAI stage request failed.",
    "openai_timeout": "The OpenAI stage request timed out.",
    "openai_connection_failed": "The OpenAI stage could not establish a connection.",
    "openai_rate_limited": "The OpenAI stage was rate limited.",
    "openai_server_error": "The OpenAI service returned a server error.",
    "openai_auth_failed": "The OpenAI server credentials were rejected.",
    "openai_permission_denied": "The OpenAI request was not permitted.",
    "openai_bad_request": "The OpenAI stage request was rejected.",
    "structured_output_invalid": "The OpenAI stage returned invalid structured output.",
    "structured_output_truncated": "The OpenAI stage output exceeded its output budget.",
    "structured_output_refused": "The OpenAI stage output was stopped by content filtering.",
    "structured_output_incomplete": "The OpenAI stage returned an incomplete response.",
    "stage_contract_rejected": "The OpenAI stage output violated its fixed contract.",
    "runtime_io_failed": "APR could not materialize the Mission Studio run.",
    "runtime_failed": "Mission Studio could not complete the APR run.",
}


class MissionStudioValidationError(ValueError):
    """A Mission Studio request violates the fixed v1 request contract."""


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _json_text(value: Any) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) + "\n"


def _text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def load_packaged_mission() -> BuildWeekMission:
    """Load the fixed manifest from installed package resources."""

    resource = resources.files("agent_proof_runtime").joinpath(*PACKAGED_MANIFEST)
    with resources.as_file(resource) as manifest_path:
        return load_build_week_mission(manifest_path)


def _failure_category(error: Exception) -> str:
    if isinstance(error, MissionStudioOpenAIError):
        return error.category
    if isinstance(error, FileNotFoundError):
        return "manifest_unavailable"
    if isinstance(error, MissionValidationError):
        return "manifest_invalid"
    if isinstance(error, ArtifactPolicyError):
        return "artifact_contract_rejected"
    if isinstance(error, ProviderError):
        return "provider_failed"
    if isinstance(error, OSError):
        return "runtime_io_failed"
    return "runtime_failed"


def _normalized_brief(value: Any) -> str:
    if not isinstance(value, str):
        raise MissionStudioValidationError("brief must be a string")
    if "\x00" in value:
        raise MissionStudioValidationError("brief must not contain NUL")
    for character in value:
        if ord(character) < 32 and character not in {"\t", "\n", "\r"}:
            raise MissionStudioValidationError(
                "brief contains a disallowed control character"
            )
        if ord(character) == 127:
            raise MissionStudioValidationError(
                "brief contains a disallowed control character"
            )
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\s+", " ", normalized, flags=re.UNICODE).strip()
    if len(normalized) < 10:
        raise MissionStudioValidationError(
            "normalized brief must contain at least 10 characters"
        )
    if len(normalized) > 2000:
        raise MissionStudioValidationError(
            "normalized brief must contain at most 2000 characters"
        )
    return normalized


@dataclass(frozen=True)
class MissionStudioRequest:
    mission_type: str
    brief: str
    provider: str = "fixture"

    @classmethod
    def parse(cls, value: Any) -> "MissionStudioRequest":
        if not isinstance(value, dict):
            raise MissionStudioValidationError("request must be a JSON object")
        if set(value) not in (
            {"mission_type", "brief"},
            {"mission_type", "brief", "provider"},
        ):
            raise MissionStudioValidationError(
                "request must contain mission_type, brief, and optional provider"
            )
        if value["mission_type"] != MISSION_TYPE:
            raise MissionStudioValidationError(
                f"mission_type must equal {MISSION_TYPE}"
            )
        provider = value.get("provider", "fixture")
        if provider not in {"fixture", "openai"}:
            raise MissionStudioValidationError(
                "provider must equal fixture or openai"
            )
        return cls(
            mission_type=MISSION_TYPE,
            brief=_normalized_brief(value["brief"]),
            provider=provider,
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "mission_type": self.mission_type,
            "brief": self.brief,
            "provider": self.provider,
        }


def _page_data(request: MissionStudioRequest) -> dict[str, Any]:
    lowered = request.brief.casefold()
    security = "security" in lowered or "secure" in lowered or "cyber" in lowered
    product_name = "Aegis AI" if security else "Signal AI"
    headline = (
        "Secure every AI workflow."
        if security
        else "Turn intelligent work into trusted outcomes."
    )
    return {
        "schema_version": "apr.verified-website-build.data.v1",
        "product_name": product_name,
        "eyebrow": "AI OPERATIONS / VERIFIABLE DELIVERY",
        "headline": headline,
        "description": request.brief,
        "cta": "Request a security review" if security else "Start a verified build",
        "features": [
            {
                "title": "Constrained by design",
                "description": "Declared artifacts and exact paths keep delivery inside a visible contract.",
            },
            {
                "title": "Evidence at every step",
                "description": "Hashes, event-chain data, and acceptance results make changes detectable.",
            },
            {
                "title": "Verified independently",
                "description": "A deterministic verifier recomputes bundle integrity without an LLM.",
            },
        ],
    }


def _stage_results(request: MissionStudioRequest) -> tuple[dict[str, Any], ...]:
    data = _page_data(request)
    outputs = (
        {
            "page_goal": "Produce one responsive static landing page.",
            "sections": ["hero", "features", "cta"],
            "constraints": [
                "exactly three feature cards",
                "no remote assets or scripts",
                "four declared artifacts only",
            ],
        },
        {
            "research_mode": "deterministic_fixture_demo",
            "audience": "Teams evaluating verifiable AI-enabled delivery",
            "content_signals": [
                "clear value proposition",
                "trust boundary language",
                "single primary call to action",
            ],
        },
        {
            "content_model": "verified_website_content_v1",
            "feature_count": len(data["features"]),
            "trust_point_count": 3,
        },
        {
            "artifact_path": "site/index.html",
            "page_structure": ["hero", "features", "cta"],
            "semantic": True,
        },
        {
            "artifact_path": "site/styles.css",
            "responsive": True,
            "external_dependencies": 0,
        },
        {
            "artifact_path": "site/data.json",
            "valid_json": True,
            "schema_version": data["schema_version"],
        },
        {
            "checks": [
                "semantic section markers present",
                "exactly three feature cards",
                "user-derived HTML escaped",
                "no remote assets or scripts",
            ],
            "verdict": "ready_for_apr_handoff",
            "proof_status": None,
        },
    )
    results: list[dict[str, Any]] = []
    for (stage_id, stage_name, _), output in zip(STAGES, outputs, strict=True):
        results.append(
            {
                "stage_id": stage_id,
                "stage_name": stage_name,
                "summary": {
                    "planner": "Locked the fixed website structure and artifact constraints.",
                    "research": "Prepared deterministic fixture content signals for the page.",
                    "content": "Structured the verified website content model.",
                    "html_builder": "Prepared the declared semantic HTML artifact.",
                    "css_builder": "Prepared the declared responsive CSS artifact.",
                    "data_builder": "Prepared the declared structured data artifact.",
                    "qa": "Reviewed structure and safety before APR handoff.",
                }[stage_id],
                "output": output,
                "output_hash": hash_json(output),
                "status": "completed",
            }
        )
    return tuple(results)


def _handoffs(stages: tuple[dict[str, Any], ...]) -> tuple[dict[str, str], ...]:
    destinations = (*[stage[0] for stage in STAGES[1:]], "apr")
    return tuple(
        {
            "source_stage": stage["stage_id"],
            "destination_stage": destination,
            "output_hash": stage["output_hash"],
        }
        for stage, destination in zip(stages, destinations, strict=True)
    )


def _index_html(data: dict[str, Any]) -> str:
    escaped = {
        key: html.escape(str(data[key]), quote=True)
        for key in ("product_name", "eyebrow", "headline", "description", "cta")
    }
    feature_html = "\n".join(
        """        <article class="feature-card">
          <span class="feature-index">0{index}</span>
          <h3>{title}</h3>
          <p>{description}</p>
        </article>""".format(
            index=index,
            title=html.escape(feature["title"], quote=True),
            description=html.escape(feature["description"], quote=True),
        )
        for index, feature in enumerate(data["features"], start=1)
    )
    return f"""<!doctype html>
<html lang="en" data-apr-build="verified-website-build-v1">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped['product_name']} — Verifiable AI delivery</title>
  <meta name="description" content="{escaped['description']}">
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header class="site-header"><a class="brand" href="#top">{escaped['product_name']}</a><a class="text-link" href="#contact">Contact</a></header>
  <main id="top">
    <section class="hero" data-apr-section="hero">
      <p class="eyebrow">{escaped['eyebrow']}</p>
      <h1>{escaped['headline']}</h1>
      <p class="lede">{escaped['description']}</p>
      <a class="button" href="#contact">{escaped['cta']}</a>
    </section>
    <section class="features" data-apr-section="features" aria-labelledby="features-title">
      <div><p class="eyebrow">THREE CONTROL LAYERS</p><h2 id="features-title">Built for work that must hold up.</h2></div>
      <div class="feature-grid">
{feature_html}
      </div>
    </section>
    <section class="cta" id="contact" data-apr-section="cta" aria-labelledby="cta-title">
      <p class="eyebrow">READY FOR REVIEW</p>
      <h2 id="cta-title">Move from intent to evidence.</h2>
      <a class="button button-light" href="mailto:hello@example.invalid">{escaped['cta']}</a>
    </section>
  </main>
  <footer><span>{escaped['product_name']}</span><span>Static / local / verifiable</span></footer>
</body>
</html>
"""


def _styles_css() -> str:
    return """*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:#050609;color:#f4f7f8;font-family:Arial,Helvetica,sans-serif;line-height:1.5}a{color:inherit}.site-header,main,footer{width:min(1120px,calc(100% - 40px));margin-inline:auto}.site-header{height:76px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #242831}.brand{font-weight:800;text-decoration:none;letter-spacing:-.03em}.text-link{color:#aab1bd;text-underline-offset:5px}.hero{min-height:680px;display:grid;align-content:center;max-width:900px}.eyebrow{color:#79f2c0;font:700 12px/1.3 monospace;letter-spacing:.18em}.hero h1{font-size:clamp(52px,8vw,108px);line-height:.92;letter-spacing:-.065em;margin:24px 0}.lede{max-width:720px;color:#b9c0cb;font-size:clamp(18px,2vw,23px)}.button{display:inline-flex;width:max-content;margin-top:30px;padding:15px 21px;background:#79f2c0;color:#07110d;text-decoration:none;font-weight:800;border-radius:4px}.features{padding:120px 0;border-top:1px solid #242831}.features h2,.cta h2{font-size:clamp(36px,5vw,68px);line-height:1;letter-spacing:-.045em;max-width:760px}.feature-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:56px}.feature-card{min-height:260px;padding:28px;background:#0c0f14;border:1px solid #242831}.feature-index{color:#79f2c0;font:700 12px monospace}.feature-card h3{font-size:23px;margin:70px 0 12px}.feature-card p{color:#aab1bd}.cta{margin-bottom:80px;padding:80px;background:#111720;border:1px solid #303744}.button-light{background:#f4f7f8;color:#080a0d}footer{display:flex;justify-content:space-between;padding:28px 0 42px;color:#7f8793;border-top:1px solid #242831;font:700 11px monospace;text-transform:uppercase;letter-spacing:.12em}@media(max-width:760px){.site-header,main,footer{width:min(100% - 24px,1120px)}.hero{min-height:590px}.feature-grid{grid-template-columns:1fr}.features{padding:80px 0}.cta{padding:48px 24px}.feature-card{min-height:220px}}
"""


class MissionStudioFixtureProvider:
    """ArtifactProvider-compatible, offline provider for the fixed v1 mission."""

    name = "fixture"

    def __init__(self, request: MissionStudioRequest) -> None:
        self.request = request
        self.stages = _stage_results(request)
        self.handoffs = _handoffs(self.stages)
        page_data = _page_data(request)
        trace = {
            "schema_version": "apr.mission-studio.trace.v1",
            "mission_type": request.mission_type,
            "brief_hash": _text_hash(request.brief),
            "agent_order": [stage[0] for stage in STAGES],
            "stages": list(self.stages),
            "handoffs": list(self.handoffs),
            "artifact_contract": {
                "paths": list(ARTIFACT_PATHS),
                "file_count": 4,
            },
        }
        self.proposal = ArtifactProposal(
            (
                ProposedArtifact("site/index.html", "text/html", _index_html(page_data)),
                ProposedArtifact("site/styles.css", "text/css", _styles_css()),
                ProposedArtifact("site/data.json", "application/json", _json_text(page_data)),
                ProposedArtifact("studio/trace.json", "application/json", _json_text(trace)),
            )
        )

    def propose(self, mission: Any) -> ProviderResult:
        normalized_proposal = {
            "artifacts": sorted(
                (artifact.to_dict() for artifact in self.proposal.artifacts),
                key=lambda item: item["path"],
            )
        }
        return ProviderResult(
            proposal=self.proposal,
            metadata={
                "provider": self.name,
                "requested_model": mission.model,
                # The existing verifier intentionally pins fixture provider
                # metadata to this resolved model identifier.
                "resolved_model": "fixture-v1",
                "response_id": None,
                "token_usage": {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                },
                "latency_ms": 0,
                "input_hash": hash_json(mission.provider_input()),
                "response_hash": hash_json(normalized_proposal),
                "implementation_status": "DETERMINISTIC_FIXTURE",
            },
        )


class MissionStudioManager:
    """Thread-safe backend-owned sessions for the fixed Mission Studio flow."""

    def __init__(
        self,
        *,
        runs_dir: Path,
        run_lock: threading.Lock,
        stage_delay_seconds: float = 0.08,
        openai_client: Any | None = None,
    ) -> None:
        self.runs_dir = runs_dir
        self.run_lock = run_lock
        self.stage_delay_seconds = max(0.0, stage_delay_seconds)
        self.openai_client = openai_client
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def start(self, value: Any) -> dict[str, Any]:
        request = MissionStudioRequest.parse(value)
        model = (
            "fixture-v1"
            if request.provider == "fixture"
            else configured_openai_model()
        )
        if not self.run_lock.acquire(blocking=False):
            raise RuntimeError("another mission is already running")
        session_id = "studio-" + uuid.uuid4().hex
        session = {
            "session_id": session_id,
            "mission_type": request.mission_type,
            "brief": request.brief,
            "provider": request.provider,
            "model": model,
            "state": "queued",
            "progress": 0,
            "current_stage": None,
            "current_output_hash": None,
            "current_handoff": None,
            "agents": [
                {
                    "stage_id": stage_id,
                    "stage_name": stage_name,
                    "status": "ready",
                    "output_hash": None,
                }
                for stage_id, stage_name, _ in STAGES
            ],
            "apr": {"status": "AWAITING ARTIFACT"},
            "events": [
                {
                    "id": "event-001",
                    "type": "studio.mission_accepted",
                    "timestamp": _timestamp(),
                    "summary": "The fixed verified website mission was accepted.",
                }
            ],
            "apr_run_id": None,
            "mission_status": None,
            "proof_status": None,
            "anchor_status": None,
            "failure_category": None,
            "error": None,
        }
        with self._lock:
            self._sessions[session_id] = session
        thread = threading.Thread(
            target=self._run, args=(session_id, request), daemon=True
        )
        try:
            thread.start()
        except Exception:
            self.run_lock.release()
            with self._lock:
                self._sessions.pop(session_id, None)
            raise
        return self.get(session_id)

    def get(self, session_id: str) -> dict[str, Any]:
        if not isinstance(session_id, str) or not STUDIO_SESSION.fullmatch(session_id):
            raise ValueError("invalid Mission Studio session id")
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise KeyError(session_id)
            return json.loads(json.dumps(session, ensure_ascii=False))

    def _update(self, session_id: str, **values: Any) -> None:
        with self._lock:
            self._sessions[session_id].update(values)

    def _agent(self, session_id: str, stage_id: str, **values: Any) -> None:
        with self._lock:
            for agent in self._sessions[session_id]["agents"]:
                if agent["stage_id"] == stage_id:
                    agent.update(values)
                    break

    def _event(self, session_id: str, event_type: str, **values: Any) -> None:
        with self._lock:
            events = self._sessions[session_id]["events"]
            events.append(
                {
                    "id": f"event-{len(events) + 1:03d}",
                    "type": event_type,
                    "timestamp": _timestamp(),
                    **values,
                }
            )

    def _pause(self) -> None:
        if self.stage_delay_seconds:
            time.sleep(self.stage_delay_seconds)

    def _run(self, session_id: str, request: MissionStudioRequest) -> None:
        try:
            provider: Any
            if request.provider == "fixture":
                provider = MissionStudioFixtureProvider(request)
            else:
                provider = MissionStudioOpenAIProvider(
                    request, client=self.openai_client
                )
            completed_progress = tuple(
                round(72 * (index + 1) / len(STAGES))
                for index in range(len(STAGES))
            )
            for index, (stage_id, stage_name, state) in enumerate(STAGES):
                self._update(
                    session_id,
                    state=state,
                    progress=max(1, completed_progress[index] - 10),
                    current_stage=stage_id,
                    current_handoff=None,
                )
                self._agent(session_id, stage_id, status="working")
                self._event(
                    session_id,
                    f"agent.{stage_id}.started",
                    stage_id=stage_id,
                    stage_name=stage_name,
                )
                if request.provider == "fixture":
                    self._pause()
                    result = provider.stages[index]
                    handoff = provider.handoffs[index]
                else:
                    result = provider.run_stage(stage_id)
                    handoff = {
                        "source_stage": stage_id,
                        "destination_stage": (
                            STAGES[index + 1][0]
                            if index + 1 < len(STAGES)
                            else "apr"
                        ),
                        "output_hash": result["output_hash"],
                    }
                self._agent(
                    session_id,
                    stage_id,
                    status="completed",
                    output_hash=result["output_hash"],
                )
                self._update(
                    session_id,
                    progress=completed_progress[index],
                    current_output_hash=result["output_hash"],
                )
                self._event(
                    session_id,
                    f"agent.{stage_id}.completed",
                    stage_id=stage_id,
                    stage_name=stage_name,
                    summary=result["summary"],
                    structured_output=result.get("event_output", result["output"]),
                    output_hash=result["output_hash"],
                    status="completed",
                )
                destination = handoff["destination_stage"]
                handoff_type = f"handoff.{stage_id}_to_{destination}"
                self._agent(session_id, stage_id, status="handing_off")
                self._update(session_id, current_handoff=handoff)
                self._event(session_id, handoff_type, **handoff)
                self._pause()
                self._agent(session_id, stage_id, status="completed")

            self._update(
                session_id,
                state="handoff_to_apr",
                progress=78,
                current_stage="apr",
                apr={"status": "ENFORCING CONTRACT"},
            )
            self._event(session_id, "apr.run.started")
            mission = load_packaged_mission()
            validate_proposal(mission, provider.proposal)
            self._event(
                session_id,
                "apr.contract_enforced",
                artifact_count=len(provider.proposal.artifacts),
            )
            self._update(
                session_id,
                state="apr_verifying",
                progress=84,
                apr={"status": "RECORDING EVIDENCE"},
            )
            self._pause()
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            run_name = f"{stamp}-verified-website-build-{uuid.uuid4().hex[:8]}"
            result = run_build_week_mission(
                mission,
                self.runs_dir / run_name,
                provider_name=request.provider,
                provider=provider,
            )
            self._event(session_id, "apr.run.completed", run_id=run_name)
            self._update(
                session_id,
                progress=94,
                apr={"status": "VERIFYING"},
                apr_run_id=run_name,
            )
            self._pause()
            verification = result.verification
            self._event(
                session_id,
                "verifier.completed",
                status=verification.status,
                anchor_status=verification.anchor_status,
            )
            completed = (
                result.mission_status == "PASSED"
                and verification.status == "LOCAL_VERIFIED"
            )
            self._update(
                session_id,
                state="completed" if completed else "failed",
                progress=100,
                current_handoff=None,
                mission_status=result.mission_status,
                proof_status=verification.status,
                anchor_status=verification.anchor_status,
                apr={"status": verification.status},
            )
        except Exception as error:
            failure_category = _failure_category(error)
            failure_diagnostics: dict[str, Any] | None = None
            if isinstance(error, MissionStudioOpenAIError):
                failure_diagnostics = error.safe_diagnostics()
                LOGGER.warning(
                    "mission_studio_openai_failure %s",
                    json.dumps(
                        failure_diagnostics,
                        ensure_ascii=True,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
            with self._lock:
                session = self._sessions[session_id]
                session.update(
                    state="failed",
                    current_handoff=None,
                    proof_status="FAILED",
                    apr={"status": "FAILED"},
                    failure_category=failure_category,
                    error=FAILURE_MESSAGES[failure_category],
                )
                if failure_diagnostics is not None:
                    session["failure_diagnostics"] = failure_diagnostics
                for agent in session["agents"]:
                    if agent["status"] in {"working", "handing_off"}:
                        agent["status"] = "failed"
                events = session["events"]
                failed_event = {
                    "id": f"event-{len(events) + 1:03d}",
                    "type": "studio.mission_failed",
                    "timestamp": _timestamp(),
                    "category": failure_category,
                }
                if failure_diagnostics is not None:
                    failed_event.update(failure_diagnostics)
                events.append(failed_event)
        finally:
            self.run_lock.release()
