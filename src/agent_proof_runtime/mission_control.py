"""Local mission-control service for Agent Proof Runtime.

The service is deliberately a thin operator layer over the existing MissionSpec,
runtime, and independent validator. It does not introduce another execution path.
"""

from __future__ import annotations

import json
import mimetypes
import os
import re
import secrets
import threading
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path, PurePosixPath
from typing import Any, Callable
from urllib.parse import unquote, urlsplit

from . import __version__
from .bundle import BundleFormatError, load_bundle
from .gvisor import BackendUnavailableError, DockerGVisorSandbox
from .mission import MissionSpec, MissionValidationError
from .mission_loader import load_declared_mission
from .mission_v1 import BuildWeekMission
from .mission_control_ui import render_mission_control
from .mission_studio import (
    MissionStudioManager,
    MissionStudioValidationError,
)
from .mission_studio_openai import (
    DEFAULT_OPENAI_MODEL,
    MissionStudioOpenAIError,
    configured_openai_model,
)
from .build_week_runtime import ArtifactPolicyError, run_build_week_mission
from .providers import ProviderError
from .runtime import RunDirectoryExists, run_mission
from .validator import verify_bundle
from .tamper_lab import TAMPER_CASES, run_tamper_case

MAX_REQUEST_BYTES = 16 * 1024
RUN_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class MissionControlError(RuntimeError):
    """An operator-facing request error with an HTTP status."""

    def __init__(self, message: str, status: HTTPStatus = HTTPStatus.BAD_REQUEST):
        self.status = status
        super().__init__(message)


@dataclass(frozen=True)
class MissionControlConfig:
    missions_dir: Path
    runs_dir: Path
    host: str = "127.0.0.1"
    port: int = 8080
    allow_remote: bool = False

    def normalized(self) -> "MissionControlConfig":
        return MissionControlConfig(
            missions_dir=self.missions_dir.resolve(),
            runs_dir=self.runs_dir.resolve(),
            host=self.host,
            port=self.port,
            allow_remote=self.allow_remote,
        )


def _is_loopback_host(host: str) -> bool:
    return host.lower() in {"127.0.0.1", "::1", "localhost"}


def validate_bind(config: MissionControlConfig) -> None:
    if not 0 <= config.port <= 65_535:
        raise MissionControlError("port must be between 0 and 65535")
    if not _is_loopback_host(config.host) and not config.allow_remote:
        raise MissionControlError(
            "refusing a non-loopback bind without --allow-remote",
            HTTPStatus.FORBIDDEN,
        )


def _request_hostname(host_header: str) -> str | None:
    try:
        parsed = urlsplit("//" + host_header)
    except ValueError:
        return None
    if parsed.username is not None or parsed.password is not None:
        return None
    return parsed.hostname


def _relative_file(root: Path, requested: str, *, suffix: str | None = None) -> Path:
    if not isinstance(requested, str) or not requested:
        raise MissionControlError("path must be a non-empty string")
    pure = PurePosixPath(requested)
    if (
        pure.is_absolute()
        or ".." in pure.parts
        or "\\" in requested
        or pure.as_posix() != requested
    ):
        raise MissionControlError("path must be a canonical relative POSIX path")
    if suffix is not None and pure.suffix != suffix:
        raise MissionControlError(f"path must end with {suffix}")
    unresolved = root.joinpath(*pure.parts)
    current = root
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise MissionControlError(
                "symbolic links are not allowed", HTTPStatus.FORBIDDEN
            )
    try:
        target = unresolved.resolve(strict=True)
    except (OSError, ValueError) as error:
        raise MissionControlError("path does not exist", HTTPStatus.NOT_FOUND) from error
    if not target.is_relative_to(root) or not target.is_file():
        raise MissionControlError(
            "path is outside the configured root", HTTPStatus.FORBIDDEN
        )
    return target


def _run_directory(runs_root: Path, run_name: str) -> Path:
    if not isinstance(run_name, str) or not RUN_NAME.fullmatch(run_name):
        raise MissionControlError("invalid run id")
    unresolved = runs_root / run_name
    if unresolved.is_symlink():
        raise MissionControlError(
            "symbolic links are not allowed", HTTPStatus.FORBIDDEN
        )
    try:
        target = unresolved.resolve(strict=True)
    except (OSError, ValueError) as error:
        raise MissionControlError("run does not exist", HTTPStatus.NOT_FOUND) from error
    if not target.is_relative_to(runs_root) or not target.is_dir():
        raise MissionControlError(
            "run is outside the configured root", HTTPStatus.FORBIDDEN
        )
    return target


def _doctor_summary() -> dict[str, Any]:
    result = DockerGVisorSandbox().doctor()
    return result.to_dict()


def discover_missions(missions_root: Path) -> list[dict[str, Any]]:
    root = missions_root.resolve()
    if not root.is_dir():
        return []
    missions: list[dict[str, Any]] = []
    for candidate in sorted(root.rglob("*.json")):
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if (
            not resolved.is_relative_to(root)
            or candidate.is_symlink()
            or not candidate.is_file()
        ):
            continue
        relative = candidate.relative_to(root).as_posix()
        try:
            spec = load_declared_mission(candidate)
        except MissionValidationError as error:
            missions.append(
                {
                    "path": relative,
                    "valid": False,
                    "errors": list(error.errors),
                }
            )
            continue
        if isinstance(spec, BuildWeekMission):
            missions.append(
                {
                    "path": relative,
                    "valid": True,
                    "schema_version": "apr.mission.v1",
                    "mission_id": spec.mission_id,
                    "title": spec.title,
                    "provider": spec.provider,
                    "model": spec.model,
                    "backend": "controlled-artifact-runtime",
                    "workload": "artifact-proposal",
                    "timeout_seconds": spec.limits.provider_timeout_seconds,
                    "memory_mb": None,
                    "network_mode": "fixture-offline" if spec.provider == "fixture" else "provider-api-only",
                    "artifact_required": any(item.required for item in spec.artifact_contract.artifacts),
                    "spec_hash": spec.manifest_hash,
                    "errors": [],
                }
            )
        else:
            missions.append(
                {
                    "path": relative,
                    "valid": True,
                    "schema_version": "apr.mission.v0.2",
                    "mission_id": spec.mission_id,
                    "title": spec.mission_id,
                    "provider": "sandbox",
                    "model": None,
                    "backend": spec.backend,
                    "workload": spec.workload.kind,
                    "timeout_seconds": spec.limits.timeout_seconds,
                    "memory_mb": spec.limits.memory_mb,
                    "network_mode": spec.network_mode,
                    "artifact_required": spec.artifacts.required,
                    "spec_hash": spec.spec_hash,
                    "errors": [],
                }
            )
    return missions


def _read_run(run_dir: Path) -> dict[str, Any]:
    bundle_path = run_dir / "proof-bundle.json"
    if bundle_path.is_symlink():
        return {
            "run_id": run_dir.name,
            "mission_id": "unknown",
            "started_at": None,
            "mission_status": "UNKNOWN",
            "proof_status": "FAILED",
            "anchor_status": "UNKNOWN",
            "event_count": 0,
            "security_level": "unknown",
            "backend": "unknown",
            "report_url": None,
            "errors": ["proof-bundle.json cannot be a symbolic link"],
        }
    try:
        bundle = load_bundle(bundle_path)
        verification = verify_bundle(bundle_path)
    except (BundleFormatError, OSError, ValueError, RecursionError) as error:
        return {
            "run_id": run_dir.name,
            "mission_id": "unknown",
            "started_at": None,
            "mission_status": "UNKNOWN",
            "proof_status": "FAILED",
            "anchor_status": "UNKNOWN",
            "event_count": 0,
            "security_level": "unknown",
            "backend": "unknown",
            "report_url": None,
            "errors": [str(error)],
        }

    mission = bundle.get("mission")
    mission_spec_value = mission.get("spec") if isinstance(mission, dict) else None
    mission_manifest_value = mission.get("manifest") if isinstance(mission, dict) else None
    mission_spec = mission_spec_value if isinstance(mission_spec_value, dict) else {}
    mission_manifest = mission_manifest_value if isinstance(mission_manifest_value, dict) else {}
    run_value = bundle.get("run")
    run = run_value if isinstance(run_value, dict) else {}
    report_path = run_dir / "report.html"
    return {
        "run_id": run_dir.name,
        "mission_id": mission_manifest.get("mission_id", mission_spec.get("mission_id", "legacy-demo")),
        "started_at": run.get("started_at"),
        "duration_ms": run.get("duration_ms"),
        "mission_status": verification.mission_status,
        "proof_status": verification.status,
        "anchor_status": verification.anchor_status,
        "event_count": verification.event_count,
        "security_level": run.get("security_level", "unknown"),
        "backend": run.get("sandbox_backend", "unknown"),
        "provider": (
            bundle.get("provider", {}).get("provider", "sandbox")
            if isinstance(bundle.get("provider"), dict)
            else "sandbox"
        ),
        "report_url": f"/runs/{run_dir.name}/report.html" if report_path.is_file() else None,
        "bundle_url": f"/runs/{run_dir.name}/proof-bundle.json",
        "errors": list(verification.errors),
    }


def discover_runs(runs_root: Path) -> list[dict[str, Any]]:
    root = runs_root.resolve()
    if not root.is_dir():
        return []
    runs: list[dict[str, Any]] = []
    for candidate in root.iterdir():
        if not RUN_NAME.fullmatch(candidate.name):
            continue
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        if (
            not resolved.is_relative_to(root)
            or candidate.is_symlink()
            or not candidate.is_dir()
        ):
            continue
        if not (candidate / "proof-bundle.json").is_file():
            continue
        runs.append(_read_run(candidate))
    runs.sort(key=lambda item: item.get("started_at") or "", reverse=True)
    return runs


class MissionControl:
    """State and commands shared by the HTTP adapter and tests."""

    def __init__(self, config: MissionControlConfig) -> None:
        self.config = config.normalized()
        validate_bind(self.config)
        self.csrf_token = secrets.token_urlsafe(32)
        self._run_lock = threading.Lock()
        self._studio = MissionStudioManager(
            runs_dir=self.config.runs_dir,
            run_lock=self._run_lock,
        )

    def state(self) -> dict[str, Any]:
        try:
            studio_openai_model = configured_openai_model()
        except MissionStudioOpenAIError:
            studio_openai_model = DEFAULT_OPENAI_MODEL
        return {
            "service": {
                "name": "Agent Proof Runtime Mission Control",
                "version": __version__,
                "trust_boundary": "local-operator",
                "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
                "mission_studio_openai_model": studio_openai_model,
            },
            "doctor": _doctor_summary(),
            "missions": discover_missions(self.config.missions_dir),
            "runs": discover_runs(self.config.runs_dir),
        }

    def run(self, mission_path: str) -> dict[str, Any]:
        if not self._run_lock.acquire(blocking=False):
            raise MissionControlError(
                "another mission is already running", HTTPStatus.CONFLICT
            )
        try:
            manifest = _relative_file(
                self.config.missions_dir, mission_path, suffix=".json"
            )
            spec = load_declared_mission(manifest)
            stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
            run_name = f"{stamp}-{spec.mission_id}-{uuid.uuid4().hex[:8]}"
            self.config.runs_dir.mkdir(parents=True, exist_ok=True)
            if isinstance(spec, BuildWeekMission):
                result = run_build_week_mission(spec, self.config.runs_dir / run_name)
            else:
                result = run_mission(spec, self.config.runs_dir / run_name)
            return _read_run(result.output_dir)
        except MissionValidationError as error:
            raise MissionControlError("; ".join(error.errors)) from error
        except RunDirectoryExists as error:
            raise MissionControlError(str(error), HTTPStatus.CONFLICT) from error
        except BackendUnavailableError as error:
            raise MissionControlError(
                str(error), HTTPStatus.SERVICE_UNAVAILABLE
            ) from error
        except (ProviderError, ArtifactPolicyError) as error:
            raise MissionControlError(
                str(error), HTTPStatus.SERVICE_UNAVAILABLE
            ) from error
        finally:
            self._run_lock.release()

    def verify(self, run_name: str) -> dict[str, Any]:
        run_dir = _run_directory(self.config.runs_dir, run_name)
        return _read_run(run_dir)

    def start_studio(self, value: Any) -> dict[str, Any]:
        try:
            return self._studio.start(value)
        except MissionStudioValidationError as error:
            raise MissionControlError(str(error)) from error
        except RuntimeError as error:
            raise MissionControlError(str(error), HTTPStatus.CONFLICT) from error

    def studio(self, session_id: str) -> dict[str, Any]:
        try:
            return self._studio.get(session_id)
        except ValueError as error:
            raise MissionControlError(str(error)) from error
        except KeyError as error:
            raise MissionControlError(
                "Mission Studio session does not exist", HTTPStatus.NOT_FOUND
            ) from error

    def detail(self, run_name: str) -> dict[str, Any]:
        run_dir = _run_directory(self.config.runs_dir, run_name)
        bundle_path = _relative_file(run_dir, "proof-bundle.json", suffix=".json")
        return {"summary": _read_run(run_dir), "evidence": load_bundle(bundle_path)}

    def tamper(self, run_name: str, case: str) -> dict[str, Any]:
        if case not in TAMPER_CASES:
            raise MissionControlError("tamper case must be artifact, event, or metadata")
        run_dir = _run_directory(self.config.runs_dir, run_name)
        try:
            return run_tamper_case(run_dir, case)
        except (OSError, ValueError, RuntimeError) as error:
            raise MissionControlError(str(error)) from error

    def public_file(self, request_path: str) -> Path:
        parts = PurePosixPath(unquote(request_path)).parts
        if len(parts) < 3 or parts[0] != "/" or parts[1] != "runs":
            raise MissionControlError("file not found", HTTPStatus.NOT_FOUND)
        run_dir = _run_directory(self.config.runs_dir, parts[2])
        relative_parts = parts[3:]
        if not relative_parts:
            raise MissionControlError("file not found", HTTPStatus.NOT_FOUND)
        relative = PurePosixPath(*relative_parts).as_posix()
        allowed = relative in {"report.html", "proof-bundle.json"} or relative.startswith(
            "artifact/"
        )
        if not allowed:
            raise MissionControlError("file not found", HTTPStatus.NOT_FOUND)
        return _relative_file(run_dir, relative)


def _handler_factory(control: MissionControl) -> type[BaseHTTPRequestHandler]:
    class MissionControlHandler(BaseHTTPRequestHandler):
        server_version = "APR-Mission-Control"
        sys_version = ""

        def _headers(
            self,
            status: HTTPStatus,
            content_type: str,
            length: int,
            *,
            dashboard: bool = False,
        ) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(length))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("X-Frame-Options", "DENY")
            if dashboard:
                content_policy = (
                    "default-src 'none'; style-src 'unsafe-inline'; "
                    "script-src 'unsafe-inline'; connect-src 'self'; "
                    "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'"
                )
            else:
                content_policy = (
                    "default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'none'; "
                    "img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; "
                    "sandbox allow-same-origin"
                )
            self.send_header("Content-Security-Policy", content_policy)
            self.end_headers()

        def _send_bytes(
            self,
            payload: bytes,
            content_type: str,
            status: HTTPStatus = HTTPStatus.OK,
            *,
            dashboard: bool = False,
        ) -> None:
            self._headers(status, content_type, len(payload), dashboard=dashboard)
            self.wfile.write(payload)

        def _send_json(self, value: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
            self._send_bytes(payload, "application/json; charset=utf-8", status)

        def _error(self, error: Exception) -> None:
            if isinstance(error, MissionControlError):
                status = error.status
                message = str(error)
            else:
                status = HTTPStatus.INTERNAL_SERVER_ERROR
                message = "internal mission-control error"
            self._send_json({"ok": False, "error": message}, status)

        def _read_json(self) -> dict[str, Any]:
            media_type = self.headers.get("Content-Type", "").split(";", 1)[0].lower()
            if media_type != "application/json":
                raise MissionControlError(
                    "Content-Type must be application/json",
                    HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                )
            raw_length = self.headers.get("Content-Length")
            try:
                length = int(raw_length or "0")
            except ValueError as error:
                raise MissionControlError("invalid Content-Length") from error
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise MissionControlError("request body has an invalid size")
            try:
                value = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeError, json.JSONDecodeError) as error:
                raise MissionControlError("request body must be valid JSON") from error
            if not isinstance(value, dict):
                raise MissionControlError("request body must be a JSON object")
            return value

        def _require_token(self) -> None:
            supplied = self.headers.get("X-APR-Token", "")
            if not secrets.compare_digest(supplied, control.csrf_token):
                raise MissionControlError(
                    "request token is missing or invalid", HTTPStatus.FORBIDDEN
                )

        def _require_allowed_host(self) -> None:
            if control.config.allow_remote:
                return
            hostname = _request_hostname(self.headers.get("Host", ""))
            if hostname is None or not _is_loopback_host(hostname):
                raise MissionControlError(
                    "request Host is not allowed", HTTPStatus.FORBIDDEN
                )

        def do_GET(self) -> None:  # noqa: N802 - stdlib HTTP hook
            path = urlsplit(self.path).path
            try:
                self._require_allowed_host()
                if path == "/health":
                    self._send_json(
                        {
                            "ok": True,
                            "status": "healthy",
                            "service": "apr-mission-control",
                            "version": __version__,
                        }
                    )
                elif path == "/":
                    document = render_mission_control(control.csrf_token).encode("utf-8")
                    self._send_bytes(
                        document, "text/html; charset=utf-8", dashboard=True
                    )
                elif path == "/api/state":
                    self._send_json({"ok": True, **control.state()})
                elif path.startswith("/api/studio/"):
                    parts = PurePosixPath(path).parts
                    if len(parts) != 4 or parts[:3] != ("/", "api", "studio"):
                        raise MissionControlError("route not found", HTTPStatus.NOT_FOUND)
                    self._send_json(
                        {"ok": True, "session": control.studio(parts[3])}
                    )
                elif path.startswith("/api/runs/"):
                    parts = PurePosixPath(path).parts
                    if len(parts) != 4 or parts[:3] != ("/", "api", "runs"):
                        raise MissionControlError("route not found", HTTPStatus.NOT_FOUND)
                    self._send_json({"ok": True, **control.detail(parts[3])})
                elif path.startswith("/runs/"):
                    file_path = control.public_file(path)
                    content_type = (
                        mimetypes.guess_type(file_path.name)[0]
                        or "application/octet-stream"
                    )
                    if content_type.startswith("text/") or content_type == "application/json":
                        content_type += "; charset=utf-8"
                    self._send_bytes(file_path.read_bytes(), content_type)
                else:
                    raise MissionControlError("route not found", HTTPStatus.NOT_FOUND)
            except Exception as error:  # request boundary
                self._error(error)

        def do_POST(self) -> None:  # noqa: N802 - stdlib HTTP hook
            path = urlsplit(self.path).path
            try:
                self._require_allowed_host()
                self._require_token()
                value = self._read_json()
                if path == "/api/runs":
                    if set(value) != {"mission_path"}:
                        raise MissionControlError("expected only mission_path")
                    run = control.run(value["mission_path"])
                    self._send_json({"ok": True, "run": run}, HTTPStatus.CREATED)
                elif path == "/api/studio/start":
                    session = control.start_studio(value)
                    self._send_json(
                        {"ok": True, "session": session}, HTTPStatus.CREATED
                    )
                elif path == "/api/verify":
                    if set(value) != {"run_id"}:
                        raise MissionControlError("expected only run_id")
                    run = control.verify(value["run_id"])
                    self._send_json({"ok": True, "run": run})
                elif path == "/api/tamper":
                    if set(value) != {"run_id", "case"}:
                        raise MissionControlError("expected only run_id and case")
                    result = control.tamper(value["run_id"], value["case"])
                    self._send_json({"ok": True, "result": result})
                else:
                    raise MissionControlError("route not found", HTTPStatus.NOT_FOUND)
            except Exception as error:  # request boundary
                self._error(error)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return MissionControlHandler


def build_server(
    config: MissionControlConfig,
) -> tuple[HTTPServer, MissionControl]:
    control = MissionControl(config)
    server = HTTPServer(
        (control.config.host, control.config.port), _handler_factory(control)
    )
    return server, control


def serve(
    config: MissionControlConfig,
    *,
    announce: Callable[[str], None] = print,
) -> None:
    server, _ = build_server(config)
    host, port = server.server_address[:2]
    announce(f"Mission Control: http://{host}:{port}")
    announce("Press Ctrl+C to stop. Runs remain in the configured runs directory.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
