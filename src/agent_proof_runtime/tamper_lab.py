"""Disposable tamper demonstrations for verified runs."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from .bundle import load_bundle, write_bundle
from .validator import verify_bundle

TAMPER_CASES = ("artifact", "event", "metadata")


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(128 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def run_fingerprint(run_dir: Path) -> dict[str, str]:
    root = run_dir.resolve(strict=True)
    result: dict[str, str] = {}
    for candidate in sorted(run_dir.rglob("*")):
        relative = candidate.relative_to(run_dir).as_posix()
        if candidate.is_symlink():
            result[relative] = "symlink"
        elif candidate.is_file():
            resolved = candidate.resolve(strict=True)
            if not resolved.is_relative_to(root):
                raise ValueError("run contains a file outside its root")
            result[relative] = _file_hash(candidate)
    return result


def _mutate(copy_dir: Path, case: str) -> None:
    bundle_path = copy_dir / "proof-bundle.json"
    bundle = load_bundle(bundle_path)
    if case == "artifact":
        artifacts = bundle.get("artifacts")
        if not isinstance(artifacts, list) or not artifacts:
            raise ValueError("run has no artifact to tamper with")
        raw_path = artifacts[0].get("path")
        if not isinstance(raw_path, str):
            raise ValueError("run has no valid artifact path")
        target = copy_dir.joinpath(*raw_path.split("/"))
        with target.open("ab") as handle:
            handle.write(b"\nTAMPER-LAB\n")
    elif case == "event":
        events = bundle.get("events")
        if not isinstance(events, list) or not events or not isinstance(events[0], dict):
            raise ValueError("run has no event to tamper with")
        events[0]["type"] = "tamper.event_modified"
        write_bundle(bundle_path, bundle)
    elif case == "metadata":
        provider = bundle.get("provider")
        if isinstance(provider, dict) and isinstance(provider.get("resolved_model"), str):
            provider["resolved_model"] += "-tampered"
        else:
            run = bundle.get("run")
            if not isinstance(run, dict):
                raise ValueError("run has no critical metadata to tamper with")
            run["security_level"] = "tampered"
        write_bundle(bundle_path, bundle)
    else:
        raise ValueError("tamper case must be artifact, event, or metadata")


def run_tamper_case(run_dir: str | Path, case: str) -> dict[str, Any]:
    if case not in TAMPER_CASES:
        raise ValueError("tamper case must be artifact, event, or metadata")
    original = Path(run_dir)
    original_bundle = original / "proof-bundle.json"
    original_verification = verify_bundle(original_bundle)
    if not original_verification.valid:
        raise ValueError("Tamper Lab requires an originally verified run")
    before = run_fingerprint(original)
    with tempfile.TemporaryDirectory(prefix="apr-tamper-") as temporary:
        copy_dir = Path(temporary) / "run-copy"
        shutil.copytree(original, copy_dir, symlinks=True)
        _mutate(copy_dir, case)
        verification = verify_bundle(copy_dir / "proof-bundle.json")
        result = {
            "case": case,
            "status": verification.status,
            "errors": list(verification.errors),
            "original_status": original_verification.status,
            "original_preserved": run_fingerprint(original) == before,
            "copy_disposed": True,
        }
    result["original_preserved"] = result["original_preserved"] and (
        run_fingerprint(original) == before
    )
    if result["status"] != "FAILED":
        raise RuntimeError("tamper demonstration did not fail verification")
    if not result["original_preserved"]:
        raise RuntimeError("Tamper Lab changed the original run")
    return result
