"""Tests for the APR 3D Control Plane static host."""

from __future__ import annotations

import json
import unittest
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from agent_proof_runtime.control_plane import (
    CONTENT_SECURITY_POLICY,
    ControlPlaneAssetError,
    ControlPlaneUnavailable,
    control_plane_asset,
    default_dist,
    render_control_plane,
)
from agent_proof_runtime.mission_control import MissionControlConfig, build_server

DOCUMENT = (
    '<!doctype html><html lang="pl"><head><title>APR 3D CONTROL PLANE</title>'
    '<script type="module" src="/control-plane/assets/app.js"></script>'
    "</head><body><div id=\"root\"></div></body></html>"
)


def _bundle(root: Path) -> Path:
    dist = root / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(DOCUMENT, encoding="utf-8")
    (dist / "assets" / "app.js").write_text("export const apr = 1;\n", encoding="utf-8")
    (dist / "assets" / "app.css").write_text(":root{color:#fff}\n", encoding="utf-8")
    return dist


class ControlPlaneDocumentTest(unittest.TestCase):
    def test_token_is_injected_into_the_document(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            document = render_control_plane("token-value", dist=dist).decode("utf-8")
            self.assertIn('window.__APR_TOKEN__="token-value";', document)
            self.assertLess(document.index("__APR_TOKEN__"), document.index("</head>"))

    def test_token_is_json_encoded(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            document = render_control_plane('a"b</script>', dist=dist).decode("utf-8")
            self.assertIn(json.dumps('a"b</script>'), document)

    def test_missing_bundle_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaises(ControlPlaneUnavailable):
                render_control_plane("token", dist=Path(directory) / "dist")

    def test_default_dist_points_at_the_frontend_project(self) -> None:
        self.assertEqual(default_dist().name, "dist")
        self.assertEqual(default_dist().parent.name, "frontend")


class ControlPlaneAssetTest(unittest.TestCase):
    def test_asset_is_resolved(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            asset = control_plane_asset("/control-plane/assets/app.js", dist=dist)
            self.assertTrue(asset.is_file())

    def test_traversal_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            (dist / "secret.txt").write_text("nope", encoding="utf-8")
            for candidate in (
                "/control-plane/assets/../secret.txt",
                "/control-plane/assets/../../etc/passwd",
                "/control-plane/index.html",
                "/control-plane/assets/",
            ):
                with self.assertRaises(ControlPlaneAssetError):
                    control_plane_asset(candidate, dist=dist)

    def test_unserved_suffix_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            (dist / "assets" / "notes.txt").write_text("nope", encoding="utf-8")
            with self.assertRaises(ControlPlaneAssetError):
                control_plane_asset("/control-plane/assets/notes.txt", dist=dist)

    def test_symlinked_asset_is_rejected(self) -> None:
        with TemporaryDirectory() as directory:
            dist = _bundle(Path(directory))
            (dist / "outside.js").write_text("secret", encoding="utf-8")
            link = dist / "assets" / "linked.js"
            try:
                link.symlink_to(dist / "outside.js")
            except (OSError, NotImplementedError):  # pragma: no cover - platform guard
                self.skipTest("symbolic links are unavailable")
            with self.assertRaises(ControlPlaneAssetError):
                control_plane_asset("/control-plane/assets/linked.js", dist=dist)


class ControlPlaneRouteTest(unittest.TestCase):
    """The served routes must exist without changing any evidence behavior."""

    def setUp(self) -> None:
        self._directory = TemporaryDirectory()
        root = Path(self._directory.name)
        self.dist = _bundle(root)
        (root / "missions").mkdir()
        (root / "runs").mkdir()
        self.server, self.control = build_server(
            MissionControlConfig(
                missions_dir=root / "missions",
                runs_dir=root / "runs",
                host="127.0.0.1",
                port=0,
            )
        )
        import os
        import threading

        os.environ["APR_CONTROL_PLANE_DIST"] = str(self.dist)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address[:2]
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        import os

        os.environ.pop("APR_CONTROL_PLANE_DIST", None)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._directory.cleanup()

    def test_document_is_served_with_its_own_policy(self) -> None:
        with urlopen(Request(f"{self.base}/control-plane")) as response:
            body = response.read().decode("utf-8")
            self.assertEqual(response.status, HTTPStatus.OK)
            self.assertEqual(
                response.headers["Content-Security-Policy"], CONTENT_SECURITY_POLICY
            )
        self.assertIn(f'window.__APR_TOKEN__="{self.control.csrf_token}"', body)

    def test_asset_is_served(self) -> None:
        with urlopen(Request(f"{self.base}/control-plane/assets/app.css")) as response:
            self.assertEqual(response.status, HTTPStatus.OK)
            self.assertIn("text/css", response.headers["Content-Type"])

    def test_unknown_asset_is_not_found(self) -> None:
        with self.assertRaises(HTTPError) as caught:
            urlopen(Request(f"{self.base}/control-plane/assets/missing.js"))
        self.assertEqual(caught.exception.code, HTTPStatus.NOT_FOUND)

    def test_dashboard_policy_is_unchanged(self) -> None:
        with urlopen(Request(f"{self.base}/")) as response:
            self.assertIn(
                "script-src 'unsafe-inline'", response.headers["Content-Security-Policy"]
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
