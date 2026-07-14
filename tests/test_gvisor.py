from __future__ import annotations

import json
import subprocess
import tempfile
import time
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from agent_proof_runtime.gvisor import DockerGVisorSandbox
from agent_proof_runtime.mission import ArtifactPolicy, load_mission
from agent_proof_runtime.runtime import run_mission


def _completed(command: list[str], *, stdout: str, returncode: int = 0):
    return subprocess.CompletedProcess(command, returncode, stdout=stdout, stderr="")


class GVisorDoctorTests(unittest.TestCase):
    def test_missing_docker_fails_closed(self) -> None:
        backend = DockerGVisorSandbox(docker_executable=None)
        with patch("agent_proof_runtime.gvisor.shutil.which", return_value=None):
            result = backend.doctor()
        self.assertFalse(result.available)
        self.assertEqual(result.checks[0]["name"], "docker_executable")

    def test_registered_runsc_is_required(self) -> None:
        def runner(command, **kwargs):
            return _completed(command, stdout=json.dumps({"runc": {}}))

        backend = DockerGVisorSandbox(
            docker_executable="/usr/bin/docker", command_runner=runner
        )
        self.assertFalse(backend.doctor().available)

    def test_registered_runsc_passes_doctor(self) -> None:
        def runner(command, **kwargs):
            return _completed(command, stdout=json.dumps({"runc": {}, "runsc": {}}))

        backend = DockerGVisorSandbox(
            docker_executable="/usr/bin/docker", command_runner=runner
        )
        self.assertTrue(backend.doctor().available)

    def test_run_preflight_does_not_create_output_when_backend_is_missing(self) -> None:
        spec = load_mission("missions/gvisor-python.example.json")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "run"
            with patch("agent_proof_runtime.gvisor.shutil.which", return_value=None):
                with self.assertRaisesRegex(RuntimeError, "backend unavailable"):
                    run_mission(spec, output)
            self.assertFalse(output.exists())


class GVisorCommandTests(unittest.TestCase):
    def test_create_command_contains_locked_security_policy(self) -> None:
        spec = load_mission("missions/gvisor-python.example.json")
        backend = DockerGVisorSandbox(docker_executable="/usr/bin/docker")
        command = backend.build_create_command(
            spec,
            workspace=Path("/tmp/apr/workspace"),
            artifact_output=Path("/tmp/apr/output"),
            container_name="apr-test",
        )

        pairs = list(zip(command, command[1:]))
        self.assertIn(("--runtime", "runsc"), pairs)
        self.assertIn(("--pull", "never"), pairs)
        self.assertIn(("--network", "none"), pairs)
        self.assertIn(("--cap-drop", "ALL"), pairs)
        self.assertIn(("--security-opt", "no-new-privileges"), pairs)
        self.assertIn(("--pids-limit", "64"), pairs)
        self.assertIn(("--memory", "256m"), pairs)
        self.assertIn(("--memory-swap", "256m"), pairs)
        self.assertIn(("--cpus", "1"), pairs)
        self.assertIn(("--user", "65532:65532"), pairs)
        self.assertIn("--read-only", command)
        self.assertIn(("--cgroupns", "private"), pairs)
        self.assertIn(("--ulimit", "fsize=5242880:5242880"), pairs)
        self.assertTrue(
            any("target=/workspace,readonly" in value for value in command)
        )
        self.assertNotIn("--privileged", command)
        self.assertEqual(command[-2:], ["python", "agent.py"])

    def test_simulated_container_lifecycle_collects_artifact_and_cleans_up(self) -> None:
        calls: list[str] = []
        output_mount: Path | None = None

        def runner(command, **kwargs):
            nonlocal output_mount
            operation = command[1]
            calls.append(operation)
            if operation == "info":
                return _completed(command, stdout=json.dumps({"runsc": {}}))
            if operation == "create":
                mounts = [
                    command[index + 1]
                    for index, value in enumerate(command)
                    if value == "--mount"
                ]
                output_spec = next(value for value in mounts if "target=/output" in value)
                source = output_spec.split("source=", 1)[1].split(",target=", 1)[0]
                output_mount = Path(source)
                return _completed(command, stdout="container-id\n")
            if operation == "start":
                return _completed(command, stdout="apr-test\n")
            if operation == "wait":
                assert output_mount is not None
                (output_mount / "result.txt").write_text("done\n", encoding="utf-8")
                return _completed(command, stdout="0\n")
            if operation == "logs":
                return _completed(command, stdout="agent completed\n")
            if operation == "rm":
                return _completed(command, stdout="apr-test\n")
            raise AssertionError(f"unexpected docker operation: {operation}")

        spec = load_mission("missions/gvisor-python.example.json")
        backend = DockerGVisorSandbox(
            docker_executable="/usr/bin/docker", command_runner=runner
        )
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "artifact"
            result = backend.run(
                spec,
                destination,
                run_id="12345678-1234-4234-8234-123456789abc",
            )
            self.assertEqual(result.return_code, 0)
            self.assertEqual((destination / "result.txt").read_text(), "done\n")
        self.assertEqual(calls, ["info", "create", "start", "wait", "logs", "rm"])

    def test_simulated_timeout_kills_and_removes_container(self) -> None:
        calls: list[str] = []

        def runner(command, **kwargs):
            operation = command[1]
            calls.append(operation)
            if operation == "info":
                return _completed(command, stdout=json.dumps({"runsc": {}}))
            if operation == "wait":
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])
            return _completed(command, stdout="ok\n")

        spec = load_mission("missions/gvisor-python.example.json")
        backend = DockerGVisorSandbox(
            docker_executable="/usr/bin/docker", command_runner=runner
        )
        with tempfile.TemporaryDirectory() as temporary:
            result = backend.run(
                spec,
                Path(temporary) / "artifact",
                run_id="12345678-1234-4234-8234-123456789abc",
            )
        self.assertEqual(result.return_code, 124)
        self.assertTrue(result.events[0]["output"]["timed_out"])
        self.assertEqual(
            calls,
            ["info", "create", "start", "wait", "kill", "logs", "rm"],
        )

    def test_artifact_policy_violation_fails_without_copying_output(self) -> None:
        output_mount: Path | None = None
        calls: list[str] = []

        def runner(command, **kwargs):
            nonlocal output_mount
            operation = command[1]
            calls.append(operation)
            if operation == "info":
                return _completed(command, stdout=json.dumps({"runsc": {}}))
            if operation == "create":
                mounts = [
                    command[index + 1]
                    for index, value in enumerate(command)
                    if value == "--mount"
                ]
                output_spec = next(value for value in mounts if "target=/output" in value)
                source = output_spec.split("source=", 1)[1].split(",target=", 1)[0]
                output_mount = Path(source)
            if operation == "wait":
                assert output_mount is not None
                (output_mount / "one.txt").write_text("one", encoding="utf-8")
                (output_mount / "two.txt").write_text("two", encoding="utf-8")
                time.sleep(0.12)
                return _completed(command, stdout="0\n")
            return _completed(command, stdout="ok\n")

        original = load_mission("missions/gvisor-python.example.json")
        spec = replace(
            original,
            artifacts=ArtifactPolicy(required=True, max_files=1, max_bytes=1024),
        )
        backend = DockerGVisorSandbox(
            docker_executable="/usr/bin/docker", command_runner=runner
        )
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "artifact"
            result = backend.run(
                spec,
                destination,
                run_id="12345678-1234-4234-8234-123456789abc",
            )
            self.assertFalse(destination.exists())
        self.assertTrue(result.protocol_errors)
        self.assertIn("file-count", result.protocol_errors[0])
        self.assertIn("kill", calls)


if __name__ == "__main__":
    unittest.main()
