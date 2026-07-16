"""Static operator report renderer."""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from .validator import VerificationResult


def _short_hash(value: Any) -> str:
    text = str(value)
    if len(text) <= 25:
        return text
    return text[:17] + "…" + text[-8:]


def write_report(
    path: Path, bundle: dict[str, Any], verification: VerificationResult
) -> None:
    run = bundle["run"]
    integrity = bundle["integrity"]
    schema_version = bundle.get("schema_version", "unknown")
    mission_value = bundle.get("mission")
    if isinstance(mission_value, dict):
        mission_document = mission_value.get("manifest", mission_value.get("spec", {}))
        mission_id = (
            mission_document.get("mission_id", "legacy-demo")
            if isinstance(mission_document, dict)
            else "legacy-demo"
        )
    else:
        mission_id = "legacy-demo"
    provider_value = bundle.get("provider")
    provider = provider_value if isinstance(provider_value, dict) else {}
    acceptance_value = bundle.get("acceptance", bundle.get("validation", {}))
    acceptance = acceptance_value if isinstance(acceptance_value, dict) else {}
    proof_ok = verification.status == "LOCAL_VERIFIED"
    proof_class = "ok" if proof_ok else "bad"
    mission_class = "ok" if verification.mission_status == "PASSED" else "bad"

    event_rows = "".join(
        "<tr>"
        f"<td>{event['index']}</td>"
        f"<td>{escape(event['type'])}</td>"
        f"<td><code>{escape(_short_hash(event['step_hash']))}</code></td>"
        "</tr>"
        for event in bundle["events"]
    )
    artifact_rows = "".join(
        "<tr>"
        f"<td><a href=\"{escape(artifact['path'], quote=True)}\">{escape(artifact['path'])}</a></td>"
        f"<td>{artifact['size']} B</td>"
        f"<td><code>{escape(_short_hash(artifact['sha256']))}</code></td>"
        "</tr>"
        for artifact in bundle["artifacts"]
    ) or '<tr><td colspan="3">No artifacts</td></tr>'
    check_rows = "".join(
        "<tr>"
        f"<td>{escape(str(check.get('id', check.get('name', 'unknown'))))}</td>"
        f"<td>{escape(str(check.get('type', 'legacy')))}</td>"
        f"<td class=\"{'ok' if check.get('passed') is True else 'bad'}\">"
        f"{'PASS' if check.get('passed') is True else 'FAIL'}</td>"
        "</tr>"
        for check in acceptance.get("checks", [])
        if isinstance(check, dict)
    ) or '<tr><td colspan="3">No checks</td></tr>'
    error_items = "".join(
        f"<li>{escape(error)}</li>" for error in verification.errors
    ) or "<li>None</li>"
    if run["security_level"] == "sandboxed":
        boundary_notice = (
            "<strong>Sandboxed execution.</strong> gVisor and blocked networking form the "
            "execution boundary, but this receipt is still unsigned and externally unanchored."
        )
    else:
        boundary_notice = (
            "<strong>Development boundary.</strong> This run is internally verifiable but not "
            "externally anchored or signed. The local-process backend is not safe for hostile code."
        )

    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Agent Proof Runtime — {escape(str(mission_id))}</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #090d12; color: #e8edf2; }}
    main {{ width: min(1080px, calc(100% - 32px)); margin: 0 auto; padding: 48px 0 72px; }}
    .eyebrow {{ color: #8ba0b3; letter-spacing: .14em; text-transform: uppercase; font-size: 12px; }}
    h1 {{ font-size: clamp(32px, 6vw, 64px); margin: 10px 0 28px; letter-spacing: -.04em; }}
    h2 {{ margin-top: 38px; font-size: 20px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; }}
    .card {{ background: #111821; border: 1px solid #24303c; border-radius: 14px; padding: 18px; }}
    .label {{ color: #8ba0b3; font-size: 12px; text-transform: uppercase; letter-spacing: .08em; }}
    .value {{ font-size: 18px; margin-top: 9px; overflow-wrap: anywhere; }}
    .ok {{ color: #68e0a0; }} .bad {{ color: #ff7b72; }}
    .warning {{ margin: 24px 0; border-left: 3px solid #f0b35b; background: #201a11; padding: 16px 18px; color: #f6d49f; }}
    table {{ width: 100%; border-collapse: collapse; background: #111821; border-radius: 14px; overflow: hidden; }}
    th, td {{ padding: 13px 15px; text-align: left; border-bottom: 1px solid #24303c; }}
    th {{ color: #8ba0b3; font-size: 12px; text-transform: uppercase; }}
    code {{ color: #b7c7d6; font-size: 12px; }}
    a {{ color: #75bfff; }}
    ul {{ color: #c5d0da; }}
  </style>
</head>
<body>
<main>
  <div class="eyebrow">Agent Proof Runtime · {escape(str(schema_version))}</div>
  <h1>Execution receipt</h1>
  <section class="grid">
    <div class="card"><div class="label">Proof</div><div class="value {proof_class}">{escape(verification.status)}</div></div>
    <div class="card"><div class="label">Mission</div><div class="value {mission_class}">{escape(verification.mission_status)}</div></div>
    <div class="card"><div class="label">Anchor</div><div class="value">{escape(verification.anchor_status)}</div></div>
    <div class="card"><div class="label">Security</div><div class="value">{escape(run['security_level'])}</div></div>
  </section>
  <div class="warning">{boundary_notice}</div>
  <section class="grid">
    <div class="card"><div class="label">Mission</div><div class="value"><code>{escape(str(mission_id))}</code></div></div>
    <div class="card"><div class="label">Run ID</div><div class="value"><code>{escape(run['run_id'])}</code></div></div>
    <div class="card"><div class="label">Backend</div><div class="value">{escape(run['sandbox_backend'])}</div></div>
    <div class="card"><div class="label">Events</div><div class="value">{len(bundle['events'])}</div></div>
    <div class="card"><div class="label">Provider</div><div class="value">{escape(str(provider.get('provider', 'sandbox')))}</div></div>
    <div class="card"><div class="label">Model</div><div class="value"><code>{escape(str(provider.get('resolved_model', 'n/a')))}</code></div></div>
    <div class="card"><div class="label">Merkle root</div><div class="value"><code>{escape(_short_hash(integrity['event_merkle_root']))}</code></div></div>
    <div class="card"><div class="label">Bundle hash</div><div class="value"><code>{escape(_short_hash(integrity['bundle_hash']))}</code></div></div>
  </section>
  <h2>Artifacts</h2>
  <table><thead><tr><th>Path</th><th>Size</th><th>SHA-256</th></tr></thead><tbody>{artifact_rows}</tbody></table>
  <h2>Acceptance checks</h2>
  <table><thead><tr><th>Check</th><th>Type</th><th>Result</th></tr></thead><tbody>{check_rows}</tbody></table>
  <h2>Execution chain</h2>
  <table><thead><tr><th>#</th><th>Event</th><th>Step hash</th></tr></thead><tbody>{event_rows}</tbody></table>
  <h2>Validator errors</h2>
  <ul>{error_items}</ul>
  <p><a href="proof-bundle.json">Open raw Proof Bundle</a></p>
</main>
</body>
</html>
"""
    path.write_text(document, encoding="utf-8")
