"""Dependency-free Mission Control dashboard."""

from __future__ import annotations

import json


def render_mission_control(csrf_token: str) -> str:
    token = json.dumps(csrf_token)
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>APR Mission Control</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg: #090b0d;
      --panel: #111519;
      --panel-2: #161b20;
      --line: #273039;
      --muted: #8f9ba6;
      --text: #f3f6f8;
      --green: #70e1a1;
      --amber: #f2bd64;
      --red: #ff7b72;
      --blue: #8ac7ff;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; min-width: 300px; background: var(--bg); color: var(--text); }}
    body::before {{
      content: ""; position: fixed; inset: 0; pointer-events: none; opacity: .24;
      background-image: linear-gradient(#151a1f 1px, transparent 1px), linear-gradient(90deg, #151a1f 1px, transparent 1px);
      background-size: 40px 40px; mask-image: linear-gradient(to bottom, black, transparent 68%);
    }}
    button, a {{ -webkit-tap-highlight-color: transparent; }}
    button:focus-visible, a:focus-visible {{ outline: 2px solid var(--blue); outline-offset: 3px; }}
    .shell {{ position: relative; width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 72px; }}
    header {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-bottom: 22px; border-bottom: 1px solid var(--line); }}
    .brand {{ display: flex; align-items: center; gap: 12px; font-weight: 720; letter-spacing: -.02em; }}
    .mark {{ width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #3b4854; border-radius: 9px; background: #151a1f; color: var(--green); font: 800 15px/1 ui-monospace, monospace; }}
    .system {{ display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 0 4px #f2bd6418; }}
    .hero {{ padding: clamp(52px, 10vw, 110px) 0 48px; max-width: 860px; }}
    .eyebrow {{ color: var(--green); text-transform: uppercase; letter-spacing: .16em; font-size: 11px; font-weight: 760; }}
    h1 {{ margin: 14px 0 18px; font-size: clamp(42px, 8vw, 86px); line-height: .96; letter-spacing: -.065em; max-width: 850px; }}
    .lead {{ margin: 0; max-width: 650px; color: #b4bec7; font-size: clamp(16px, 2.2vw, 20px); line-height: 1.55; }}
    .truth {{ margin-top: 28px; display: inline-flex; align-items: center; gap: 10px; padding: 10px 13px; border: 1px solid #4b3b21; background: #1d1810; color: #e8c98f; border-radius: 9px; font-size: 13px; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--line); border-radius: 14px; background: #0e1215; overflow: hidden; }}
    .stat {{ padding: 20px; min-height: 100px; border-right: 1px solid var(--line); }} .stat:last-child {{ border: 0; }}
    .label {{ color: var(--muted); font-size: 11px; font-weight: 720; letter-spacing: .1em; text-transform: uppercase; }}
    .value {{ margin-top: 13px; font-size: clamp(18px, 3vw, 28px); letter-spacing: -.03em; overflow-wrap: anywhere; }}
    .section-head {{ margin: 54px 0 18px; display: flex; align-items: end; justify-content: space-between; gap: 20px; }}
    h2 {{ margin: 0; font-size: 24px; letter-spacing: -.035em; }}
    .section-note {{ color: var(--muted); font-size: 13px; }}
    .missions {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 21px; }}
    .card-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }}
    .card h3 {{ margin: 5px 0 7px; font-size: 20px; letter-spacing: -.025em; }}
    .path {{ color: var(--muted); font: 12px/1.4 ui-monospace, SFMono-Regular, Consolas, monospace; overflow-wrap: anywhere; }}
    .badge {{ display: inline-flex; align-items: center; min-height: 25px; padding: 4px 8px; border-radius: 999px; border: 1px solid var(--line); color: #c7d0d8; font-size: 11px; white-space: nowrap; }}
    .badge.ok {{ border-color: #24583c; background: #10241a; color: var(--green); }}
    .badge.warn {{ border-color: #594222; background: #211910; color: var(--amber); }}
    .badge.bad {{ border-color: #64302c; background: #261312; color: var(--red); }}
    .meta {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; margin: 20px 0; }}
    .meta div {{ padding: 10px; border-radius: 9px; background: var(--panel-2); }}
    .meta span {{ display: block; }} .meta .k {{ color: var(--muted); font-size: 10px; text-transform: uppercase; letter-spacing: .08em; }} .meta .v {{ margin-top: 5px; font-size: 13px; }}
    .actions {{ display: flex; align-items: center; gap: 10px; }}
    button {{ min-height: 42px; border: 0; border-radius: 9px; padding: 0 15px; background: var(--text); color: #090b0d; font: 700 13px/1 inherit; cursor: pointer; }}
    button:hover {{ background: #dbe2e7; }} button:disabled {{ cursor: not-allowed; opacity: .38; }}
    .hash {{ margin-left: auto; color: #65727d; font: 10px/1.3 ui-monospace, monospace; }}
    .runs {{ border: 1px solid var(--line); border-radius: 14px; overflow: hidden; background: var(--panel); }}
    .run {{ display: grid; grid-template-columns: 1.4fr .8fr .8fr .7fr auto; align-items: center; gap: 14px; min-height: 74px; padding: 15px 18px; border-bottom: 1px solid var(--line); }} .run:last-child {{ border: 0; }}
    .run-title {{ font-weight: 700; }} .run-sub {{ margin-top: 4px; color: var(--muted); font-size: 12px; }}
    .run a {{ color: var(--blue); font-size: 13px; font-weight: 700; text-decoration: none; }} .run a:hover {{ text-decoration: underline; }}
    .verify {{ background: transparent; color: #cbd4db; border: 1px solid #3a4650; min-height: 34px; padding: 0 10px; }}
    .empty {{ padding: 34px; color: var(--muted); text-align: center; }}
    .evidence {{ margin-top: 14px; display: none; }} .evidence.show {{ display: block; }}
    .evidence-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 14px 0; }}
    .evidence-list {{ margin: 12px 0 0; padding: 0; list-style: none; }}
    .evidence-list li {{ display: grid; grid-template-columns: 1.3fr .7fr; gap: 12px; padding: 10px 0; border-bottom: 1px solid var(--line); overflow-wrap: anywhere; }}
    .tamper-actions {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 15px; }}
    .tamper {{ background: transparent; color: var(--red); border: 1px solid #64302c; }}
    .toast {{ position: fixed; right: 20px; bottom: 20px; width: min(390px, calc(100% - 40px)); padding: 14px 16px; border-radius: 10px; background: #e9eff3; color: #111519; box-shadow: 0 18px 70px #0009; font-size: 13px; transform: translateY(130%); transition: transform .22s ease; }}
    .toast.show {{ transform: translateY(0); }} .toast.error {{ background: #ffd8d5; color: #3a1110; }}
    .skeleton {{ min-height: 180px; display: grid; place-items: center; color: var(--muted); }}
    footer {{ margin-top: 55px; padding-top: 20px; border-top: 1px solid var(--line); color: #697681; font-size: 12px; line-height: 1.6; }}
    @media (max-width: 780px) {{
      .stats {{ grid-template-columns: repeat(2, 1fr); }} .stat:nth-child(2) {{ border-right: 0; }} .stat:nth-child(-n+2) {{ border-bottom: 1px solid var(--line); }}
      .missions {{ grid-template-columns: 1fr; }}
      .evidence-grid {{ grid-template-columns: 1fr; }}
      .run {{ grid-template-columns: 1fr auto; }} .run > :not(:first-child):not(:last-child) {{ display: none; }}
      .system span:last-child {{ display: none; }}
    }}
    @media (prefers-reduced-motion: reduce) {{ .toast {{ transition: none; }} }}
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand"><div class="mark">APR</div><span>Mission Control</span></div>
      <div class="system"><span class="dot" id="system-dot"></span><span id="system-status">checking runtime</span></div>
    </header>
    <main>
      <section class="hero">
        <div class="eyebrow">Agent sandbox · verifiable execution</div>
        <h1>Autonomous work that proves itself.</h1>
        <p class="lead">Run approved missions, inspect deterministic acceptance evidence, and let an independent verifier detect changes to artifacts, events, or critical metadata.</p>
        <div class="truth">● Development-only trust boundary. Evidence is locally verifiable and deliberately UNANCHORED.</div>
      </section>
      <section class="stats" aria-label="System status">
        <div class="stat"><div class="label">Missions</div><div class="value" id="mission-count">—</div></div>
        <div class="stat"><div class="label">Runs</div><div class="value" id="run-count">—</div></div>
        <div class="stat"><div class="label">gVisor</div><div class="value" id="gvisor-status">—</div></div>
        <div class="stat"><div class="label">Latest proof</div><div class="value" id="proof-status">—</div></div>
      </section>

      <div class="section-head"><div><div class="eyebrow">01 / Start</div><h2>Approved missions</h2></div><div class="section-note">Checked-in manifests only</div></div>
      <section class="missions" id="missions"><div class="card skeleton">Loading manifests…</div></section>

      <div class="section-head"><div><div class="eyebrow">02 / Proof</div><h2>Execution history</h2></div><div class="section-note">Newest first</div></div>
      <section class="runs" id="runs"><div class="skeleton">Loading evidence…</div></section>
      <section class="card evidence" id="evidence"></section>
    </main>
    <footer>The UI is a view of evidence, never the source of truth. Mission Control accepts no arbitrary commands or filesystem paths. <strong>UNANCHORED</strong> means a host administrator could still replace and recompute local evidence; external trust is roadmap work.</footer>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>
  <script>
    const token = {token};
    const $ = (selector) => document.querySelector(selector);
    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    let busy = false;

    function toast(message, error = false) {{
      const node = $('#toast'); node.textContent = message; node.className = 'toast show' + (error ? ' error' : '');
      window.setTimeout(() => node.className = 'toast', 3500);
    }}

    async function api(path, options = {{}}) {{
      const response = await fetch(path, options);
      const body = await response.json();
      if (!response.ok || !body.ok) throw new Error(body.error || `HTTP ${{response.status}}`);
      return body;
    }}

    function missionCard(mission, gvisorReady, openaiConfigured) {{
      if (!mission.valid) return `<article class="card"><div class="card-top"><div><div class="path">${{esc(mission.path)}}</div><h3>Invalid manifest</h3></div><span class="badge bad">INVALID</span></div><p class="path">${{esc(mission.errors.join(' · '))}}</p></article>`;
      const needsKey = mission.provider === 'openai' && !openaiConfigured;
      const blocked = (mission.backend === 'gvisor' && !gvisorReady) || needsKey;
      const security = mission.backend === 'gvisor' ? 'sandboxed' : (mission.provider === 'fixture' ? 'fixture · offline' : 'development only');
      const blockedLabel = needsKey ? 'OPENAI_API_KEY absent' : 'runsc unavailable';
      return `<article class="card"><div class="card-top"><div><div class="path">${{esc(mission.path)}}</div><h3>${{esc(mission.title || mission.mission_id)}}</h3><div class="path">${{esc(mission.mission_id)}} · ${{esc(mission.model || 'no model')}}</div></div><span class="badge ${{blocked ? 'warn' : 'ok'}}">${{esc(security)}}</span></div><div class="meta"><div><span class="k">Provider</span><span class="v">${{esc(mission.provider)}}</span></div><div><span class="k">Network</span><span class="v">${{esc(mission.network_mode)}}</span></div><div><span class="k">Limit</span><span class="v">${{esc(mission.timeout_seconds)}} s</span></div></div><div class="actions"><button data-run="${{esc(mission.path)}}" ${{blocked || busy ? 'disabled' : ''}}>${{blocked ? blockedLabel : 'Run mission'}}</button><span class="hash">${{esc(mission.spec_hash.slice(0, 18))}}…</span></div></article>`;
    }}

    function runRow(run) {{
      const proofClass = run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad';
      const report = run.report_url ? `<a href="${{esc(run.report_url)}}" target="_blank" rel="noopener">Report ↗</a>` : '<span class="path">no report</span>';
      return `<article class="run"><div><div class="run-title">${{esc(run.mission_id)}}</div><div class="run-sub">${{esc(run.started_at || run.run_id)}} · ${{esc(run.provider)}} · ${{esc(run.backend)}}</div></div><span class="badge ${{proofClass}}">${{esc(run.proof_status)}}</span><span class="badge ${{run.mission_status === 'PASSED' ? 'ok' : 'bad'}}">${{esc(run.mission_status)}}</span><span class="badge warn">${{esc(run.anchor_status)}}</span><div class="actions">${{report}}<button class="verify" data-detail="${{esc(run.run_id)}}">Evidence</button><button class="verify" data-verify="${{esc(run.run_id)}}">Reverify</button></div></article>`;
    }}

    function evidenceView(detail) {{
      const e = detail.evidence, run = detail.summary, integrity = e.integrity || {{}};
      const provider = e.provider || {{provider:'sandbox', resolved_model:'n/a', implementation_status:'legacy sandbox'}};
      const acceptance = e.acceptance || e.validation || {{checks:[]}};
      const artifacts = (e.artifacts || []).map(a => `<li><span>${{esc(a.path)}} · ${{esc(a.size)}} B</span><code>${{esc(a.sha256)}}</code></li>`).join('') || '<li>No artifacts</li>';
      const checks = (acceptance.checks || []).map(c => `<li><span>${{esc(c.id || c.name)}} · ${{esc(c.type || 'legacy')}}</span><span class="${{c.passed ? 'ok' : 'bad'}}">${{c.passed ? 'PASS' : 'FAIL'}}</span></li>`).join('') || '<li>No checks</li>';
      const events = (e.events || []).map(item => `<li><span>${{esc(item.index)}} · ${{esc(item.type)}}</span><code>${{esc(item.step_hash)}}</code></li>`).join('');
      return `<div class="card-top"><div><div class="eyebrow">03 / Evidence</div><h2>${{esc(run.mission_id)}}</h2></div><span class="badge ${{run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad'}}">${{esc(run.proof_status)}}</span></div><div class="truth">Provider ${{esc(provider.provider)}} · ${{esc(provider.resolved_model)}} · ${{esc(provider.implementation_status)}}</div><div class="evidence-grid"><div class="meta"><div><span class="k">Anchor</span><span class="v">${{esc(integrity.anchor_status)}}</span></div></div><div class="meta"><div><span class="k">Merkle root</span><span class="v hash">${{esc(integrity.event_merkle_root)}}</span></div></div><div class="meta"><div><span class="k">Bundle hash</span><span class="v hash">${{esc(integrity.bundle_hash)}}</span></div></div></div><h3>Artifacts and hashes</h3><ul class="evidence-list">${{artifacts}}</ul><h3>Acceptance checks</h3><ul class="evidence-list">${{checks}}</ul><h3>Event replay</h3><ul class="evidence-list">${{events}}</ul><h3>Tamper Lab · disposable copies</h3><div class="tamper-actions"><button class="tamper" data-tamper="artifact" data-run-id="${{esc(run.run_id)}}">Tamper artifact</button><button class="tamper" data-tamper="event" data-run-id="${{esc(run.run_id)}}">Tamper event</button><button class="tamper" data-tamper="metadata" data-run-id="${{esc(run.run_id)}}">Tamper metadata</button><a href="${{esc(run.bundle_url)}}" target="_blank" rel="noopener">Proof Bundle ↗</a></div>`;
    }}

    async function refresh() {{
      try {{
        const data = await api('/api/state');
        const ready = Boolean(data.doctor.available);
        $('#mission-count').textContent = data.missions.filter(m => m.valid).length;
        $('#run-count').textContent = data.runs.length;
        $('#gvisor-status').textContent = ready ? 'READY' : 'OFFLINE';
        $('#gvisor-status').style.color = ready ? 'var(--green)' : 'var(--amber)';
        $('#proof-status').textContent = data.runs[0]?.proof_status || 'NO RUNS YET';
        $('#proof-status').style.color = data.runs[0]?.proof_status === 'LOCAL_VERIFIED' ? 'var(--green)' : 'inherit';
        $('#system-status').textContent = ready ? 'gVisor ready' : 'fixture mode · runsc unavailable';
        $('#system-dot').style.background = ready ? 'var(--green)' : 'var(--amber)';
        $('#missions').innerHTML = data.missions.length ? data.missions.map(m => missionCard(m, ready, data.service.openai_configured)).join('') : '<div class="card empty">No manifests in the configured directory.</div>';
        $('#runs').innerHTML = data.runs.length ? data.runs.map(runRow).join('') : '<div class="empty">No runs yet. Start an approved mission above.</div>';
      }} catch (error) {{ toast(error.message, true); }}
    }}

    document.addEventListener('click', async (event) => {{
      const runButton = event.target.closest('[data-run]');
      const verifyButton = event.target.closest('[data-verify]');
      const detailButton = event.target.closest('[data-detail]');
      const tamperButton = event.target.closest('[data-tamper]');
      if (!runButton && !verifyButton && !detailButton && !tamperButton) return;
      try {{
        if (runButton) {{
          if (busy) return; busy = true; runButton.disabled = true; runButton.textContent = 'Mission running…';
          const body = await api('/api/runs', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{mission_path:runButton.dataset.run}})}});
          toast(`Mission ${{body.run.mission_id}}: ${{body.run.proof_status}}`);
        }} else if (verifyButton) {{
          verifyButton.disabled = true;
          const body = await api('/api/verify', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{run_id:verifyButton.dataset.verify}})}});
          toast(`Reverification: ${{body.run.proof_status}}`, body.run.proof_status !== 'LOCAL_VERIFIED');
        }} else if (detailButton) {{
          const body = await api(`/api/runs/${{encodeURIComponent(detailButton.dataset.detail)}}`);
          const node = $('#evidence');
          node.innerHTML = evidenceView(body);
          node.className = 'card evidence show';
          node.scrollIntoView({{behavior:'smooth'}});
        }} else if (tamperButton) {{
          tamperButton.disabled = true;
          const body = await api('/api/tamper', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{run_id:tamperButton.dataset.runId, case:tamperButton.dataset.tamper}})}});
          const reason = body.result.errors[0] || 'tampering detected';
          toast(`${{body.result.case}} copy: ${{body.result.status}} · ${{reason}} · original preserved=${{body.result.original_preserved}}`, body.result.status !== 'FAILED');
        }}
      }} catch (error) {{ toast(error.message, true); }} finally {{ busy = false; await refresh(); }}
    }});
    refresh();
  </script>
</body>
</html>'''
