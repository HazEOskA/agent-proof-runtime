"""Controlled artifact runtime for apr.mission.v1."""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .acceptance import evaluate_acceptance
from .bundle import SCHEMA_VERSION_BUILD_WEEK, compute_bundle_hash, write_bundle
from .canonical import CANONICALIZATION_PROFILE, HASH_ALGORITHM
from .chain import EventChain
from .merkle import merkle_root_from_step_hashes
from .mission_v1 import BuildWeekMission, load_build_week_mission
from .providers import ArtifactProposal, ArtifactProvider, provider_for
from .report import write_report
from .runtime import DemoRunResult, RunDirectoryExists
from .validator import verify_bundle


class ArtifactPolicyError(ValueError):
    """A proposal violates the declarative artifact contract."""


def _timestamp() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def validate_proposal(mission: BuildWeekMission, proposal: ArtifactProposal) -> None:
    contract = mission.artifact_contract
    if len(proposal.artifacts) > contract.max_files:
        raise ArtifactPolicyError("proposal exceeds artifact_contract.max_files")
    declared = {item.path: item for item in contract.artifacts}
    seen: set[str] = set()
    total = 0
    for artifact in proposal.artifacts:
        if artifact.path in seen:
            raise ArtifactPolicyError(f"proposal duplicates artifact path {artifact.path}")
        seen.add(artifact.path)
        expected = declared.get(artifact.path)
        if expected is None:
            raise ArtifactPolicyError(f"proposal path is not allowlisted: {artifact.path}")
        if artifact.media_type != expected.media_type:
            raise ArtifactPolicyError(
                f"proposal media type does not match contract for {artifact.path}"
            )
        if artifact.media_type not in contract.allowed_media_types:
            raise ArtifactPolicyError(f"proposal media type is not allowed: {artifact.media_type}")
        data = artifact.content.encode("utf-8")
        if len(data) > expected.max_bytes:
            raise ArtifactPolicyError(f"proposal artifact exceeds max_bytes: {artifact.path}")
        total += len(data)
    missing = sorted(
        item.path for item in contract.artifacts if item.required and item.path not in seen
    )
    if missing:
        raise ArtifactPolicyError("proposal is missing required artifacts: " + ", ".join(missing))
    if total > contract.max_total_bytes:
        raise ArtifactPolicyError("proposal exceeds artifact_contract.max_total_bytes")


def _materialize(
    destination: Path, mission: BuildWeekMission, proposal: ArtifactProposal
) -> list[dict[str, Any]]:
    artifact_root = destination / "artifact"
    artifact_root.mkdir(parents=False, exist_ok=False)
    declared = {item.path: item for item in mission.artifact_contract.artifacts}
    artifacts: list[dict[str, Any]] = []
    for proposed in sorted(proposal.artifacts, key=lambda item: item.path):
        target = artifact_root.joinpath(*proposed.path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or target.exists():
            raise ArtifactPolicyError(f"refusing to overwrite artifact path: {proposed.path}")
        data = proposed.content.encode("utf-8")
        with target.open("xb") as handle:
            handle.write(data)
        if target.is_symlink() or not target.is_file():
            raise ArtifactPolicyError(f"artifact is not a regular file: {proposed.path}")
        artifacts.append(
            {
                "path": "artifact/" + proposed.path,
                "media_type": declared[proposed.path].media_type,
                "size": len(data),
                "sha256": _digest(data),
            }
        )
    return artifacts


def run_build_week_mission(
    mission: str | Path | BuildWeekMission,
    output_dir: str | Path,
    *,
    provider_name: str | None = None,
    provider: ArtifactProvider | None = None,
) -> DemoRunResult:
    spec = (
        load_build_week_mission(mission)
        if not isinstance(mission, BuildWeekMission)
        else mission
    )
    selected_provider = provider_name or spec.provider
    if selected_provider not in {"fixture", "openai"}:
        raise ValueError("provider override must be fixture or openai")
    artifact_provider = provider or provider_for(selected_provider)
    if artifact_provider.name != selected_provider:
        raise ValueError("injected provider name does not match selected provider")

    destination = Path(output_dir)
    if destination.exists():
        raise RunDirectoryExists(f"run directory already exists: {destination}")

    # No run directory is created until the provider returns a policy-valid proposal.
    provider_result = artifact_provider.propose(spec)
    validate_proposal(spec, provider_result.proposal)

    started_monotonic = time.monotonic()
    started_at = _timestamp()
    run_id = str(uuid.uuid4())
    network_policy = "fixture-offline" if selected_provider == "fixture" else "provider-api-only"
    run_metadata = {
        "run_id": run_id,
        "sandbox_backend": "controlled-artifact-runtime",
        "security_level": "development-only",
        "network_policy": network_policy,
    }
    destination.mkdir(parents=True, exist_ok=False)
    chain = EventChain()
    chain.append(
        "runtime.mission_started",
        event_input={"mission_id": spec.mission_id, "manifest_hash": spec.manifest_hash},
        event_output={"workspace": "created"},
        details=run_metadata,
    )
    chain.append(
        "provider.artifact_proposal_received",
        event_input={
            "provider": selected_provider,
            "requested_model": provider_result.metadata["requested_model"],
            "input_hash": provider_result.metadata["input_hash"],
        },
        event_output={
            "artifact_count": len(provider_result.proposal.artifacts),
            "response_hash": provider_result.metadata["response_hash"],
        },
        details=provider_result.metadata,
    )
    artifacts = _materialize(destination, spec, provider_result.proposal)
    for artifact in artifacts:
        chain.append(
            "runtime.artifact_materialized",
            event_input={"path": artifact["path"], "media_type": artifact["media_type"]},
            event_output=artifact,
            details={"materializer": "controlled-text-v1", "policy_enforced": True},
        )

    checks = evaluate_acceptance(spec, destination / "artifact")
    mission_status = "PASSED" if all(check["passed"] for check in checks) else "FAILED"
    acceptance = {"status": mission_status, "checks": checks}
    chain.append(
        "runtime.acceptance_completed",
        event_input={"check_count": len(checks)},
        event_output=acceptance,
        details={"artifact_count": len(artifacts), "evaluator": "deterministic-v1"},
    )
    events = chain.events
    # This is only a runtime claim. The independent verifier recomputes validity;
    # a faithfully recorded failed mission can still have a valid local proof.
    claimed_status = "LOCAL_VERIFIED"
    bundle: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION_BUILD_WEEK,
        "mission": {"manifest": spec.to_dict(), "manifest_hash": spec.manifest_hash},
        "provider": provider_result.metadata,
        "run": {
            **run_metadata,
            "started_at": started_at,
            "finished_at": _timestamp(),
            "duration_ms": max(0, int((time.monotonic() - started_monotonic) * 1000)),
        },
        "events": events,
        "artifacts": artifacts,
        "acceptance": acceptance,
        "verification": {"claimed_status": claimed_status},
        "integrity": {
            "canonicalization": CANONICALIZATION_PROFILE,
            "hash_algorithm": HASH_ALGORITHM,
            "event_count": len(events),
            "event_merkle_root": merkle_root_from_step_hashes(
                [event["step_hash"] for event in events]
            ),
            "anchor_status": "UNANCHORED",
        },
    }
    bundle["integrity"]["bundle_hash"] = compute_bundle_hash(bundle)
    bundle_path = destination / "proof-bundle.json"
    write_bundle(bundle_path, bundle)
    verification = verify_bundle(bundle_path)
    report_path = destination / "report.html"
    write_report(report_path, bundle, verification)
    return DemoRunResult(
        output_dir=destination,
        bundle_path=bundle_path,
        report_path=report_path,
        mission_status=mission_status,
        verification=verification,
    )
