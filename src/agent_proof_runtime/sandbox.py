"""Development-only local process sandbox backend."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

BACKEND_NAME = "local-process"
SECURITY_LEVEL = "development-only"
NETWORK_POLICY = "not-enforced"
MAX_ARTIFACT_FILES = 100
MAX_ARTIFACT_BYTES = 5 * 1024 * 1024


class SandboxPolicyError(RuntimeError):
    pass


@dataclass(frozen=True)
class SandboxResult:
    return_code: int
    duration_ms: int
    events: list[dict[str, Any]]
    protocol_errors: list[str]
    stderr: str


def _linux_resource_limiter() -> Callable[[], None] | None:
    if sys.platform != "linux":
        return None

    def apply_limits() -> None:
        import resource

        resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
        resource.setrlimit(resource.RLIMIT_FSIZE, (2 * 1024 * 1024, 2 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))

    return apply_limits


def _parse_worker_events(stdout: str) -> tuple[list[dict[str, Any]], list[str]]:
    events: list[dict[str, Any]] = []
    errors: list[str] = []
    required = {"type", "input", "output", "details"}
    for line_number, line in enumerate(stdout.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            errors.append(f"worker stdout line {line_number} is not JSON: {error.msg}")
            continue
        if not isinstance(value, dict) or set(value) != required:
            errors.append(f"worker stdout line {line_number} violates the event protocol")
            continue
        if not isinstance(value["type"], str) or not value["type"]:
            errors.append(f"worker stdout line {line_number} has an invalid event type")
            continue
        events.append(value)
    return events, errors


def copy_artifacts(
    source: Path,
    destination: Path,
    *,
    max_files: int = MAX_ARTIFACT_FILES,
    max_bytes: int = MAX_ARTIFACT_BYTES,
) -> None:
    if not source.exists():
        return
    destination.mkdir(parents=True, exist_ok=False)
    file_count = 0
    total_bytes = 0
    for item in source.rglob("*"):
        if item.is_symlink():
            raise SandboxPolicyError("agent artifacts cannot contain symbolic links")
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not item.is_file():
            raise SandboxPolicyError("agent artifacts must be regular files")
        file_count += 1
        total_bytes += item.stat().st_size
        if file_count > max_files:
            raise SandboxPolicyError("artifact file-count limit exceeded")
        if total_bytes > max_bytes:
            raise SandboxPolicyError("artifact byte-size limit exceeded")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(item, target)


class LocalProcessSandbox:
    """A disposable process harness; explicitly not a hostile-code boundary."""

    backend_name = BACKEND_NAME
    security_level = SECURITY_LEVEL
    network_policy = NETWORK_POLICY

    def run(
        self,
        artifact_destination: Path,
        *,
        run_id: str,
        timeout: int = 5,
        max_artifact_files: int = MAX_ARTIFACT_FILES,
        max_artifact_bytes: int = MAX_ARTIFACT_BYTES,
    ) -> SandboxResult:
        worker = Path(__file__).with_name("worker.py").resolve()
        environment = {
            "APR_RUN_ID": run_id,
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "PYTHONIOENCODING": "utf-8",
        }
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="apr-sandbox-") as temporary:
            workspace = Path(temporary)
            try:
                completed = subprocess.run(
                    [sys.executable, str(worker)],
                    cwd=workspace,
                    env=environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    timeout=timeout,
                    check=False,
                    start_new_session=True,
                    preexec_fn=_linux_resource_limiter(),
                )
                return_code = completed.returncode
                stdout = completed.stdout
                stderr = completed.stderr
            except subprocess.TimeoutExpired as error:
                return_code = 124
                stdout = error.stdout or ""
                stderr = (error.stderr or "") + "\nworker exceeded the time limit"
                if isinstance(stdout, bytes):
                    stdout = stdout.decode("utf-8", errors="replace")
                if isinstance(stderr, bytes):
                    stderr = stderr.decode("utf-8", errors="replace")

            events, protocol_errors = _parse_worker_events(stdout)
            copy_artifacts(
                workspace / "artifact",
                artifact_destination,
                max_files=max_artifact_files,
                max_bytes=max_artifact_bytes,
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        return SandboxResult(
            return_code=return_code,
            duration_ms=duration_ms,
            events=events,
            protocol_errors=protocol_errors,
            stderr=stderr[-16_384:],
        )
