"""Static host for the APR 3D Control Plane front end.

The front end is an ordinary source project under ``frontend/`` built with
Vite. This module only serves the produced bundle and injects the running
service's request token into the served document. It adds no mission,
provider, evidence, or verification behavior: the 3D world reads the same
endpoints an operator can call by hand.
"""

from __future__ import annotations

import json
import os
from pathlib import Path, PurePosixPath

DIST_ENV = "APR_CONTROL_PLANE_DIST"
INDEX_NAME = "index.html"
ASSET_PREFIX = "assets"
MAX_ASSET_BYTES = 8 * 1024 * 1024
ALLOWED_ASSET_SUFFIXES = frozenset(
    {".js", ".css", ".json", ".svg", ".png", ".jpg", ".webp", ".woff2", ".ico"}
)
TOKEN_GLOBAL = "__APR_TOKEN__"
HEAD_MARKER = "</head>"

CONTENT_SECURITY_POLICY = (
    "default-src 'none'; "
    "script-src 'self' 'unsafe-inline'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "base-uri 'none'; "
    "frame-ancestors 'none'"
)


class ControlPlaneUnavailable(RuntimeError):
    """The front-end bundle has not been built."""


class ControlPlaneAssetError(RuntimeError):
    """The requested asset is not part of the built bundle."""


def default_dist() -> Path:
    """Locate the built bundle without importing anything from Node."""

    override = os.environ.get(DIST_ENV)
    if override:
        return Path(override).expanduser()
    repository_root = Path(__file__).resolve().parents[2]
    return repository_root / "frontend" / "dist"


def _resolved_dist(dist: Path | None) -> Path:
    root = (dist or default_dist()).resolve()
    index = root / INDEX_NAME
    if not root.is_dir() or not index.is_file():
        raise ControlPlaneUnavailable(
            "the APR 3D Control Plane bundle is missing; "
            "run `npm install && npm run build` in frontend/"
        )
    return root


def render_control_plane(csrf_token: str, *, dist: Path | None = None) -> bytes:
    """Return the built document with the service request token injected.

    The token is a per-process value the runtime already generates for its own
    dashboard. It is written into the document, never into storage.
    """

    root = _resolved_dist(dist)
    document = (root / INDEX_NAME).read_text(encoding="utf-8")
    if HEAD_MARKER not in document:
        raise ControlPlaneUnavailable("the built document has no head section")
    injection = (
        f"<script>window.{TOKEN_GLOBAL}={json.dumps(csrf_token)};</script>"
    )
    return document.replace(HEAD_MARKER, injection + HEAD_MARKER, 1).encode("utf-8")


def control_plane_asset(request_path: str, *, dist: Path | None = None) -> Path:
    """Resolve one published asset below ``frontend/dist/assets``."""

    root = _resolved_dist(dist)
    parts = PurePosixPath(request_path).parts
    if len(parts) < 4 or parts[:3] != ("/", "control-plane", ASSET_PREFIX):
        raise ControlPlaneAssetError("asset not found")
    relative_parts = parts[3:]
    if any(part in {"", ".", ".."} or "\\" in part for part in relative_parts):
        raise ControlPlaneAssetError("asset path is not canonical")
    assets_root = (root / ASSET_PREFIX).resolve()
    current = assets_root
    for part in relative_parts:
        current = current / part
        if current.is_symlink():
            raise ControlPlaneAssetError("symbolic links are not allowed")
    try:
        target = current.resolve(strict=True)
    except (OSError, ValueError) as error:
        raise ControlPlaneAssetError("asset not found") from error
    if not target.is_relative_to(assets_root) or not target.is_file():
        raise ControlPlaneAssetError("asset is outside the bundle")
    if target.suffix.lower() not in ALLOWED_ASSET_SUFFIXES:
        raise ControlPlaneAssetError("asset type is not served")
    if target.stat().st_size > MAX_ASSET_BYTES:
        raise ControlPlaneAssetError("asset exceeds the served size limit")
    return target
