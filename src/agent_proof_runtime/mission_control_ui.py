'''Dependency-free Mission Control dashboard.'''

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
      --bg: #070a0c;
      --panel: #101519;
      --panel-2: #151c21;
      --line: #26323a;
      --line-strong: #3b4a54;
      --muted: #8e9aa4;
      --text: #f4f7f8;
      --green: #70e1a1;
      --green-deep: #11281c;
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
      background-size: 40px 40px; mask-image: linear-gradient(to bottom, black, transparent 72%);
    }}
    button, a {{ -webkit-tap-highlight-color: transparent; }}
    button:focus-visible, a:focus-visible {{ outline: 2px solid var(--blue); outline-offset: 3px; }}
    .shell {{ position: relative; width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 24px 0 72px; }}
    header {{ display: flex; align-items: center; justify-content: space-between; gap: 16px; padding-bottom: 22px; border-bottom: 1px solid var(--line); }}
    .brand {{ display: flex; align-items: center; gap: 12px; font-weight: 720; letter-spacing: -.02em; }}
    .mark {{ width: 34px; height: 34px; display: grid; place-items: center; border: 1px solid #3b4854; border-radius: 9px; background: #151a1f; color: var(--green); font: 800 15px/1 ui-monospace, monospace; }}
    .system {{ display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 13px; }}
    .dot {{ width: 8px; height: 8px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 0 4px #f2bd6418; }}
    .hero {{ padding: clamp(50px, 9vw, 96px) 0 34px; max-width: 920px; }}
    .eyebrow {{ color: var(--green); text-transform: uppercase; letter-spacing: .16em; font-size: 11px; font-weight: 760; }}
    h1 {{ margin: 14px 0 18px; font-size: clamp(42px, 8vw, 82px); line-height: .98; letter-spacing: -.062em; max-width: 900px; }}
    .lead {{ margin: 0; max-width: 710px; color: #b4bec7; font-size: clamp(16px, 2.2vw, 20px); line-height: 1.55; }}
    .truth {{ margin-top: 24px; display: inline-flex; align-items: center; gap: 10px; padding: 10px 13px; border: 1px solid #4b3b21; background: #1d1810; color: #e8c98f; border-radius: 9px; font-size: 13px; }}
    .control-room {{ position: relative; overflow: hidden; margin: 12px 0 24px; padding: 24px; border: 1px solid var(--line-strong); border-radius: 18px; background: linear-gradient(145deg, #11181d, #0b1014 68%); box-shadow: 0 24px 80px #0006; }}
    .control-room::after {{ content: ""; position: absolute; width: 340px; height: 340px; right: -170px; top: -190px; border-radius: 50%; background: #70e1a10d; filter: blur(8px); pointer-events: none; }}
    .control-head {{ position: relative; display: flex; justify-content: space-between; align-items: end; gap: 20px; }}
    .control-head h2 {{ margin-top: 6px; font-size: clamp(24px, 4vw, 38px); }}
    .control-note {{ max-width: 390px; color: var(--muted); font-size: 13px; line-height: 1.55; text-align: right; }}
    .flow {{ position: relative; display: grid; grid-template-columns: repeat(5, minmax(120px, 1fr)); gap: 8px; margin: 24px 0 16px; overflow-x: auto; padding-bottom: 4px; }}
    .flow-step {{ position: relative; min-width: 128px; padding: 14px; border: 1px solid var(--line); border-radius: 11px; background: #0c1115; color: #65727d; transition: border-color .22s ease, background .22s ease, color .22s ease, transform .22s ease; }}
    .flow-step:not(:last-child)::after {{ content: "→"; position: absolute; z-index: 2; right: -9px; top: 50%; transform: translate(50%, -50%); color: #52606a; font-weight: 800; }}
    .flow-step .step-no {{ display: block; margin-bottom: 10px; font: 700 10px/1 ui-monospace, monospace; letter-spacing: .12em; }}
    .flow-step .step-name {{ display: block; font-size: 12px; font-weight: 780; letter-spacing: .04em; text-transform: uppercase; }}
    .flow-step.active {{ border-color: #8a6936; background: #1d1810; color: var(--amber); transform: translateY(-2px); animation: pulse 1.1s ease-in-out infinite; }}
    .flow-step.complete {{ border-color: #24583c; background: var(--green-deep); color: var(--green); }}
    .flow-step.failed {{ border-color: #71352f; background: #2a1513; color: var(--red); animation: shake .28s linear 1; }}
    .outcome {{ position: relative; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 20px; align-items: end; min-height: 128px; padding: 20px; border: 1px solid var(--line); border-radius: 13px; background: #0a0f12; transition: border-color .2s ease, background .2s ease; }}
    .outcome.working {{ border-color: #66502c; background: #17140f; }}
    .outcome.verified {{ border-color: #2b6747; background: linear-gradient(135deg, #10251a, #0a1110); animation: verifiedPulse .45s ease-out 1; }}
    .outcome.failed {{ border-color: #71352f; background: linear-gradient(135deg, #2a1513, #100c0c); animation: shake .28s linear 1; }}
    .outcome-kicker {{ color: var(--muted); font-size: 10px; font-weight: 760; letter-spacing: .14em; text-transform: uppercase; }}
    .outcome-title {{ margin-top: 7px; font-size: clamp(25px, 4vw, 42px); font-weight: 820; letter-spacing: -.045em; }}
    .outcome-copy {{ margin-top: 7px; max-width: 650px; color: #aeb9c1; font-size: 13px; line-height: 1.55; }}
    .outcome-metrics {{ display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; max-width: 430px; }}
    .metric {{ min-width: 104px; padding: 10px 11px; border: 1px solid var(--line); border-radius: 9px; background: #11171b; }}
    .metric .k {{ color: var(--muted); font-size: 9px; letter-spacing: .1em; text-transform: uppercase; }}
    .metric .v {{ margin-top: 5px; color: var(--text); font: 750 12px/1.25 ui-monospace, monospace; }}
    .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); border: 1px solid var(--line); border-radius: 14px; background: #0e1215; overflow: hidden; }}
    .stat {{ padding: 20px; min-height: 100px; border-right: 1px solid var(--line); }} .stat:last-child {{ border: 0; }}
    .label {{ color: var(--muted); font-size: 11px; font-weight: 720; letter-spacing: .1em; text-transform: uppercase; }}
    .value {{ margin-top: 13px; font-size: clamp(18px, 3vw, 28px); letter-spacing: -.03em; overflow-wrap: anywhere; }}
    .section-head {{ margin: 54px 0 18px; display: flex; align-items: end; justify-content: space-between; gap: 20px; }}
    h2 {{ margin: 0; font-size: 24px; letter-spacing: -.035em; }}
    .section-note {{ color: var(--muted); font-size: 13px; }}
    .missions {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }}
    .card {{ background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 21px; }}
    .card.featured {{ border-color: #315e47; box-shadow: inset 0 0 0 1px #70e1a10a; }}
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
    button {{ min-height: 42px; border: 0; border-radius: 9px; padding: 0 15px; background: var(--text); color: #090b0d; font: 700 13px/1 inherit; cursor: pointer; transition: transform .16s ease, background .16s ease, border-color .16s ease; }}
    button:hover {{ background: #dbe2e7; transform: translateY(-1px); }} button:disabled {{ cursor: not-allowed; opacity: .38; transform: none; }}
    .primary {{ background: var(--green); color: #07100b; box-shadow: 0 10px 28px #70e1a118; }}
    .primary:hover {{ background: #8ce9b5; }}
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
    .evidence-list li {{ display: grid; grid-template-columns: 1.1fr .9fr; gap: 12px; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--line); overflow-wrap: anywhere; }}
    .hash-chip {{ display: inline-flex; align-items: center; justify-content: space-between; gap: 8px; min-width: 0; padding: 7px 8px; border: 1px solid #2d3941; border-radius: 8px; background: #0b1013; }}
    .hash-chip code {{ overflow: hidden; text-overflow: ellipsis; color: #aab6be; font-size: 10px; white-space: nowrap; }}
    .copy {{ min-height: 26px; padding: 0 8px; border: 1px solid #3a4650; background: transparent; color: #b9c4cb; font-size: 10px; }}
    .tamper-flow {{ display: grid; grid-template-columns: repeat(4, minmax(110px, 1fr)); gap: 8px; margin: 14px 0; overflow-x: auto; }}
    .tamper-stage {{ min-width: 114px; padding: 10px; border: 1px solid var(--line); border-radius: 9px; background: #0c1115; color: #65727d; font: 700 10px/1.3 ui-monospace, monospace; text-transform: uppercase; }}
    .tamper-stage.active {{ border-color: #66502c; color: var(--amber); background: #1d1810; }}
    .tamper-stage.complete {{ border-color: #3f4c55; color: #b9c4cb; }}
    .tamper-stage.failed {{ border-color: #71352f; color: var(--red); background: #2a1513; animation: shake .28s linear 1; }}
    .tamper-actions {{ display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 15px; }}
    .tamper {{ background: transparent; color: var(--red); border: 1px solid #64302c; }}
    .toast {{ position: fixed; z-index: 20; right: 20px; bottom: 20px; width: min(390px, calc(100% - 40px)); padding: 14px 16px; border-radius: 10px; background: #e9eff3; color: #111519; box-shadow: 0 18px 70px #0009; font-size: 13px; transform: translateY(130%); transition: transform .22s ease; }}
    .toast.show {{ transform: translateY(0); }} .toast.error {{ background: #ffd8d5; color: #3a1110; }}
    .skeleton {{ min-height: 180px; display: grid; place-items: center; color: var(--muted); }}
    footer {{ margin-top: 55px; padding-top: 20px; border-top: 1px solid var(--line); color: #79858e; font-size: 13px; line-height: 1.65; }}
    @keyframes pulse {{ 0%, 100% {{ box-shadow: 0 0 0 0 #f2bd6400; }} 50% {{ box-shadow: 0 0 0 5px #f2bd6412; }} }}
    @keyframes verifiedPulse {{ from {{ box-shadow: 0 0 0 0 #70e1a133; }} to {{ box-shadow: 0 0 0 14px #70e1a100; }} }}
    @keyframes shake {{ 0%, 100% {{ transform: translateX(0); }} 30% {{ transform: translateX(-4px); }} 70% {{ transform: translateX(4px); }} }}
    @media (max-width: 900px) {{
      .control-head {{ align-items: flex-start; flex-direction: column; }}
      .control-note {{ text-align: left; }}
      .outcome {{ grid-template-columns: 1fr; }}
      .outcome-metrics {{ justify-content: flex-start; max-width: none; }}
    }}
    @media (max-width: 780px) {{
      .stats {{ grid-template-columns: repeat(2, 1fr); }} .stat:nth-child(2) {{ border-right: 0; }} .stat:nth-child(-n+2) {{ border-bottom: 1px solid var(--line); }}
      .missions {{ grid-template-columns: 1fr; }}
      .evidence-grid {{ grid-template-columns: 1fr; }}
      .evidence-list li {{ grid-template-columns: 1fr; }}
      .run {{ grid-template-columns: 1fr auto; }} .run > :not(:first-child):not(:last-child) {{ display: none; }}
      .system span:last-child {{ display: none; }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{ animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }}
    }}
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
        <h1>Run autonomous work. Verify what actually happened.</h1>
        <p class="lead">Execute an approved mission, inspect deterministic acceptance evidence, and let an independent verifier detect changes to artifacts, events, or critical metadata.</p>
        <div class="truth">● Development-only trust boundary. Evidence is locally verifiable and deliberately UNANCHORED.</div>
      </section>

      <section class="control-room" aria-label="Verified execution flow">
        <div class="control-head">
          <div><div class="eyebrow">Live execution narrative</div><h2>Evidence Control Room</h2></div>
          <div class="control-note">The interface visualizes the checked-in runtime path. Proof Bundle data and independent verification remain the source of truth.</div>
        </div>
        <div class="flow" id="flow">
          <div class="flow-step active" data-step="ready"><span class="step-no">01</span><span class="step-name">Mission ready</span></div>
          <div class="flow-step" data-step="executing"><span class="step-no">02</span><span class="step-name">Executing</span></div>
          <div class="flow-step" data-step="acceptance"><span class="step-no">03</span><span class="step-name">Acceptance</span></div>
          <div class="flow-step" data-step="proof"><span class="step-no">04</span><span class="step-name">Building proof</span></div>
          <div class="flow-step" data-step="verified"><span class="step-no">05</span><span class="step-name">Local verified</span></div>
        </div>
        <div class="outcome" id="outcome">
          <div>
            <div class="outcome-kicker" id="outcome-kicker">Verified execution path</div>
            <div class="outcome-title" id="outcome-title">Choose an approved mission</div>
            <div class="outcome-copy" id="outcome-copy">The deterministic fixture path is offline, repeatable, and requires no API key.</div>
          </div>
          <div class="outcome-metrics" id="outcome-metrics"></div>
        </div>
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
    const FLOW = ['ready', 'executing', 'acceptance', 'proof', 'verified'];
    const TAMPER_FLOW = ['ready', 'applied', 'verifying', 'failed'];
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

    function wait(milliseconds) {{
      return new Promise(resolve => window.setTimeout(resolve, milliseconds));
    }}

    function setFlow(stage, mode = 'active') {{
      const target = FLOW.indexOf(stage);
      document.querySelectorAll('.flow-step').forEach((node, index) => {{
        node.classList.remove('active', 'complete', 'failed');
        if (index < target || (index === target && mode === 'complete')) node.classList.add('complete');
        else if (index === target) node.classList.add(mode === 'failed' ? 'failed' : 'active');
      }});
    }}

    function setOutcome(kind, kicker, title, copy, metrics = []) {{
      const node = $('#outcome');
      node.className = `outcome ${{kind || ''}}`;
      $('#outcome-kicker').textContent = kicker;
      $('#outcome-title').textContent = title;
      $('#outcome-copy').textContent = copy;
      $('#outcome-metrics').innerHTML = metrics.map(([label, value]) => `<div class="metric"><div class="k">${{esc(label)}}</div><div class="v">${{esc(value)}}</div></div>`).join('');
    }}

    function shortHash(value) {{
      const text = String(value || '');
      return text.length > 22 ? `${{text.slice(0, 11)}}…${{text.slice(-8)}}` : text || '—';
    }}

    function hashChip(value) {{
      const text = String(value || '');
      if (!text) return '<span class="path">not available</span>';
      return `<span class="hash-chip"><code title="${{esc(text)}}">${{esc(shortHash(text))}}</code><button class="copy" data-copy="${{esc(text)}}">Copy</button></span>`;
    }}

    function resultMetrics(run, detail = null) {{
      const evidence = detail?.evidence || {{}};
      const acceptance = evidence.acceptance || evidence.validation || {{checks: []}};
      const checks = acceptance.checks || [];
      const artifacts = evidence.artifacts || [];
      const passed = checks.filter(check => check.passed).length;
      return [
        ['Mission', run.mission_status || 'UNKNOWN'],
        ['Checks', checks.length ? `${{passed}}/${{checks.length}} PASS` : 'verified'],
        ['Events', `${{run.event_count ?? 0}} replayed`],
        ['Anchor', run.anchor_status || 'UNKNOWN'],
        ['Artifacts', artifacts.length ? `${{artifacts.length}} verified` : 'verified'],
      ];
    }}

    function missionCard(mission, gvisorReady, openaiConfigured) {{
      if (!mission.valid) return `<article class="card"><div class="card-top"><div><div class="path">${{esc(mission.path)}}</div><h3>Invalid manifest</h3></div><span class="badge bad">INVALID</span></div><p class="path">${{esc(mission.errors.join(' · '))}}</p></article>`;
      const needsKey = mission.provider === 'openai' && !openaiConfigured;
      const blocked = (mission.backend === 'gvisor' && !gvisorReady) || needsKey;
      const featured = mission.provider === 'fixture';
      const security = mission.backend === 'gvisor' ? 'sandboxed' : (featured ? 'fixture · offline' : 'development only');
      const blockedLabel = needsKey ? 'OPENAI_API_KEY absent' : 'runsc unavailable';
      const actionLabel = featured ? 'Run verified demo' : 'Run mission';
      return `<article class="card${{featured ? ' featured' : ''}}"><div class="card-top"><div><div class="path">${{esc(mission.path)}}</div><h3>${{esc(mission.title || mission.mission_id)}}</h3><div class="path">${{esc(mission.mission_id)}} · ${{esc(mission.model || 'no model')}}</div></div><span class="badge ${{blocked ? 'warn' : 'ok'}}">${{esc(security)}}</span></div><div class="meta"><div><span class="k">Provider</span><span class="v">${{esc(mission.provider)}}</span></div><div><span class="k">Network</span><span class="v">${{esc(mission.network_mode)}}</span></div><div><span class="k">Limit</span><span class="v">${{esc(mission.timeout_seconds)}} s</span></div></div><div class="actions"><button class="${{featured ? 'primary' : ''}}" data-run="${{esc(mission.path)}}" ${{blocked || busy ? 'disabled' : ''}}>${{blocked ? blockedLabel : actionLabel}}</button><span class="hash">${{esc(mission.spec_hash.slice(0, 18))}}…</span></div></article>`;
    }}

    function runRow(run) {{
      const proofClass = run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad';
      const report = run.report_url ? `<a href="${{esc(run.report_url)}}" target="_blank" rel="noopener">Report ↗</a>` : '<span class="path">no report</span>';
      return `<article class="run"><div><div class="run-title">${{esc(run.mission_id)}}</div><div class="run-sub">${{esc(run.started_at || run.run_id)}} · ${{esc(run.provider)}} · ${{esc(run.backend)}}</div></div><span class="badge ${{proofClass}}">${{esc(run.proof_status)}}</span><span class="badge ${{run.mission_status === 'PASSED' ? 'ok' : 'bad'}}">${{esc(run.mission_status)}}</span><span class="badge warn">${{esc(run.anchor_status)}}</span><div class="actions">${{report}}<button class="verify" data-detail="${{esc(run.run_id)}}">Evidence</button><button class="verify" data-verify="${{esc(run.run_id)}}">Reverify original</button></div></article>`;
    }}

    function evidenceView(detail) {{
      const e = detail.evidence, run = detail.summary, integrity = e.integrity || {{}};
      const provider = e.provider || {{provider:'sandbox', resolved_model:'n/a', implementation_status:'legacy sandbox'}};
      const acceptance = e.acceptance || e.validation || {{checks:[]}};
      const artifacts = (e.artifacts || []).map(a => `<li><span>${{esc(a.path)}} · ${{esc(a.size)}} B</span>${{hashChip(a.sha256)}}</li>`).join('') || '<li>No artifacts</li>';
      const checks = (acceptance.checks || []).map(c => `<li><span>${{esc(c.id || c.name)}} · ${{esc(c.type || 'legacy')}}</span><span class="badge ${{c.passed ? 'ok' : 'bad'}}">${{c.passed ? 'PASS' : 'FAIL'}}</span></li>`).join('') || '<li>No checks</li>';
      const events = (e.events || []).map(item => `<li><span>${{esc(item.index)}} · ${{esc(item.type)}}</span>${{hashChip(item.step_hash)}}</li>`).join('');
      return `<div class="card-top"><div><div class="eyebrow">03 / Evidence</div><h2>${{esc(run.mission_id)}}</h2></div><span class="badge ${{run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad'}}">${{esc(run.proof_status)}}</span></div><div class="truth">Provider ${{esc(provider.provider)}} · ${{esc(provider.resolved_model)}} · ${{esc(provider.implementation_status)}}</div><div class="evidence-grid"><div class="meta"><div><span class="k">Anchor</span><span class="v">${{esc(integrity.anchor_status)}}</span></div></div><div class="meta"><div><span class="k">Merkle root</span><span class="v">${{hashChip(integrity.event_merkle_root)}}</span></div></div><div class="meta"><div><span class="k">Bundle hash</span><span class="v">${{hashChip(integrity.bundle_hash)}}</span></div></div></div><h3>Artifacts and hashes</h3><ul class="evidence-list">${{artifacts}}</ul><h3>Acceptance checks</h3><ul class="evidence-list">${{checks}}</ul><h3>Event replay</h3><ul class="evidence-list">${{events}}</ul><h3>Tamper Lab · disposable copies</h3><div class="tamper-flow" aria-label="Tamper verification flow"><div class="tamper-stage active" data-tamper-stage="ready">Copy ready</div><div class="tamper-stage" data-tamper-stage="applied">Tamper applied</div><div class="tamper-stage" data-tamper-stage="verifying">Verifying</div><div class="tamper-stage" data-tamper-stage="failed">Integrity failed</div></div><div class="tamper-actions"><button class="tamper" data-tamper="artifact" data-run-id="${{esc(run.run_id)}}">Tamper artifact</button><button class="tamper" data-tamper="event" data-run-id="${{esc(run.run_id)}}">Tamper event</button><button class="tamper" data-tamper="metadata" data-run-id="${{esc(run.run_id)}}">Tamper metadata</button><a href="${{esc(run.bundle_url)}}" target="_blank" rel="noopener">Proof Bundle ↗</a></div>`;
    }}

    function setTamperFlow(stage, failed = false) {{
      const target = TAMPER_FLOW.indexOf(stage);
      document.querySelectorAll('[data-tamper-stage]').forEach((node, index) => {{
        node.classList.remove('active', 'complete', 'failed');
        if (index < target) node.classList.add('complete');
        else if (index === target) node.classList.add(failed ? 'failed' : 'active');
      }});
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
      const copyButton = event.target.closest('[data-copy]');
      if (copyButton) {{
        try {{
          await navigator.clipboard.writeText(copyButton.dataset.copy);
          toast('Hash copied');
        }} catch (error) {{
          toast('Clipboard access failed', true);
        }}
        return;
      }}

      const runButton = event.target.closest('[data-run]');
      const verifyButton = event.target.closest('[data-verify]');
      const detailButton = event.target.closest('[data-detail]');
      const tamperButton = event.target.closest('[data-tamper]');
      if (!runButton && !verifyButton && !detailButton && !tamperButton) return;
      try {{
        if (runButton) {{
          if (busy) return;
          busy = true;
          runButton.disabled = true;
          runButton.textContent = 'Executing…';
          setFlow('executing');
          setOutcome('working', 'Mission running', 'Controlled execution in progress', 'The approved manifest is executing inside the configured runtime boundary.');
          const body = await api('/api/runs', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{mission_path:runButton.dataset.run}})}});
          setFlow('acceptance');
          await wait(220);
          setFlow('proof');
          const detail = await api(`/api/runs/${{encodeURIComponent(body.run.run_id)}}`);
          await wait(220);
          const verified = body.run.proof_status === 'LOCAL_VERIFIED';
          setFlow(verified ? 'verified' : 'proof', verified ? 'complete' : 'failed');
          setOutcome(
            verified ? 'verified' : 'failed',
            verified ? 'Mission passed' : 'Verification failed',
            body.run.proof_status,
            verified ? 'Independent verification replayed the event chain and confirmed the stored evidence.' : 'The verifier rejected the resulting evidence.',
            resultMetrics(body.run, detail),
          );
          toast(`Mission ${{body.run.mission_id}}: ${{body.run.proof_status}}`, !verified);
        }} else if (verifyButton) {{
          verifyButton.disabled = true;
          setOutcome('working', 'Reverifying original', 'Independent replay in progress', 'The original Proof Bundle is being verified again.');
          const body = await api('/api/verify', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{run_id:verifyButton.dataset.verify}})}});
          const verified = body.run.proof_status === 'LOCAL_VERIFIED';
          setFlow(verified ? 'verified' : 'proof', verified ? 'complete' : 'failed');
          setOutcome(
            verified ? 'verified' : 'failed',
            verified ? 'Original preserved' : 'Original verification failed',
            body.run.proof_status,
            verified ? 'Tamper Lab changed only disposable copies. The original evidence remains valid.' : 'The original evidence did not pass independent verification.',
            resultMetrics(body.run),
          );
          toast(`Reverification: ${{body.run.proof_status}}`, !verified);
        }} else if (detailButton) {{
          const body = await api(`/api/runs/${{encodeURIComponent(detailButton.dataset.detail)}}`);
          const node = $('#evidence');
          node.innerHTML = evidenceView(body);
          node.className = 'card evidence show';
          node.scrollIntoView({{behavior:'smooth'}});
        }} else if (tamperButton) {{
          tamperButton.disabled = true;
          setTamperFlow('applied');
          setOutcome('working', 'Tamper Lab', 'Applying controlled evidence mutation', 'A disposable copy is being changed and passed to the independent verifier.');
          const body = await api('/api/tamper', {{method:'POST', headers:{{'Content-Type':'application/json','X-APR-Token':token}}, body:JSON.stringify({{run_id:tamperButton.dataset.runId, case:tamperButton.dataset.tamper}})}});
          setTamperFlow('verifying');
          await wait(220);
          const detected = body.result.status === 'FAILED';
          setTamperFlow(detected ? 'failed' : 'verifying', detected);
          const reason = body.result.errors[0] || 'tampering detected';
          setOutcome(
            detected ? 'failed' : 'verified',
            detected ? 'Tampering detected' : 'Unexpected verifier result',
            detected ? 'INTEGRITY FAILED' : body.result.status,
            `${{reason}} · original preserved=${{body.result.original_preserved}}`,
            [['Case', body.result.case], ['Copy', body.result.status], ['Original', body.result.original_preserved ? 'preserved' : 'changed']],
          );
          toast(`${{body.result.case}} copy: ${{body.result.status}} · original preserved=${{body.result.original_preserved}}`, !detected);
        }}
      }} catch (error) {{
        setOutcome('failed', 'Request failed', 'Mission Control rejected the action', error.message);
        toast(error.message, true);
      }} finally {{
        busy = false;
        await refresh();
      }}
    }});
    refresh();
  </script>
</body>
</html>'''
