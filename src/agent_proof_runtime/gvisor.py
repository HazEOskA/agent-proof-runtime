"""Fail-closed Docker + gVisor (runsc) sandbox backend."""

from __future__ import annotations

import json
import shutil
import stat
import subprocess
import tempfile
import threading
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from .canonical import hash_json, sha256_digest
from .mission import MissionSpec
from .sandbox import SandboxPolicyError, SandboxResult, copy_artifacts

BACKEND_NAME = "docker-gvisor"
SECURITY_LEVEL = "sandboxed"
NETWORK_POLICY = "blocked"
RUNTIME_NAME = "runsc"
MAX_SOURCE_FILES = 10_000
MAX_SOURCE_BYTES = 100 * 1024 * 1024


class BackendUnavailableError(RuntimeError):
    pass


class SandboxExecutionError(RuntimeError):
    pass


class SandboxTimeoutError(SandboxExecutionError):
    pass


@dataclass(frozen=True)
class DoctorResult:
    backend: str
    available: bool
    checks: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "backend": self.backend,
            "available": self.available,
            "checks": [dict(check) for check in self.checks],
        }


def _copy_source(source: Path, destination: Path) -> None:
    if not source.is_dir():
        raise SandboxExecutionError(f"source directory does not exist: {source}")
    destination.mkdir(parents=True, exist_ok=False)
    file_count = 0
    total_bytes = 0
    for item in source.rglob("*"):
        if item.is_symlink():
            raise SandboxExecutionError("mission source cannot contain symbolic links")
        relative = item.relative_to(source)
        target = destination / relative
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
            continue
        if not item.is_file():
            raise SandboxExecutionError("mission source must contain only regular files")
        file_count += 1
        total_bytes += item.stat().st_size
        if file_count > MAX_SOURCE_FILES:
            raise SandboxExecutionError("mission source file-count limit exceeded")
        if total_bytes > MAX_SOURCE_BYTES:
            raise SandboxExecutionError("mission source byte-size limit exceeded")
        target.parent.mkdir(parents=True, exist_ok=True)
        source_mode = stat.S_IMODE(item.stat().st_mode)
        shutil.copyfile(item, target)
        target.chmod(0o755 if source_mode & 0o111 else 0o644)


def _make_writable_by_sandbox(path: Path) -> None:
    def grant(item: Path) -> None:
        current = stat.S_IMODE(item.stat().st_mode)
        if item.is_dir():
            item.chmod(current | 0o777)
        elif item.is_file():
            item.chmod(current | 0o666)

    grant(path)
    for item in path.rglob("*"):
        grant(item)


def _artifact_policy_error(
    path: Path, *, max_files: int, max_bytes: int
) -> str | None:
    file_count = 0
    total_bytes = 0
    try:
        for item in path.rglob("*"):
            if item.is_symlink():
                return "agent artifacts cannot contain symbolic links"
            if item.is_dir():
                continue
            if not item.is_file():
                return "agent artifacts must be regular files"
            file_count += 1
            if file_count > max_files:
                return "artifact file-count limit exceeded during execution"
            total_bytes += item.stat().st_size
            if total_bytes > max_bytes:
                return "artifact byte-size limit exceeded during execution"
    except OSError as error:
        return f"artifact policy monitor failed: {error}"
    return None


class DockerGVisorSandbox:
    backend_name = BACKEND_NAME
    security_level = SECURITY_LEVEL
    network_policy = NETWORK_POLICY

    def __init__(
        self,
        *,
        docker_executable: str | None = None,
        command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self._docker_executable = docker_executable
        self._command_runner = command_runner

    def _docker(self) -> str | None:
        return self._docker_executable or shutil.which("docker")

    def doctor(self) -> DoctorResult:
        docker = self._docker()
        checks: list[dict[str, Any]] = []
        if not docker:
            checks.append(
                {"name": "docker_executable", "passed": False, "detail": "not found"}
            )
            checks.append(
                {"name": "runsc_runtime", "passed": False, "detail": "not checked"}
            )
            return DoctorResult(BACKEND_NAME, False, tuple(checks))

        checks.append(
            {"name": "docker_executable", "passed": True, "detail": docker}
        )
        try:
            completed = self._command_runner(
                [docker, "info", "--format", "{{json .Runtimes}}"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as error:
            checks.append(
                {"name": "runsc_runtime", "passed": False, "detail": str(error)}
            )
            return DoctorResult(BACKEND_NAME, False, tuple(checks))

        runtimes: Any = None
        if completed.returncode == 0:
            try:
                runtimes = json.loads(completed.stdout)
            except json.JSONDecodeError:
                runtimes = None
        runsc_available = isinstance(runtimes, dict) and RUNTIME_NAME in runtimes
        detail = (
            "registered"
            if runsc_available
            else (completed.stderr.strip() or "runsc is not registered in Docker")
        )
        checks.append(
            {"name": "runsc_runtime", "passed": runsc_available, "detail": detail}
        )
        return DoctorResult(BACKEND_NAME, runsc_available, tuple(checks))

    def build_create_command(
        self,
        spec: MissionSpec,
        *,
        workspace: Path,
        artifact_output: Path,
        container_name: str,
    ) -> list[str]:
        docker = self._docker()
        if not docker:
            raise BackendUnavailableError("docker executable was not found")
        if spec.workload.image is None or not spec.workload.command:
            raise SandboxExecutionError("gVisor workload is incomplete")

        cpus = str(Decimal(spec.limits.cpu_millis) / Decimal(1000))
        return [
            docker,
            "create",
            "--name",
            container_name,
            "--runtime",
            RUNTIME_NAME,
            "--pull",
            "never",
            "--network",
            "none",
            "--read-only",
            "--cap-drop",
            "ALL",
            "--security-opt",
            "no-new-privileges",
            "--pids-limit",
            str(spec.limits.pids),
            "--memory",
            f"{spec.limits.memory_mb}m",
            "--memory-swap",
            f"{spec.limits.memory_mb}m",
            "--cpus",
            cpus,
            "--user",
            "65532:65532",
            "--ipc",
            "none",
            "--cgroupns",
            "private",
            "--ulimit",
            f"fsize={spec.artifacts.max_bytes}:{spec.artifacts.max_bytes}",
            "--ulimit",
            "nofile=128:128",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=64m",
            "--mount",
            f"type=bind,source={workspace},target=/workspace,readonly",
            "--mount",
            f"type=bind,source={artifact_output},target=/output",
            "--workdir",
            "/workspace",
            "--env",
            "HOME=/tmp",
            "--log-driver",
            "local",
            "--log-opt",
            "max-size=1m",
            "--log-opt",
            "max-file=1",
            spec.workload.image,
            *spec.workload.command,
        ]

    def _run_command(
        self, command: list[str], *, timeout: int
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._command_runner(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise SandboxTimeoutError(str(error)) from error
        except (OSError, subprocess.SubprocessError) as error:
            raise SandboxExecutionError(str(error)) from error

    def run(
        self,
        spec: MissionSpec,
        artifact_destination: Path,
        *,
        run_id: str,
    ) -> SandboxResult:
        doctor = self.doctor()
        if not doctor.available:
            failed = [check for check in doctor.checks if not check["passed"]]
            detail = "; ".join(str(check["detail"]) for check in failed)
            raise BackendUnavailableError(f"gVisor backend unavailable: {detail}")
        source = spec.source_dir
        if source is None:
            raise SandboxExecutionError("gVisor mission has no source directory")

        docker = self._docker()
        if docker is None:
            raise BackendUnavailableError("docker executable was not found")
        container_name = "apr-" + run_id.replace("-", "")[:20]
        started = time.monotonic()
        return_code = 125
        stdout = ""
        stderr = ""
        timed_out = False
        container_created = False
        policy_errors: list[str] = []

        with tempfile.TemporaryDirectory(prefix="apr-gvisor-") as temporary:
            root = Path(temporary)
            workspace = root / "workspace"
            artifact_output = root / "output"
            _copy_source(source, workspace)
            artifact_output.mkdir()
            _make_writable_by_sandbox(artifact_output)
            command = self.build_create_command(
                spec,
                workspace=workspace,
                artifact_output=artifact_output,
                container_name=container_name,
            )

            try:
                created = self._run_command(command, timeout=15)
                stderr = created.stderr[-16_384:]
                if created.returncode != 0:
                    raise SandboxExecutionError(
                        f"docker create failed: {stderr.strip() or 'unknown error'}"
                    )
                container_created = True

                started_container = self._run_command(
                    [docker, "start", container_name], timeout=15
                )
                if started_container.returncode != 0:
                    raise SandboxExecutionError(
                        "docker start failed: "
                        + (started_container.stderr.strip() or "unknown error")
                    )

                monitor_stop = threading.Event()

                def monitor_artifacts() -> None:
                    while not monitor_stop.wait(0.05):
                        violation = _artifact_policy_error(
                            artifact_output,
                            max_files=spec.artifacts.max_files,
                            max_bytes=spec.artifacts.max_bytes,
                        )
                        if violation:
                            policy_errors.append(violation)
                            try:
                                self._run_command(
                                    [docker, "kill", container_name], timeout=10
                                )
                            except SandboxExecutionError as error:
                                policy_errors.append(f"container kill failed: {error}")
                            return

                monitor = threading.Thread(
                    target=monitor_artifacts,
                    name=f"apr-artifact-monitor-{container_name}",
                    daemon=True,
                )
                monitor.start()
                try:
                    try:
                        waited = self._run_command(
                            [docker, "wait", container_name],
                            timeout=spec.limits.timeout_seconds,
                        )
                        if waited.returncode != 0:
                            raise SandboxExecutionError(
                                "docker wait failed: "
                                + (waited.stderr.strip() or "unknown error")
                            )
                        try:
                            return_code = int(waited.stdout.strip().splitlines()[-1])
                        except (IndexError, ValueError) as error:
                            raise SandboxExecutionError(
                                "docker wait returned an invalid exit code"
                            ) from error
                    except SandboxTimeoutError:
                        timed_out = True
                        return_code = 124
                        self._run_command([docker, "kill", container_name], timeout=10)
                finally:
                    monitor_stop.set()
                    monitor.join(timeout=12)
                    if monitor.is_alive():
                        policy_errors.append("artifact policy monitor did not stop")

                logs = self._run_command(
                    [docker, "logs", "--tail", "500", container_name], timeout=10
                )
                stdout = logs.stdout[-65_536:]
                stderr = logs.stderr[-65_536:]
                final_policy_error = _artifact_policy_error(
                    artifact_output,
                    max_files=spec.artifacts.max_files,
                    max_bytes=spec.artifacts.max_bytes,
                )
                if final_policy_error and final_policy_error not in policy_errors:
                    policy_errors.append(final_policy_error)
                if not policy_errors:
                    try:
                        copy_artifacts(
                            artifact_output,
                            artifact_destination,
                            max_files=spec.artifacts.max_files,
                            max_bytes=spec.artifacts.max_bytes,
                        )
                    except SandboxPolicyError as error:
                        policy_errors.append(str(error))
            finally:
                if container_created:
                    self._run_command([docker, "rm", "-f", container_name], timeout=10)

        duration_ms = int((time.monotonic() - started) * 1000)
        events = [
            {
                "type": "sandbox.container_completed",
                "input": {
                    "mission_id": spec.mission_id,
                    "image": spec.workload.image,
                    "command_hash": hash_json(list(spec.workload.command)),
                },
                "output": {
                    "exit_code": return_code,
                    "timed_out": timed_out,
                    "stdout_hash": sha256_digest(stdout.encode("utf-8")),
                    "stderr_hash": sha256_digest(stderr.encode("utf-8")),
                },
                "details": {
                    "backend": BACKEND_NAME,
                    "runtime": RUNTIME_NAME,
                    "network_policy": NETWORK_POLICY,
                },
            }
        ]
        return SandboxResult(
            return_code=return_code,
            duration_ms=duration_ms,
            events=events,
            protocol_errors=policy_errors,
            stderr=stderr,
        )
