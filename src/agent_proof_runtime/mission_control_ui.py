'''Dependency-free Mission Control dashboard.'''

from __future__ import annotations

import json


_HTML = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <title>APR Mission Control</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #080b08;
      --panel: #0f1511;
      --panel-2: #141b16;
      --line: #28332b;
      --line-strong: #3b4b3f;
      --muted: #93a098;
      --text: #f2f7f3;
      --body: #c4cec7;
      --green: #39ff14;
      --green-soft: #a3ff92;
      --green-deep: #0d240d;
      --amber: #ffc857;
      --amber-deep: #241b09;
      --red: #ff3655;
      --red-deep: #2a0d14;
      --cyan: #55dcff;
      --cyan-deep: #0b2026;
      --sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --mono: "SFMono-Regular", "Cascadia Code", "Roboto Mono", Consolas, "Liberation Mono", monospace;
      font-family: var(--sans);
    }
    * { box-sizing: border-box; }
    html { background: var(--bg); }
    body { margin: 0; min-width: 300px; overflow-x: hidden; background: var(--bg); color: var(--text); }
    body::before {
      content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none; opacity: .42;
      background-image:
        repeating-linear-gradient(0deg, #d8ffe705 0, #d8ffe705 1px, transparent 1px, transparent 4px),
        linear-gradient(#16301b24 1px, transparent 1px),
        linear-gradient(90deg, #16301b24 1px, transparent 1px);
      background-size: auto, 44px 44px, 44px 44px;
      mask-image: linear-gradient(to bottom, black, transparent 86%);
    }
    body::after {
      content: ""; position: fixed; inset: 0; z-index: 0; pointer-events: none;
      background: radial-gradient(circle at 50% -10%, #39ff1409, transparent 46%);
    }
    button, a { -webkit-tap-highlight-color: transparent; }
    button:focus-visible, a:focus-visible { outline: 2px solid var(--cyan); outline-offset: 3px; }
    .shell { position: relative; z-index: 1; width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 22px 0 72px; }
    header { display: flex; align-items: center; justify-content: space-between; gap: 18px; padding-bottom: 19px; border-bottom: 1px solid var(--line); }
    .brand { display: flex; align-items: center; gap: 13px; min-width: 0; }
    .terminal-mark { display: inline-flex; align-items: center; gap: 7px; min-width: 0; padding: 9px 11px; border: 1px solid #35523a; border-radius: 8px; background: #0a110b; color: var(--green-soft); font: 700 11px/1 var(--mono); letter-spacing: .01em; box-shadow: inset 0 0 0 1px #39ff1406; }
    .terminal-mark .prompt { color: var(--green); text-shadow: 0 0 10px #39ff1470; }
    .terminal-mark .cmd { color: #7e8c83; font-weight: 500; }
    .brand-title { color: #dce5df; font-size: 14px; font-weight: 750; letter-spacing: -.015em; white-space: nowrap; }
    .system { display: inline-flex; align-items: center; gap: 9px; min-height: 32px; padding: 0 10px; border: 1px solid #564521; border-radius: 999px; background: #171208; color: var(--amber); font: 700 11px/1 var(--mono); letter-spacing: .035em; text-transform: uppercase; white-space: nowrap; }
    .dot, .status-dot { width: 8px; height: 8px; flex: 0 0 auto; border-radius: 50%; background: #657068; }
    .dot { background: var(--amber); box-shadow: 0 0 0 4px #ffc85714, 0 0 12px #ffc85745; }
    .status-dot.green { background: var(--green); box-shadow: 0 0 10px #39ff1470; }
    .status-dot.amber { background: var(--amber); box-shadow: 0 0 10px #ffc85755; }
    .status-dot.red { background: var(--red); box-shadow: 0 0 10px #ff365566; }
    .status-dot.cyan { background: var(--cyan); box-shadow: 0 0 10px #55dcff55; }
    .status-dot.dim { background: #59645d; box-shadow: none; }
    .hero { padding: clamp(50px, 9vw, 92px) 0 34px; max-width: 940px; }
    .eyebrow, .label, .section-note, .outcome-kicker { font-family: var(--mono); text-transform: uppercase; letter-spacing: .15em; }
    .eyebrow { color: var(--green); font-size: 11px; font-weight: 800; text-shadow: 0 0 12px #39ff1435; }
    h1 { margin: 14px 0 18px; max-width: 920px; font-size: clamp(42px, 8vw, 82px); line-height: .98; letter-spacing: -.062em; }
    .lead { margin: 0; max-width: 720px; color: var(--body); font-size: clamp(16px, 2.2vw, 20px); line-height: 1.58; }
    .truth { margin-top: 24px; display: inline-flex; align-items: center; gap: 10px; padding: 10px 13px; border: 1px solid #5d4820; background: var(--amber-deep); color: #f3d995; border-radius: 8px; font: 650 12px/1.4 var(--mono); }
    .truth::before { content: "!"; display: grid; place-items: center; width: 17px; height: 17px; border: 1px solid #8c6a2a; border-radius: 50%; color: var(--amber); font-size: 10px; }
    .control-room { position: relative; overflow: hidden; margin: 12px 0 24px; padding: 24px; border: 1px solid var(--line-strong); border-radius: 16px; background: linear-gradient(145deg, #101812, #090d0a 72%); box-shadow: 0 28px 90px #0008; }
    .control-room::before { content: ""; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(105deg, transparent 0 52%, #39ff1404 52% 52.2%, transparent 52.2% 100%); }
    .control-room::after { content: ""; position: absolute; width: 360px; height: 360px; right: -190px; top: -205px; border-radius: 50%; background: #39ff1409; filter: blur(8px); pointer-events: none; }
    .control-head { position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: end; gap: 20px; }
    .control-head h2 { margin-top: 7px; font-size: clamp(24px, 4vw, 38px); }
    .control-note { max-width: 410px; color: var(--muted); font-size: 13px; line-height: 1.58; text-align: right; }
    .flow { position: relative; z-index: 1; display: grid; grid-template-columns: repeat(5, minmax(128px, 1fr)); gap: 14px; margin: 25px 0 17px; overflow-x: auto; overflow-y: visible; padding: 8px 2px 8px; scrollbar-width: thin; scrollbar-color: #334238 transparent; }
    .flow-step { position: relative; min-width: 128px; min-height: 78px; padding: 14px; border: 1px solid #27312a; border-radius: 9px; background: #0a0f0b; color: #667169; opacity: .52; transition: border-color .22s ease, background .22s ease, color .22s ease, opacity .22s ease, transform .22s ease, box-shadow .22s ease; }
    .flow-step:not(:last-child)::after { content: ""; position: absolute; z-index: 2; right: -15px; top: 50%; width: 15px; height: 2px; transform: translateY(-50%); background: #344139; box-shadow: none; }
    .flow-step:not(:last-child)::before { content: ">"; position: absolute; z-index: 3; right: -17px; top: 50%; transform: translateY(-54%); color: #536057; font: 800 10px/1 var(--mono); }
    .flow-step .step-no { display: block; margin-bottom: 11px; font: 800 10px/1 var(--mono); letter-spacing: .15em; }
    .flow-step .step-name { display: block; font: 780 12px/1.25 var(--mono); letter-spacing: .055em; text-transform: uppercase; }
    .flow-step.active, .flow-step.complete { opacity: 1; border-color: #3fad2b; background: linear-gradient(145deg, #102511, #09100a); color: var(--green-soft); }
    .flow-step.active { transform: translateY(-2px); box-shadow: 0 0 0 1px #39ff1420, 0 0 24px #39ff1418; animation: activePulse 1.35s ease-in-out infinite; }
    .flow-step.complete { color: var(--green); box-shadow: inset 0 0 20px #39ff1408; }
    .flow-step.active:not(:last-child)::after, .flow-step.complete:not(:last-child)::after { background: linear-gradient(90deg, #1a6c18, var(--green), #1a6c18); background-size: 200% 100%; box-shadow: 0 0 10px #39ff1455; animation: connectorPulse 1.5s linear infinite; }
    .flow-step.active:not(:last-child)::before, .flow-step.complete:not(:last-child)::before { color: var(--green); text-shadow: 0 0 8px #39ff1470; }
    .flow-step.failed { opacity: 1; border-color: #a6283e; background: var(--red-deep); color: var(--red); box-shadow: 0 0 0 1px #ff36551f, 0 0 24px #ff365516; animation: shake .28s linear 1; }
    .outcome { position: relative; z-index: 1; display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 20px; align-items: end; min-height: 138px; overflow: hidden; padding: 21px; border: 1px solid var(--line); border-radius: 11px; background: #090e0a; transition: border-color .2s ease, background .2s ease, box-shadow .2s ease; }
    .outcome > * { position: relative; z-index: 2; }
    .outcome.working { border-color: #765a22; background: #171307; box-shadow: 0 0 22px #ffc8570e; }
    .outcome.verified { border-color: #45d32e; background: linear-gradient(135deg, #102711, #071008); box-shadow: 0 0 0 1px #39ff1420, 0 0 34px #39ff141f, inset 0 0 34px #39ff1408; }
    .outcome.verified::after { content: ""; position: absolute; z-index: 1; top: -20%; bottom: -20%; left: -24%; width: 18%; transform: skewX(-18deg); background: linear-gradient(90deg, transparent, #b8ffad30, transparent); filter: blur(1px); animation: verificationSweep .6s ease-out 1; }
    .outcome.failed { border-color: #d72f4b; background: linear-gradient(135deg, #2b0c14, #0f080a); box-shadow: 0 0 0 1px #ff36552b, 0 0 42px #ff365525, inset 0 0 30px #ff36550b; }
    .outcome.failed::before { content: ""; position: absolute; inset: 0; z-index: 1; pointer-events: none; opacity: .32; background: repeating-linear-gradient(0deg, transparent 0 4px, #ff365512 4px 5px); animation: redScan 1.5s linear 1; }
    .outcome-kicker { color: var(--muted); font-size: 10px; font-weight: 800; }
    .outcome-title { margin-top: 7px; font-size: clamp(26px, 4vw, 43px); font-weight: 850; letter-spacing: -.045em; }
    .outcome.verified .outcome-title { color: var(--green-soft); text-shadow: 0 0 18px #39ff1438; }
    .outcome.failed .outcome-title { color: #ff6b82; text-shadow: 2px 0 #55dcff50, -2px 0 #ff365565, 0 0 22px #ff36554f; animation: glitchTitle 1.35s steps(1, end) 1; }
    .outcome-copy { margin-top: 7px; max-width: 660px; color: var(--body); font-size: 13px; line-height: 1.58; }
    .outcome-metrics { display: grid; grid-template-columns: repeat(3, minmax(104px, 1fr)); gap: 8px; max-width: 450px; }
    .metric { min-width: 104px; min-height: 61px; padding: 10px 11px; border: 1px solid var(--line); border-radius: 8px; background: #101611; }
    .metric .k { color: var(--muted); font: 750 9px/1 var(--mono); letter-spacing: .11em; text-transform: uppercase; }
    .metric .v { margin-top: 7px; color: var(--text); font: 780 12px/1.25 var(--mono); overflow-wrap: anywhere; }
    .outcome.verified .metric { border-color: #2f6f2b; background: #0d1c0e; }
    .outcome.failed .metric { border-color: #692131; background: #1c0b10; }
    .stats { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); border: 1px solid var(--line); border-radius: 12px; background: #0d120e; overflow: hidden; }
    .stat { display: flex; min-width: 0; min-height: 118px; padding: 19px; flex-direction: column; justify-content: space-between; border-right: 1px solid var(--line); }
    .stat:last-child { border: 0; }
    .stat-head { display: flex; align-items: center; gap: 9px; }
    .label { color: var(--muted); font-size: 10px; font-weight: 800; }
    .value { margin-top: 16px; color: #e9f0eb; font: 800 clamp(17px, 2.5vw, 27px)/1.15 var(--mono); letter-spacing: -.035em; overflow-wrap: anywhere; }
    .section-head { margin: 54px 0 18px; display: flex; align-items: end; justify-content: space-between; gap: 20px; }
    h2 { margin: 0; font-size: 24px; letter-spacing: -.035em; }
    .section-note { color: var(--muted); font-size: 10px; }
    .missions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .card { background: var(--panel); border: 1px solid var(--line); border-radius: 12px; padding: 21px; }
    .card.featured { border-color: #38643b; box-shadow: inset 0 0 0 1px #39ff1408; }
    .card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .card h3 { margin: 5px 0 7px; font-size: 20px; letter-spacing: -.025em; }
    .path { color: var(--muted); font: 12px/1.45 var(--mono); overflow-wrap: anywhere; }
    .badge { display: inline-flex; align-items: center; min-height: 25px; padding: 4px 8px; border-radius: 999px; border: 1px solid var(--line); color: #c7d0ca; font: 750 10px/1 var(--mono); letter-spacing: .035em; text-transform: uppercase; white-space: nowrap; }
    .badge.ok { border-color: #34762f; background: #0e220f; color: var(--green-soft); }
    .badge.warn { border-color: #6b5422; background: #211908; color: var(--amber); }
    .badge.bad { border-color: #77283a; background: #251016; color: #ff7087; }
    .meta { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; margin: 20px 0; }
    .meta > div { min-width: 0; padding: 10px; border-radius: 8px; background: var(--panel-2); }
    .meta span { display: block; }
    .meta .k, .evidence-metric .k { color: var(--muted); font: 750 9px/1 var(--mono); text-transform: uppercase; letter-spacing: .1em; }
    .meta .v { margin-top: 6px; font: 700 12px/1.35 var(--mono); overflow-wrap: anywhere; }
    .actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
    button { min-height: 42px; border: 0; border-radius: 8px; padding: 0 15px; background: var(--text); color: #071008; font: 800 12px/1 var(--mono); letter-spacing: .02em; cursor: pointer; transition: transform .16s ease, background .16s ease, border-color .16s ease, box-shadow .16s ease; }
    button:hover { background: #dbe5de; transform: translateY(-1px); }
    button:disabled { cursor: not-allowed; opacity: .38; transform: none; box-shadow: none; }
    .primary { background: var(--green); color: #061006; box-shadow: 0 0 0 1px #39ff1430, 0 10px 28px #39ff141e; }
    .primary:hover { background: #72ff58; box-shadow: 0 0 24px #39ff1438; }
    .hash { margin-left: auto; color: #657269; font: 10px/1.3 var(--mono); }
    .runs { border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: var(--panel); }
    .run { display: grid; grid-template-columns: 1.4fr .8fr .8fr .7fr auto; align-items: center; gap: 14px; min-height: 74px; padding: 15px 18px; border-bottom: 1px solid var(--line); }
    .run:last-child { border: 0; }
    .run-title { font-weight: 750; }
    .run-sub { margin-top: 4px; color: var(--muted); font: 11px/1.4 var(--mono); }
    .run a, .tamper-actions a { color: var(--cyan); font: 750 12px/1 var(--mono); text-decoration: none; }
    .run a:hover, .tamper-actions a:hover { text-decoration: underline; }
    .verify { min-height: 34px; padding: 0 10px; border: 1px solid #3a4a3e; background: transparent; color: #d2dcd5; }
    .verify:hover { background: #172019; border-color: #526657; }
    .empty { padding: 34px; color: var(--muted); text-align: center; }
    .evidence { margin-top: 14px; display: none; }
    .evidence.show { display: block; }
    .evidence-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin: 14px 0 24px; }
    .evidence-metric { display: flex; min-width: 0; min-height: 94px; padding: 14px; flex-direction: column; justify-content: space-between; border: 1px solid var(--line); border-radius: 9px; background: #0b100c; }
    .evidence-metric .v { margin-top: 12px; min-width: 0; color: #d9e2dc; font: 700 12px/1.35 var(--mono); overflow-wrap: anywhere; }
    .evidence-metric .hash-chip { width: 100%; }
    .evidence-list { margin: 12px 0 0; padding: 0; list-style: none; }
    .evidence-list li { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, .9fr); gap: 12px; align-items: center; padding: 11px 0; border-bottom: 1px solid var(--line); overflow-wrap: anywhere; }
    .evidence-list li > span:first-child { font-family: var(--mono); font-size: 12px; }
    .hash-chip { display: inline-flex; align-items: center; justify-content: space-between; gap: 8px; min-width: 0; max-width: 100%; padding: 7px 8px; border: 1px solid #304037; border-radius: 7px; background: #080d09; }
    .hash-chip code { overflow: hidden; text-overflow: ellipsis; color: #b8c4bc; font: 10px/1.2 var(--mono); white-space: nowrap; }
    .copy { min-height: 26px; padding: 0 8px; border: 1px solid #415447; background: transparent; color: #c4cec7; font-size: 9px; }
    .copy:hover { background: #152018; border-color: #5c745f; }
    .tamper-flow { display: grid; grid-template-columns: repeat(4, minmax(120px, 1fr)); gap: 14px; margin: 15px 0; overflow-x: auto; padding: 7px 2px; }
    .tamper-stage { position: relative; min-width: 120px; padding: 11px 12px; border: 1px solid #29342c; border-radius: 7px; background: #090e0a; color: #657169; font: 800 10px/1.35 var(--mono); letter-spacing: .055em; text-transform: uppercase; opacity: .55; transition: all .2s ease; }
    .tamper-stage::before { content: "> "; color: #4e5c53; }
    .tamper-stage:not(:last-child)::after { content: "···>"; position: absolute; right: -15px; top: 50%; transform: translate(50%, -50%); color: #425047; font: 700 9px/1 var(--mono); }
    .tamper-stage.active { opacity: 1; border-color: #8a6926; color: var(--amber); background: var(--amber-deep); box-shadow: 0 0 18px #ffc85713; animation: terminalBlink 1s steps(2, end) infinite; }
    .tamper-stage.complete { opacity: 1; border-color: #2d6e79; color: var(--cyan); background: var(--cyan-deep); }
    .tamper-stage.failed { opacity: 1; border-color: #b52d47; color: #ff7087; background: var(--red-deep); box-shadow: 0 0 24px #ff365525; animation: shake .28s linear 1; }
    .tamper-stage.active::before { color: var(--amber); }
    .tamper-stage.complete::before { color: var(--cyan); }
    .tamper-stage.failed::before { color: var(--red); }
    .tamper-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 15px; }
    .tamper { border: 1px solid #7c2b3c; background: transparent; color: #ff7087; }
    .tamper:hover { border-color: var(--red); background: #220d13; box-shadow: 0 0 18px #ff365519; }
    .toast { position: fixed; z-index: 20; right: 20px; bottom: 20px; width: min(390px, calc(100% - 40px)); overflow: hidden; padding: 14px 16px; border: 1px solid #416148; border-radius: 8px; background: #0c150e; color: #dce6df; box-shadow: 0 18px 70px #000b, 0 0 22px #39ff1410; font: 700 12px/1.45 var(--mono); transform: translate3d(0, calc(100% + 28px), 0); transition: transform .22s ease; }
    .toast::before { content: ">"; margin-right: 8px; color: var(--green); }
    .toast.show { transform: translate3d(0, 0, 0); }
    .toast.error { border-color: #8f2c41; background: #200c12; color: #ffd4dc; box-shadow: 0 18px 70px #000b, 0 0 22px #ff365519; }
    .toast.error::before { color: var(--red); }
    .skeleton { min-height: 180px; display: grid; place-items: center; color: var(--muted); }
    footer { margin-top: 55px; padding-top: 20px; border-top: 1px solid var(--line); color: #849188; font-size: 13px; line-height: 1.65; }
    footer strong { color: var(--amber); font-family: var(--mono); }
    @keyframes activePulse { 0%, 100% { box-shadow: 0 0 0 1px #39ff141c, 0 0 18px #39ff1412; } 50% { box-shadow: 0 0 0 1px #39ff143c, 0 0 30px #39ff142a; } }
    @keyframes connectorPulse { from { background-position: 100% 0; } to { background-position: -100% 0; } }
    @keyframes verificationSweep { from { left: -24%; opacity: 0; } 15% { opacity: 1; } to { left: 118%; opacity: 0; } }
    @keyframes redScan { from { transform: translateY(-8px); } to { transform: translateY(8px); } }
    @keyframes glitchTitle { 0%, 100% { transform: translate(0); filter: none; } 14% { transform: translate(-1px, 0); } 17% { transform: translate(2px, -1px); filter: contrast(1.25); } 20% { transform: translate(0); } 48% { transform: translate(1px, 0); } 51% { transform: translate(-2px, 1px); } 55% { transform: translate(0); } }
    @keyframes terminalBlink { 0%, 46% { border-color: #8a6926; } 47%, 100% { border-color: #d5a839; } }
    @keyframes shake { 0%, 100% { transform: translateX(0); } 30% { transform: translateX(-4px); } 70% { transform: translateX(4px); } }
    @media (max-width: 900px) {
      .control-head { align-items: flex-start; flex-direction: column; }
      .control-note { text-align: left; }
      .outcome { grid-template-columns: 1fr; }
      .outcome-metrics { max-width: none; }
    }
    @media (max-width: 780px) {
      .brand-title { display: none; }
      .terminal-mark { max-width: calc(100vw - 165px); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
      .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .stat:nth-child(2) { border-right: 0; }
      .stat:nth-child(-n+2) { border-bottom: 1px solid var(--line); }
      .missions { grid-template-columns: 1fr; }
      .evidence-grid { grid-template-columns: 1fr; }
      .evidence-list li { grid-template-columns: 1fr; }
      .run { grid-template-columns: 1fr auto; }
      .run > :not(:first-child):not(:last-child) { display: none; }
      .system span:last-child { display: none; }
      .outcome-metrics { grid-template-columns: repeat(2, minmax(104px, 1fr)); }
    }
    @media (max-width: 480px) {
      .shell { width: min(100% - 20px, 1180px); }
      header { gap: 8px; }
      .terminal-mark .cmd { display: none; }
      .control-room, .card { padding: 17px; }
      .outcome-metrics { grid-template-columns: 1fr 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <header>
      <div class="brand">
        <div class="terminal-mark" aria-label="Agent Proof Runtime status command"><span class="prompt">$</span><span>agent-proof-runtime</span><span class="cmd">--status</span></div>
        <span class="brand-title">Mission Control</span>
      </div>
      <div class="system"><span class="dot" id="system-dot"></span><span id="system-status">checking runtime</span></div>
    </header>
    <main>
      <section class="hero">
        <div class="eyebrow">Agent sandbox · verifiable execution</div>
        <h1>Run autonomous work. Verify what actually happened.</h1>
        <p class="lead">Execute an approved mission, inspect deterministic acceptance evidence, and let an independent verifier detect changes to artifacts, events, or critical metadata.</p>
        <div class="truth">Development-only trust boundary. Evidence is locally verifiable and deliberately UNANCHORED.</div>
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
        <div class="stat"><div class="stat-head"><span class="status-dot dim" id="mission-dot"></span><div class="label">Missions</div></div><div class="value" id="mission-count">—</div></div>
        <div class="stat"><div class="stat-head"><span class="status-dot dim" id="run-dot"></span><div class="label">Runs</div></div><div class="value" id="run-count">—</div></div>
        <div class="stat"><div class="stat-head"><span class="status-dot dim" id="gvisor-dot"></span><div class="label">gVisor</div></div><div class="value" id="gvisor-status">—</div></div>
        <div class="stat"><div class="stat-head"><span class="status-dot dim" id="proof-dot"></span><div class="label">Latest proof</div></div><div class="value" id="proof-status">—</div></div>
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
    const token = __APR_CSRF_TOKEN__;
    const $ = (selector) => document.querySelector(selector);
    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const FLOW = ['ready', 'executing', 'acceptance', 'proof', 'verified'];
    const TAMPER_FLOW = ['ready', 'applied', 'verifying', 'failed'];
    let busy = false;

    function toast(message, error = false) {
      const node = $('#toast'); node.textContent = message; node.className = 'toast show' + (error ? ' error' : '');
      window.setTimeout(() => node.className = 'toast', 3500);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, options);
      const body = await response.json();
      if (!response.ok || !body.ok) throw new Error(body.error || `HTTP ${response.status}`);
      return body;
    }

    function wait(milliseconds) {
      return new Promise(resolve => window.setTimeout(resolve, milliseconds));
    }

    function setFlow(stage, mode = 'active') {
      const target = FLOW.indexOf(stage);
      document.querySelectorAll('.flow-step').forEach((node, index) => {
        node.classList.remove('active', 'complete', 'failed');
        if (index < target || (index === target && mode === 'complete')) node.classList.add('complete');
        else if (index === target) node.classList.add(mode === 'failed' ? 'failed' : 'active');
      });
    }

    function setOutcome(kind, kicker, title, copy, metrics = []) {
      const node = $('#outcome');
      node.className = `outcome ${kind || ''}`;
      $('#outcome-kicker').textContent = kicker;
      $('#outcome-title').textContent = title;
      $('#outcome-copy').textContent = copy;
      $('#outcome-metrics').innerHTML = metrics.map(([label, value]) => `<div class="metric"><div class="k">${esc(label)}</div><div class="v">${esc(value)}</div></div>`).join('');
    }

    function setStatusDot(id, state) {
      const node = $(id);
      if (node) node.className = `status-dot ${state}`;
    }

    function shortHash(value) {
      const text = String(value || '');
      return text.length > 22 ? `${text.slice(0, 11)}…${text.slice(-8)}` : text || '—';
    }

    function hashChip(value) {
      const text = String(value || '');
      if (!text) return '<span class="path">not available</span>';
      return `<span class="hash-chip"><code title="${esc(text)}">${esc(shortHash(text))}</code><button class="copy" data-copy="${esc(text)}">Copy</button></span>`;
    }

    function resultMetrics(run, detail = null) {
      const evidence = detail?.evidence || {};
      const acceptance = evidence.acceptance || evidence.validation || {checks: []};
      const checks = acceptance.checks || [];
      const artifacts = evidence.artifacts || [];
      const passed = checks.filter(check => check.passed).length;
      return [
        ['Mission', run.mission_status || 'UNKNOWN'],
        ['Checks', checks.length ? `${passed}/${checks.length} PASS` : 'verified'],
        ['Events', `${run.event_count ?? 0} replayed`],
        ['Anchor', run.anchor_status || 'UNKNOWN'],
        ['Artifacts', artifacts.length ? `${artifacts.length} verified` : 'verified'],
      ];
    }

    function missionCard(mission, gvisorReady, openaiConfigured) {
      if (!mission.valid) return `<article class="card"><div class="card-top"><div><div class="path">${esc(mission.path)}</div><h3>Invalid manifest</h3></div><span class="badge bad">INVALID</span></div><p class="path">${esc(mission.errors.join(' · '))}</p></article>`;
      const needsKey = mission.provider === 'openai' && !openaiConfigured;
      const blocked = (mission.backend === 'gvisor' && !gvisorReady) || needsKey;
      const featured = mission.provider === 'fixture';
      const security = mission.backend === 'gvisor' ? 'sandboxed' : (featured ? 'fixture · offline' : 'development only');
      const blockedLabel = needsKey ? 'OPENAI_API_KEY absent' : 'runsc unavailable';
      const actionLabel = featured ? 'Run verified demo' : 'Run mission';
      return `<article class="card${featured ? ' featured' : ''}"><div class="card-top"><div><div class="path">${esc(mission.path)}</div><h3>${esc(mission.title || mission.mission_id)}</h3><div class="path">${esc(mission.mission_id)} · ${esc(mission.model || 'no model')}</div></div><span class="badge ${blocked ? 'warn' : 'ok'}">${esc(security)}</span></div><div class="meta"><div><span class="k">Provider</span><span class="v">${esc(mission.provider)}</span></div><div><span class="k">Network</span><span class="v">${esc(mission.network_mode)}</span></div><div><span class="k">Limit</span><span class="v">${esc(mission.timeout_seconds)} s</span></div></div><div class="actions"><button class="${featured ? 'primary' : ''}" data-run="${esc(mission.path)}" ${blocked || busy ? 'disabled' : ''}>${blocked ? blockedLabel : actionLabel}</button><span class="hash">${esc(mission.spec_hash.slice(0, 18))}…</span></div></article>`;
    }

    function runRow(run) {
      const proofClass = run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad';
      const report = run.report_url ? `<a href="${esc(run.report_url)}" target="_blank" rel="noopener">Report ↗</a>` : '<span class="path">no report</span>';
      return `<article class="run"><div><div class="run-title">${esc(run.mission_id)}</div><div class="run-sub">${esc(run.started_at || run.run_id)} · ${esc(run.provider)} · ${esc(run.backend)}</div></div><span class="badge ${proofClass}">${esc(run.proof_status)}</span><span class="badge ${run.mission_status === 'PASSED' ? 'ok' : 'bad'}">${esc(run.mission_status)}</span><span class="badge warn">${esc(run.anchor_status)}</span><div class="actions">${report}<button class="verify" data-detail="${esc(run.run_id)}">Evidence</button><button class="verify" data-verify="${esc(run.run_id)}">Reverify original</button></div></article>`;
    }

    function evidenceView(detail) {
      const e = detail.evidence, run = detail.summary, integrity = e.integrity || {};
      const provider = e.provider || {provider:'sandbox', resolved_model:'n/a', implementation_status:'legacy sandbox'};
      const acceptance = e.acceptance || e.validation || {checks:[]};
      const artifacts = (e.artifacts || []).map(a => `<li><span>${esc(a.path)} · ${esc(a.size)} B</span>${hashChip(a.sha256)}</li>`).join('') || '<li>No artifacts</li>';
      const checks = (acceptance.checks || []).map(c => `<li><span>${esc(c.id || c.name)} · ${esc(c.type || 'legacy')}</span><span class="badge ${c.passed ? 'ok' : 'bad'}">${c.passed ? 'PASS' : 'FAIL'}</span></li>`).join('') || '<li>No checks</li>';
      const events = (e.events || []).map(item => `<li><span>${esc(item.index)} · ${esc(item.type)}</span>${hashChip(item.step_hash)}</li>`).join('');
      return `<div class="card-top"><div><div class="eyebrow">03 / Evidence</div><h2>${esc(run.mission_id)}</h2></div><span class="badge ${run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad'}">${esc(run.proof_status)}</span></div><div class="truth">Provider ${esc(provider.provider)} · ${esc(provider.resolved_model)} · ${esc(provider.implementation_status)}</div><div class="evidence-grid"><div class="evidence-metric"><span class="k">Anchor</span><span class="v"><span class="badge warn">${esc(integrity.anchor_status)}</span></span></div><div class="evidence-metric"><span class="k">Merkle root</span><span class="v">${hashChip(integrity.event_merkle_root)}</span></div><div class="evidence-metric"><span class="k">Bundle hash</span><span class="v">${hashChip(integrity.bundle_hash)}</span></div></div><h3>Artifacts and hashes</h3><ul class="evidence-list">${artifacts}</ul><h3>Acceptance checks</h3><ul class="evidence-list">${checks}</ul><h3>Event replay</h3><ul class="evidence-list">${events}</ul><h3>Tamper Lab · disposable copies</h3><div class="tamper-flow" aria-label="Tamper verification flow"><div class="tamper-stage active" data-tamper-stage="ready">Copy ready</div><div class="tamper-stage" data-tamper-stage="applied">Tamper applied</div><div class="tamper-stage" data-tamper-stage="verifying">Verifying</div><div class="tamper-stage" data-tamper-stage="failed">Integrity failed</div></div><div class="tamper-actions"><button class="tamper" data-tamper="artifact" data-run-id="${esc(run.run_id)}">Tamper artifact</button><button class="tamper" data-tamper="event" data-run-id="${esc(run.run_id)}">Tamper event</button><button class="tamper" data-tamper="metadata" data-run-id="${esc(run.run_id)}">Tamper metadata</button><a href="${esc(run.bundle_url)}" target="_blank" rel="noopener">Proof Bundle ↗</a></div>`;
    }

    function setTamperFlow(stage, failed = false) {
      const target = TAMPER_FLOW.indexOf(stage);
      document.querySelectorAll('[data-tamper-stage]').forEach((node, index) => {
        node.classList.remove('active', 'complete', 'failed');
        if (index < target) node.classList.add('complete');
        else if (index === target) node.classList.add(failed ? 'failed' : 'active');
      });
    }

    async function refresh() {
      try {
        const data = await api('/api/state');
        const ready = Boolean(data.doctor.available);
        const validMissionCount = data.missions.filter(m => m.valid).length;
        const latestProof = data.runs[0]?.proof_status || 'NO RUNS YET';
        $('#mission-count').textContent = validMissionCount;
        $('#run-count').textContent = data.runs.length;
        $('#gvisor-status').textContent = ready ? 'READY' : 'OFFLINE';
        $('#gvisor-status').style.color = ready ? 'var(--green-soft)' : 'var(--amber)';
        $('#proof-status').textContent = latestProof;
        $('#proof-status').style.color = latestProof === 'LOCAL_VERIFIED' ? 'var(--green-soft)' : (latestProof === 'FAILED' ? 'var(--red)' : 'inherit');
        $('#system-status').textContent = ready ? 'gVisor ready' : 'fixture mode · runsc unavailable';
        $('#system-dot').style.background = ready ? 'var(--green)' : 'var(--amber)';
        $('#system-dot').style.boxShadow = ready ? '0 0 0 4px #39ff1414, 0 0 12px #39ff1460' : '0 0 0 4px #ffc85714, 0 0 12px #ffc85745';
        setStatusDot('#mission-dot', validMissionCount ? 'green' : 'red');
        setStatusDot('#run-dot', data.runs.length ? 'cyan' : 'dim');
        setStatusDot('#gvisor-dot', ready ? 'green' : 'amber');
        setStatusDot('#proof-dot', latestProof === 'LOCAL_VERIFIED' ? 'green' : (latestProof === 'FAILED' ? 'red' : 'amber'));
        $('#missions').innerHTML = data.missions.length ? data.missions.map(m => missionCard(m, ready, data.service.openai_configured)).join('') : '<div class="card empty">No manifests in the configured directory.</div>';
        $('#runs').innerHTML = data.runs.length ? data.runs.map(runRow).join('') : '<div class="empty">No runs yet. Start an approved mission above.</div>';
      } catch (error) { toast(error.message, true); }
    }

    document.addEventListener('click', async (event) => {
      const copyButton = event.target.closest('[data-copy]');
      if (copyButton) {
        try {
          await navigator.clipboard.writeText(copyButton.dataset.copy);
          toast('Hash copied');
        } catch (error) {
          toast('Clipboard access failed', true);
        }
        return;
      }

      const runButton = event.target.closest('[data-run]');
      const verifyButton = event.target.closest('[data-verify]');
      const detailButton = event.target.closest('[data-detail]');
      const tamperButton = event.target.closest('[data-tamper]');
      if (!runButton && !verifyButton && !detailButton && !tamperButton) return;
      try {
        if (runButton) {
          if (busy) return;
          busy = true;
          runButton.disabled = true;
          runButton.textContent = 'Executing…';
          setFlow('executing');
          setOutcome('working', 'Mission running', 'Controlled execution in progress', 'The approved manifest is executing inside the configured runtime boundary.');
          const body = await api('/api/runs', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({mission_path:runButton.dataset.run})});
          setFlow('acceptance');
          await wait(220);
          setFlow('proof');
          const detail = await api(`/api/runs/${encodeURIComponent(body.run.run_id)}`);
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
          toast(`Mission ${body.run.mission_id}: ${body.run.proof_status}`, !verified);
        } else if (verifyButton) {
          verifyButton.disabled = true;
          setOutcome('working', 'Reverifying original', 'Independent replay in progress', 'The original Proof Bundle is being verified again.');
          const body = await api('/api/verify', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({run_id:verifyButton.dataset.verify})});
          const verified = body.run.proof_status === 'LOCAL_VERIFIED';
          setFlow(verified ? 'verified' : 'proof', verified ? 'complete' : 'failed');
          setOutcome(
            verified ? 'verified' : 'failed',
            verified ? 'Original preserved' : 'Original verification failed',
            body.run.proof_status,
            verified ? 'Tamper Lab changed only disposable copies. The original evidence remains valid.' : 'The original evidence did not pass independent verification.',
            resultMetrics(body.run),
          );
          toast(`Reverification: ${body.run.proof_status}`, !verified);
        } else if (detailButton) {
          const body = await api(`/api/runs/${encodeURIComponent(detailButton.dataset.detail)}`);
          const node = $('#evidence');
          node.innerHTML = evidenceView(body);
          node.className = 'card evidence show';
          node.scrollIntoView({behavior:'smooth'});
        } else if (tamperButton) {
          tamperButton.disabled = true;
          setTamperFlow('applied');
          setOutcome('working', 'Tamper Lab', 'Applying controlled evidence mutation', 'A disposable copy is being changed and passed to the independent verifier.');
          const body = await api('/api/tamper', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({run_id:tamperButton.dataset.runId, case:tamperButton.dataset.tamper})});
          setTamperFlow('verifying');
          await wait(220);
          const detected = body.result.status === 'FAILED';
          setTamperFlow(detected ? 'failed' : 'verifying', detected);
          const reason = body.result.errors[0] || 'tampering detected';
          setOutcome(
            detected ? 'failed' : 'verified',
            detected ? 'Tampering detected' : 'Unexpected verifier result',
            detected ? 'INTEGRITY FAILED' : body.result.status,
            `${reason} · original preserved=${body.result.original_preserved}`,
            [['Case', body.result.case], ['Copy', body.result.status], ['Original', body.result.original_preserved ? 'preserved' : 'changed']],
          );
          toast(`${body.result.case} copy: ${body.result.status} · original preserved=${body.result.original_preserved}`, !detected);
        }
      } catch (error) {
        setOutcome('failed', 'Request failed', 'Mission Control rejected the action', error.message);
        toast(error.message, true);
      } finally {
        busy = false;
        await refresh();
      }
    });
    refresh();
  </script>
</body>
</html>'''


def render_mission_control(csrf_token: str) -> str:
    return _HTML.replace('__APR_CSRF_TOKEN__', json.dumps(csrf_token))
