
from __future__ import annotations

import base64
import json
from pathlib import Path

_OSA_BRAND_PATH = Path(__file__).with_name("assets") / "osa-brand-source.jpg"


_DASHBOARD = r'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark">
  <meta name="theme-color" content="#050d10">
  <title>OsaTechGPT · APR Mission Control</title>
  <style>
    :root {
      color-scheme: dark;
      --board: #050d10;
      --board-deep: #020709;
      --panel: rgba(8, 21, 25, .94);
      --panel-strong: #0a171b;
      --panel-soft: #0d1d22;
      --line: #20363d;
      --line-hot: #35e7df;
      --cyan: #36f0e4;
      --cyan-soft: #8cfbf4;
      --green: #68f79a;
      --amber: #f4bd56;
      --red: #ff5d68;
      --blue: #75a9ff;
      --text: #eef9fa;
      --muted: #839aa1;
      --mono: "IBM Plex Mono", "Cascadia Code", "SFMono-Regular", Consolas, monospace;
      --sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-family: var(--sans);
    }

    * { box-sizing: border-box; }
    html { scroll-behavior: smooth; }
    body {
      margin: 0;
      min-width: 320px;
      overflow-x: hidden;
      color: var(--text);
      background:
        radial-gradient(circle at 50% -12%, rgba(47, 231, 221, .14), transparent 34rem),
        radial-gradient(circle at 7% 24%, rgba(39, 112, 122, .11), transparent 24rem),
        linear-gradient(180deg, #071216 0%, var(--board) 44%, var(--board-deep) 100%);
    }

    body::before {
      content: "";
      position: fixed;
      inset: 0;
      pointer-events: none;
      opacity: .3;
      background-image:
        radial-gradient(circle, rgba(72, 201, 196, .42) 1px, transparent 1.6px),
        linear-gradient(90deg, transparent 49.7%, rgba(45, 113, 119, .18) 50%, transparent 50.3%),
        linear-gradient(0deg, transparent 49.7%, rgba(45, 113, 119, .12) 50%, transparent 50.3%);
      background-size: 22px 22px, 176px 176px, 176px 176px;
      mask-image: linear-gradient(to bottom, black 0%, rgba(0,0,0,.88) 72%, transparent 100%);
    }

    .board-traces {
      position: fixed;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
      z-index: 0;
      opacity: .34;
      filter: drop-shadow(0 0 7px rgba(54, 240, 228, .16));
    }
    .board-traces .trace { fill: none; stroke: #1c7d80; stroke-width: 2; vector-effect: non-scaling-stroke; }
    .board-traces .trace.hot { stroke: #35e7df; stroke-dasharray: 4 18; animation: trace-flow 8s linear infinite; }
    .board-traces .trace.fail { stroke: #ff5d68; stroke-dasharray: 2 24; animation: trace-flow 5s linear infinite reverse; }
    .board-traces .via { fill: #061114; stroke: #35e7df; stroke-width: 2; vector-effect: non-scaling-stroke; }

    @keyframes trace-flow { to { stroke-dashoffset: -176; } }
    @keyframes signal-pulse {
      0%, 100% { opacity: .55; box-shadow: 0 0 0 0 rgba(54, 240, 228, .08); }
      50% { opacity: 1; box-shadow: 0 0 0 7px rgba(54, 240, 228, 0); }
    }
    @keyframes danger-pulse {
      0%, 100% { box-shadow: inset 0 0 28px rgba(255, 57, 74, .08), 0 0 0 1px rgba(255, 93, 104, .08); }
      50% { box-shadow: inset 0 0 42px rgba(255, 57, 74, .18), 0 0 25px rgba(255, 57, 74, .1); }
    }

    button, a { -webkit-tap-highlight-color: transparent; }
    button:focus-visible, a:focus-visible { outline: 2px solid var(--cyan); outline-offset: 3px; }
    a { color: inherit; }

    .shell {
      position: relative;
      z-index: 1;
      width: min(1220px, calc(100% - 32px));
      margin: 0 auto;
      padding: 14px 0 58px;
    }

    .review-strip {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      min-height: 42px;
      padding: 8px 12px;
      border: 1px solid #27545a;
      border-radius: 12px;
      background: rgba(11, 29, 34, .9);
      box-shadow: inset 0 1px rgba(255,255,255,.03), 0 10px 50px rgba(0,0,0,.22);
      font: 700 10px/1.35 var(--mono);
      letter-spacing: .1em;
      text-transform: uppercase;
      color: #90aeb3;
    }
    .review-strip strong { color: var(--cyan-soft); }
    .strip-statuses { display: flex; gap: 8px; }
    .micro-status {
      min-height: 26px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 9px;
      border: 1px solid #2c4b51;
      border-radius: 7px;
      background: #102329;
      color: #bdd1d5;
    }
    .micro-status.good { border-color: #276a4c; color: var(--green); }
    .micro-status.bad { border-color: #76303a; color: var(--red); box-shadow: inset 0 0 16px rgba(255, 57, 74, .1); }

    .masthead {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 28px;
      padding: 28px 14px 22px;
    }
    .brand-lockup {
      position: relative;
      width: min(510px, 100%);
      height: 172px;
      min-width: 0;
      overflow: hidden;
      isolation: isolate;
      -webkit-mask-image: linear-gradient(90deg, transparent 0, #000 4%, #000 92%, transparent 100%);
      mask-image: linear-gradient(90deg, transparent 0, #000 4%, #000 92%, transparent 100%);
    }
    .brand-source {
      position: absolute;
      z-index: -1;
      left: -6px;
      top: -60px;
      width: 864px;
      max-width: none;
      height: 1536px;
      object-fit: cover;
      pointer-events: none;
    }
    .brand-source-label {
      position: absolute;
      right: 16px;
      bottom: 8px;
      padding: 3px 7px;
      border: 1px solid rgba(70, 226, 218, .25);
      border-radius: 999px;
      background: rgba(3, 12, 15, .82);
      color: #6f979b;
      font: 700 8px/1 var(--mono);
      letter-spacing: .08em;
      text-transform: uppercase;
    }

    .runtime-stack { display: grid; grid-template-columns: repeat(3, minmax(106px, 1fr)); align-items: stretch; gap: 10px; }
    .runtime-chip {
      min-height: 82px;
      display: grid;
      grid-template-columns: 38px minmax(0, 1fr);
      place-items: center start;
      gap: 9px;
      padding: 10px;
      border: 1px solid #2c4650;
      border-radius: 12px;
      background: linear-gradient(150deg, rgba(26,46,53,.95), rgba(7,16,20,.95));
      box-shadow: inset 0 1px rgba(255,255,255,.05), 0 10px 30px rgba(0,0,0,.25);
      color: #f2f7f7;
    }
    .runtime-chip.primary { border-color: #337584; box-shadow: inset 0 0 25px rgba(54,240,228,.08), 0 0 18px rgba(54,240,228,.1); }
    .runtime-chip svg { width: 34px; height: 34px; color: #fff; }
    .runtime-chip.openai-chip { grid-template-columns: 1fr; align-content: center; gap: 6px; }
    .runtime-chip svg.openai-wordmark { width: 82px; height: 22px; }
    .runtime-chip svg.codex-mark { width: 38px; height: 38px; border-radius: 10px; }
    .runtime-chip.openai-chip small { margin-top: 0; }
    .runtime-chip .runtime-name { font: 800 13px/1.05 var(--sans); letter-spacing: -.02em; }
    .runtime-chip small { display: block; margin-top: 5px; color: #769198; font: 700 8px/1.25 var(--mono); letter-spacing: .04em; text-transform: uppercase; }
    .marks-note { grid-column: 1 / -1; color: #526a70; font: 700 8px/1.35 var(--mono); text-align: right; }

    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 280px;
      align-items: end;
      gap: 30px;
      min-height: 285px;
      padding: clamp(38px, 7vw, 72px) 16px 30px;
    }
    .eyebrow { color: var(--green); font: 800 11px/1.4 var(--mono); letter-spacing: .12em; text-transform: uppercase; }
    h1 {
      max-width: 880px;
      margin: 14px 0 16px;
      font-size: clamp(44px, 6.2vw, 76px);
      line-height: .98;
      letter-spacing: -.055em;
    }
    .lead { max-width: 760px; margin: 0; color: #a2b5ba; font-size: clamp(15px, 1.7vw, 18px); line-height: 1.65; }
    .hero-proof {
      justify-self: end;
      width: min(100%, 258px);
      padding: 16px;
      border: 1px solid #21515a;
      border-radius: 14px;
      background: linear-gradient(145deg, rgba(10,28,32,.9), rgba(4,11,13,.95));
      box-shadow: inset 0 0 30px rgba(54,240,228,.05);
    }
    .hero-proof .proof-line { display: flex; justify-content: space-between; gap: 12px; padding: 8px 0; border-bottom: 1px solid #18333a; font: 700 10px/1.35 var(--mono); color: #718b91; }
    .hero-proof .proof-line:last-child { border-bottom: 0; }
    .hero-proof strong { color: var(--green); }

    .quick-nav {
      position: sticky;
      top: 8px;
      z-index: 20;
      display: flex;
      align-items: center;
      gap: 4px;
      overflow-x: auto;
      margin: 0 0 16px;
      padding: 7px;
      border: 1px solid #2b6268;
      border-radius: 13px;
      background: rgba(10, 25, 29, .9);
      backdrop-filter: blur(16px);
      box-shadow: 0 12px 40px rgba(0,0,0,.28), inset 0 0 24px rgba(54,240,228,.04);
      scrollbar-width: none;
    }
    .quick-nav::-webkit-scrollbar { display: none; }
    .quick-nav a { flex: 0 0 auto; padding: 8px 11px; border-radius: 8px; color: #c4d6d9; text-decoration: none; font: 700 13px/1 var(--mono); }
    .quick-nav a:hover { color: var(--cyan-soft); background: #10272d; }
    .quick-nav .slash { color: #28646a; font: 700 16px/1 var(--mono); }
    .quick-nav .nav-tools { margin-left: auto; display: flex; gap: 6px; }
    .icon-button { width: 34px; min-height: 34px; padding: 0; border-radius: 8px; background: #13282e; color: #88a6aa; border: 1px solid #28454d; }

    .section-block {
      position: relative;
      margin-top: 18px;
      border: 1px solid #1d454c;
      border-radius: 16px;
      background: linear-gradient(145deg, rgba(9,24,28,.96), rgba(5,14,17,.95));
      box-shadow: inset 0 1px rgba(255,255,255,.025), 0 20px 50px rgba(0,0,0,.24);
    }
    .section-block::before {
      content: "";
      position: absolute;
      left: -11px;
      top: 34px;
      width: 10px;
      height: calc(100% - 68px);
      border-left: 2px solid #226e71;
      border-top: 2px solid #226e71;
      border-bottom: 2px solid #226e71;
      border-radius: 7px 0 0 7px;
      opacity: .8;
    }
    .section-block::after {
      content: "";
      position: absolute;
      left: -16px;
      top: 28px;
      width: 10px;
      height: 10px;
      border: 2px solid var(--cyan);
      border-radius: 50%;
      background: var(--board);
      animation: signal-pulse 3s ease-in-out infinite;
    }

    .control-room { padding: 18px; border-color: #27b9b2; box-shadow: inset 0 0 40px rgba(54,240,228,.04), 0 0 0 1px rgba(54,240,228,.05); }
    .section-head { display: flex; align-items: end; justify-content: space-between; gap: 20px; margin: 0 0 18px; }
    h2 { margin: 5px 0 0; font-size: clamp(24px, 3vw, 34px); line-height: 1.1; letter-spacing: -.035em; }
    h3 { letter-spacing: -.02em; }
    .section-note { max-width: 410px; color: #728a90; font-size: 12px; line-height: 1.55; text-align: right; }

    .flow-board {
      position: relative;
      min-height: 278px;
      margin: 12px 0 16px;
      overflow: hidden;
      border: 1px solid #1e474e;
      border-radius: 13px;
      background:
        radial-gradient(circle at 72% 45%, rgba(54,240,228,.07), transparent 24%),
        linear-gradient(90deg, rgba(255,255,255,.018) 1px, transparent 1px),
        linear-gradient(rgba(255,255,255,.018) 1px, transparent 1px),
        #061316;
      background-size: auto, 20px 20px, 20px 20px, auto;
      box-shadow: inset 0 0 60px rgba(0,0,0,.35);
    }
    .flow-wires { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }
    .bus-base, .bus-progress, .tamper-wire { fill: none; vector-effect: non-scaling-stroke; }
    .bus-base { stroke: #20464d; stroke-width: 8; }
    .bus-base-thin { fill: none; stroke: #315c63; stroke-width: 1.5; stroke-dasharray: 3 8; vector-effect: non-scaling-stroke; }
    .bus-progress { stroke: var(--green); stroke-width: 3; stroke-dasharray: 9 13; filter: drop-shadow(0 0 5px rgba(104,247,154,.8)); animation: trace-flow 3.2s linear infinite; opacity: 0; }
    .tamper-wire { stroke: var(--red); stroke-width: 3; stroke-dasharray: 5 11; filter: drop-shadow(0 0 6px rgba(255,93,104,.75)); animation: trace-flow 2.1s linear infinite reverse; opacity: 0; }
    .flow-via { fill: #061316; stroke: #3a6870; stroke-width: 2; vector-effect: non-scaling-stroke; }
    .flow-packet { fill: var(--cyan); filter: drop-shadow(0 0 7px var(--cyan)); opacity: 0; }
    .flow-board[data-state="running"] .bus-progress,
    .flow-board[data-state="verified"] .bus-progress,
    .flow-board[data-state="failed"] .bus-progress,
    .flow-board[data-state="tamper-failed"] .bus-progress { opacity: 1; }
    .flow-board[data-state="running"] .flow-packet { opacity: 1; }
    .flow-board[data-state="tamper-failed"] .tamper-wire { opacity: 1; }

    .flow-grid {
      position: relative;
      z-index: 2;
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 14px;
      padding: 34px 18px 20px;
    }
    .flow-step {
      position: relative;
      min-width: 0;
      min-height: 128px;
      padding: 13px;
      border: 1px solid #294c54;
      border-radius: 10px;
      background: linear-gradient(155deg, rgba(16,39,44,.97), rgba(7,17,20,.98));
      color: #70878d;
      font-family: var(--mono);
      transition: border-color .2s ease, box-shadow .2s ease, transform .2s ease;
    }
    .flow-step::before {
      content: "";
      position: absolute;
      top: -19px;
      left: calc(50% - 5px);
      width: 10px;
      height: 10px;
      border: 2px solid #345961;
      border-radius: 50%;
      background: #061316;
    }
    .flow-step.complete { border-color: #2c8158; color: #d3f4df; box-shadow: inset 0 0 25px rgba(104,247,154,.055); }
    .flow-step.complete::before { border-color: var(--green); background: var(--green); box-shadow: 0 0 12px rgba(104,247,154,.7); }
    .flow-step.live { border-color: var(--cyan); color: #e1fffc; transform: translateY(-2px); box-shadow: inset 0 0 28px rgba(54,240,228,.09), 0 0 20px rgba(54,240,228,.11); }
    .flow-step.live::before { border-color: var(--cyan); background: var(--cyan); box-shadow: 0 0 14px rgba(54,240,228,.8); animation: signal-pulse 1.2s ease-in-out infinite; }
    .flow-step.warn { border-color: var(--amber); color: #ffe0a5; }
    .flow-step.failed { border-color: var(--red); color: #ffbbc0; background: linear-gradient(145deg, #2d1116, #140c0f); }
    .flow-step.failed::before { border-color: var(--red); background: var(--red); box-shadow: 0 0 14px rgba(255,93,104,.8); }
    .node-top { display: flex; justify-content: space-between; align-items: center; gap: 7px; }
    .node-index { color: #4f9694; font: 800 10px/1 var(--mono); }
    .node-state { color: #5e777c; font: 800 8px/1 var(--mono); letter-spacing: .08em; text-transform: uppercase; }
    .flow-step.complete .node-state { color: var(--green); }
    .flow-step.live .node-state { color: var(--cyan); }
    .flow-step.failed .node-state { color: var(--red); }
    .node-name { margin-top: 14px; color: currentColor; font: 850 11px/1.25 var(--mono); letter-spacing: .035em; text-transform: uppercase; }
    .node-value { min-height: 31px; margin-top: 9px; color: #8ca2a7; font: 700 9px/1.45 var(--mono); overflow-wrap: anywhere; }
    .flow-step.complete .node-value, .flow-step.live .node-value { color: #bad0d3; }
    .flow-context { position: relative; z-index: 2; display: grid; grid-template-columns: 1.3fr 1fr 1fr; gap: 8px; padding: 0 18px 17px; }
    .context-cell { min-width: 0; padding: 8px 10px; border: 1px solid #1d3b41; border-radius: 7px; background: #071619; }
    .context-cell small { display: block; color: #526c72; font: 800 7px/1.2 var(--mono); letter-spacing: .1em; text-transform: uppercase; }
    .context-cell span { display: block; margin-top: 5px; color: #90a7ac; font: 700 9px/1.3 var(--mono); overflow-wrap: anywhere; }
    .tamper-branch {
      position: relative;
      z-index: 2;
      display: none;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 8px;
      margin: 0 18px 17px 48%;
      padding: 10px;
      border: 1px solid #75303a;
      border-radius: 9px;
      background: rgba(43,14,19,.92);
    }
    .flow-board[data-state="tamper-failed"] .tamper-branch { display: grid; }
    .branch-chip { padding: 8px; border: 1px solid #5e2a32; border-radius: 6px; color: #ff8f98; font: 800 8px/1.35 var(--mono); text-transform: uppercase; }
    .branch-chip strong { display: block; margin-top: 4px; color: #ffd0d3; font-size: 9px; }

    .integrity-alert {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 18px;
      min-height: 132px;
      padding: 20px;
      border: 1px solid #31585e;
      border-radius: 12px;
      background: rgba(8,24,27,.88);
    }
    .integrity-alert.failed { border-color: #9c3b45; background: linear-gradient(135deg, rgba(73,20,27,.82), rgba(25,13,18,.94)); animation: danger-pulse 2.8s ease-in-out infinite; }
    .integrity-alert.verified { border-color: #2a7251; background: linear-gradient(135deg, rgba(13,54,38,.65), rgba(7,25,21,.95)); }
    .alert-kicker { color: #839da2; font: 800 10px/1.3 var(--mono); letter-spacing: .12em; text-transform: uppercase; }
    .alert-title { margin: 8px 0 6px; font: 850 clamp(27px, 4vw, 43px)/1 var(--mono); letter-spacing: .02em; }
    .integrity-alert.failed .alert-title { color: var(--red); text-shadow: 0 0 20px rgba(255,93,104,.25); }
    .integrity-alert.verified .alert-title { color: var(--green); }
    .alert-copy { color: #91a4a8; font-size: 12px; line-height: 1.5; }
    .alert-metrics { display: grid; grid-template-columns: repeat(3, 108px); gap: 8px; }
    .alert-metric { min-height: 66px; padding: 10px; border: 1px solid #3a4b50; border-radius: 7px; background: rgba(255,255,255,.035); font: 800 10px/1.35 var(--mono); color: #c5d2d4; }
    .alert-metric small { display: block; margin-bottom: 8px; color: #70868b; font-size: 8px; letter-spacing: .08em; }

    .stats {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      overflow: hidden;
      margin-top: 12px;
      border: 1px solid #1b3c43;
      border-radius: 14px;
      background: rgba(6,16,19,.92);
    }
    .stat { min-height: 98px; padding: 17px; border-right: 1px solid #1b3c43; }
    .stat:last-child { border: 0; }
    .stat-label { color: #6c858b; font: 800 10px/1.3 var(--mono); letter-spacing: .1em; text-transform: uppercase; }
    .stat-label::before { content: ""; display: inline-block; width: 7px; height: 7px; margin-right: 8px; border-radius: 50%; background: var(--green); box-shadow: 0 0 10px rgba(104,247,154,.7); }
    .stat-value { margin-top: 14px; font: 700 clamp(19px, 2.6vw, 29px)/1.15 var(--mono); letter-spacing: -.04em; overflow-wrap: anywhere; }

    .content-section { position: relative; margin-top: 34px; padding-left: 1px; }
    .content-section::before { content: ""; position: absolute; left: -10px; top: 9px; bottom: -31px; width: 1px; background: linear-gradient(var(--cyan), #16464c 55%, transparent); }
    .content-section::after { content: ""; position: absolute; left: -14px; top: 6px; width: 7px; height: 7px; border: 1px solid var(--cyan); border-radius: 50%; background: var(--board); box-shadow: 0 0 9px var(--cyan); }
    .content-section > .section-head { padding: 0 8px; }

    .missions { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .card {
      position: relative;
      padding: 19px;
      border: 1px solid #2a5259;
      border-radius: 12px;
      background: linear-gradient(145deg, rgba(11,28,32,.96), rgba(7,17,20,.96));
      box-shadow: inset 0 0 32px rgba(54,240,228,.025);
    }
    .card::before { content: ""; position: absolute; inset: 8px auto 8px -1px; width: 2px; background: linear-gradient(transparent, var(--cyan), transparent); opacity: .7; }
    .card-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
    .card h3 { margin: 6px 0 7px; font-size: 20px; }
    .path, code { color: #738b91; font: 11px/1.5 var(--mono); overflow-wrap: anywhere; }
    .badge { display: inline-flex; align-items: center; min-height: 25px; padding: 4px 8px; border: 1px solid #315058; border-radius: 999px; color: #b4c5c8; background: #102126; font: 800 9px/1 var(--mono); letter-spacing: .05em; white-space: nowrap; text-transform: uppercase; }
    .badge.ok { border-color: #246443; background: #0c281a; color: var(--green); }
    .badge.warn { border-color: #6a4d21; background: #281b0b; color: var(--amber); }
    .badge.bad { border-color: #77313a; background: #2c1117; color: var(--red); }
    .meta { display: grid; grid-template-columns: repeat(3, 1fr); gap: 7px; margin: 17px 0; }
    .meta div { min-width: 0; padding: 9px; border: 1px solid #1e3940; border-radius: 7px; background: #0a1a1e; }
    .meta span { display: block; }
    .meta .k { color: #647b80; font: 800 8px/1.3 var(--mono); letter-spacing: .08em; text-transform: uppercase; }
    .meta .v { margin-top: 6px; color: #c5d3d5; font: 700 11px/1.3 var(--mono); overflow-wrap: anywhere; }
    .actions { display: flex; align-items: center; flex-wrap: wrap; gap: 9px; }
    button {
      min-height: 42px;
      padding: 0 14px;
      border: 1px solid #47f5e7;
      border-radius: 7px;
      background: linear-gradient(180deg, #42eee4, #14c7c3);
      color: #021012;
      box-shadow: 0 0 16px rgba(54,240,228,.16);
      font: 850 11px/1 var(--mono);
      text-transform: uppercase;
      cursor: pointer;
    }
    button:hover { filter: brightness(1.08); transform: translateY(-1px); }
    button:disabled { cursor: not-allowed; opacity: .38; transform: none; }
    .hash { margin-left: auto; color: #60787e; font: 10px/1.35 var(--mono); overflow-wrap: anywhere; }
    .verify { min-height: 34px; padding: 0 10px; border-color: #31535b; background: #10242a; color: #b5c9cd; box-shadow: none; }
    .tamper { border-color: #8b3640; background: #2b1116; color: var(--red); box-shadow: inset 0 0 18px rgba(255,93,104,.08); }

    .proof-console { overflow: hidden; border: 1px solid #24464d; border-radius: 13px; background: #071417; }
    .run { display: grid; grid-template-columns: minmax(0,1.5fr) .72fr .72fr .7fr auto; align-items: center; gap: 12px; min-height: 72px; padding: 14px 16px; border-bottom: 1px solid #1c363c; }
    .run:last-child { border: 0; }
    .run-title { font-weight: 760; }
    .run-sub { margin-top: 4px; color: #6b8288; font: 10px/1.4 var(--mono); }
    .run a, .tamper-actions a { color: var(--cyan-soft); font: 800 11px/1.4 var(--mono); text-decoration: none; }
    .run a:hover, .tamper-actions a:hover { text-decoration: underline; }
    .empty, .skeleton { min-height: 130px; display: grid; place-items: center; padding: 28px; color: #6b8388; text-align: center; font: 700 11px/1.5 var(--mono); }

    .evidence { display: none; margin-top: 14px; }
    .evidence.show { display: block; }
    .evidence-grid { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 9px; margin: 15px 0; }
    .evidence-tile { min-width: 0; padding: 12px; border: 1px solid #24454c; border-radius: 8px; background: #08181c; }
    .evidence-tile .k { color: #657e84; font: 800 8px/1.3 var(--mono); letter-spacing: .08em; text-transform: uppercase; }
    .evidence-tile .v { margin-top: 8px; color: #bcd0d3; font: 700 10px/1.45 var(--mono); overflow-wrap: anywhere; }
    .evidence h3 { margin: 22px 0 7px; color: #c7d8db; font-size: 14px; }
    .evidence-list { margin: 0; padding: 0; list-style: none; border-top: 1px solid #1b363c; }
    .evidence-list li { display: grid; grid-template-columns: 1.1fr .9fr; gap: 12px; padding: 10px 4px; border-bottom: 1px solid #1b363c; color: #95a9ad; font-size: 11px; overflow-wrap: anywhere; }
    .evidence-list .ok { color: var(--green); font-family: var(--mono); }
    .evidence-list .bad { color: var(--red); font-family: var(--mono); }
    .tamper-lab { margin-top: 18px; padding: 14px; border: 1px solid #4d2930; border-radius: 9px; background: #160d10; }
    .tamper-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; margin-top: 10px; }

    .command-dock {
      display: grid;
      grid-template-columns: 190px minmax(0, 1fr) 170px;
      align-items: center;
      gap: 12px;
      margin-top: 20px;
      padding: 10px;
      border: 1px solid #406d83;
      border-radius: 13px;
      background: linear-gradient(180deg, #20324a, #15283d);
      box-shadow: inset 0 0 25px rgba(117,169,255,.1), 0 0 22px rgba(54,240,228,.08);
      font: 750 10px/1.35 var(--mono);
      color: #a9bdcb;
    }
    .dock-brand { color: #d0e2e5; }
    .dock-command { min-width: 0; padding: 9px 12px; border: 1px solid #506c8d; border-radius: 7px; background: rgba(184,213,255,.13); color: #7af4d9; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .dock-power { text-align: right; color: #aabdc7; }

    .toast { position: fixed; right: 20px; bottom: 20px; z-index: 50; width: min(430px, calc(100% - 40px)); padding: 14px 16px; border: 1px solid #37d9d0; border-radius: 10px; background: #0c2529; color: #d9f9f6; box-shadow: 0 18px 70px #000b, 0 0 25px rgba(54,240,228,.12); font: 700 11px/1.5 var(--mono); opacity: 0; visibility: hidden; pointer-events: none; transform: translateY(150%); transition: transform .22s ease, opacity .18s ease, visibility 0s linear .22s; }
    .toast.show { opacity: 1; visibility: visible; transform: translateY(0); transition-delay: 0s; }
    .toast.error { border-color: #a93d48; background: #321219; color: #ffd0d3; }
    footer { margin-top: 15px; padding: 4px 8px; color: #526a70; font: 700 9px/1.65 var(--mono); }

    @media (max-width: 900px) {
      .masthead { grid-template-columns: 1fr; }
      .runtime-stack { grid-template-columns: repeat(3, minmax(0, 1fr)); }
      .hero { grid-template-columns: 1fr; }
      .hero-proof { justify-self: start; width: 100%; max-width: 620px; }
      .flow-board { min-height: 0; }
      .flow-wires { display: none; }
      .flow-grid { grid-template-columns: 1fr; gap: 9px; padding: 18px; }
      .flow-step { min-height: 78px; margin-left: 19px; }
      .flow-step::before { top: 22px; left: -26px; }
      .flow-step:not(:last-child)::after { content: ""; position: absolute; top: 34px; left: -22px; width: 2px; height: calc(100% + 12px); background: #26525a; }
      .flow-context { grid-template-columns: 1fr; }
      .tamper-branch { margin: 0 18px 17px; }
      .integrity-alert { grid-template-columns: 1fr; }
      .alert-metrics { grid-template-columns: repeat(3, 1fr); }
      .missions { grid-template-columns: 1fr; }
      .run { grid-template-columns: 1fr auto; }
      .run > :not(:first-child):not(:last-child) { display: none; }
      .command-dock { grid-template-columns: 1fr; }
      .dock-power { text-align: left; }
    }

    @media (max-width: 640px) {
      .shell { width: min(100% - 18px, 1220px); padding-top: 8px; }
      .review-strip { align-items: flex-start; }
      .review-strip > span { max-width: 170px; }
      .strip-statuses .micro-status:nth-child(2) { display: none; }
      .masthead { padding: 22px 5px 14px; }
      .brand-lockup { width: 100%; height: 128px; }
      .brand-source { width: 648px; height: 1152px; left: -5px; top: -44px; }
      .brand-source-label { display: none; }
      .runtime-stack { grid-template-columns: 1fr; }
      .runtime-chip { min-height: 64px; }
      .marks-note { text-align: left; }
      .hero { min-height: 0; padding: 35px 6px 22px; }
      h1 { font-size: clamp(40px, 12vw, 58px); }
      .quick-nav { top: 4px; }
      .quick-nav .nav-tools { display: none; }
      .control-room, .card { padding: 14px; }
      .section-note { display: none; }
      .stats { grid-template-columns: repeat(2, 1fr); }
      .stat:nth-child(2) { border-right: 0; }
      .stat:nth-child(-n+2) { border-bottom: 1px solid #1b3c43; }
      .meta { grid-template-columns: 1fr; }
      .alert-metrics { grid-template-columns: 1fr; }
      .alert-metric { min-height: 0; }
      .tamper-branch { grid-template-columns: repeat(2, 1fr); }
      .evidence-grid { grid-template-columns: 1fr; }
      .evidence-list li { grid-template-columns: 1fr; }
      .hash { width: 100%; margin-left: 0; }
      .section-block::before, .section-block::after, .content-section::before, .content-section::after { display: none; }
      .board-traces { opacity: .2; }
    }

    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { animation: none !important; transition: none !important; }
    }
  </style>
</head>
<body>
  <svg width="0" height="0" aria-hidden="true" style="position:absolute">
    <symbol id="openai-wordmark" viewBox="0 0 288 78">
      <path fill="currentColor" d="M30.6.398C13.77.398 0 14.168 0 30.998s13.77 30.6 30.6 30.6 30.6-13.685 30.6-30.6S47.515.398 30.6.398m0 50.235c-10.455 0-18.87-8.585-18.87-19.635s8.415-19.635 18.87-19.635 18.87 8.585 18.87 19.635-8.415 19.635-18.87 19.635m61.54-33.235c-5.526 0-10.88 2.21-13.686 5.95v-5.1h-11.05v59.5h11.05V56.243c2.805 3.485 7.99 5.355 13.685 5.355 11.9 0 21.25-9.35 21.25-22.1s-9.35-22.1-21.25-22.1m-1.87 34.595c-6.29 0-11.9-4.93-11.9-12.495s5.61-12.495 11.9-12.495 11.899 4.93 11.899 12.495-5.61 12.495-11.9 12.495m49.133-34.595c-12.07 0-21.59 9.435-21.59 22.1s8.33 22.1 21.93 22.1c11.135 0 18.275-6.715 20.485-14.28h-10.795c-1.36 3.145-5.185 5.355-9.775 5.355-5.695 0-10.03-3.995-11.05-9.69h32.13v-4.335c0-11.56-8.075-21.25-21.335-21.25m-10.71 17.765c1.19-5.355 5.61-8.84 10.965-8.84 5.695 0 10.03 3.74 10.54 8.84zm61.454-17.765c-4.93 0-10.115 2.21-12.495 5.865v-5.015H166.6v42.5h11.05V37.883c0-6.63 3.57-10.965 9.35-10.965 5.355 0 8.245 4.08 8.245 9.775v24.055h11.05v-25.84c0-10.54-6.46-17.51-16.15-17.51M234.596 1.25l-24.055 59.5h11.815l5.1-13.005h27.37l5.1 13.005h11.985l-23.885-59.5zm-3.315 36.635 9.86-24.905 9.775 24.905zM287.636 1.25h-11.22v59.5h11.22z"/>
    </symbol>
    <symbol id="codex-app-mark" viewBox="0 0 192 192">
      <image width="192" height="192" href="data:image/webp;base64,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"/>
    </symbol>
    <symbol id="openai-blossom" viewBox="146 227 268 265">
      <path fill="currentColor" d="M249.176 323.434V298.276C249.176 296.158 249.971 294.569 251.825 293.509L302.406 264.381C309.29 260.409 317.5 258.555 325.973 258.555C357.75 258.555 377.877 283.185 377.877 309.399C377.877 311.253 377.877 313.371 377.611 315.49L325.178 284.771C322.001 282.919 318.822 282.919 315.645 284.771L249.176 323.434ZM367.283 421.415V361.301C367.283 357.592 365.694 354.945 362.516 353.092L296.048 314.43L317.763 301.982C319.617 300.925 321.206 300.925 323.058 301.982L373.639 331.112C388.205 339.586 398.003 357.592 398.003 375.069C398.003 395.195 386.087 413.733 367.283 421.412V421.415ZM233.553 368.452L211.838 355.742C209.986 354.684 209.19 353.095 209.19 350.975V292.718C209.19 264.383 230.905 242.932 260.301 242.932C271.423 242.932 281.748 246.641 290.49 253.26L238.321 283.449C235.146 285.303 233.555 287.951 233.555 291.659V368.455L233.553 368.452ZM280.292 395.462L249.176 377.985V340.913L280.292 323.436L311.407 340.913V377.985L280.292 395.462ZM300.286 475.968C289.163 475.968 278.837 472.259 270.097 465.64L322.264 435.449C325.441 433.597 327.03 430.949 327.03 427.239V350.445L349.011 363.155C350.865 364.213 351.66 365.802 351.66 367.922V426.179C351.66 454.514 329.679 475.965 300.286 475.965V475.968ZM237.525 416.915L186.944 387.785C172.378 379.31 162.582 361.305 162.582 343.827C162.582 323.436 174.763 305.164 193.563 297.485V357.861C193.563 361.571 195.154 364.217 198.33 366.071L264.535 404.467L242.82 416.915C240.967 417.972 239.377 417.972 237.525 416.915ZM234.614 460.343C204.689 460.343 182.71 437.833 182.71 410.028C182.71 407.91 182.976 405.792 183.238 403.672L235.405 433.863C238.582 435.715 241.763 435.715 244.938 433.863L311.407 395.466V420.622C311.407 422.742 310.612 424.331 308.758 425.389L258.179 454.519C251.293 458.491 243.083 460.343 234.611 460.343H234.614ZM300.286 491.854C332.329 491.854 359.073 469.082 365.167 438.892C394.825 431.211 413.892 403.406 413.892 375.073C413.892 356.535 405.948 338.529 391.648 325.552C392.972 319.991 393.766 314.43 393.766 308.87C393.766 271.003 363.048 242.666 327.562 242.666C320.413 242.666 313.528 243.723 306.644 246.109C294.725 234.457 278.307 227.042 260.301 227.042C228.258 227.042 201.513 249.815 195.42 280.004C165.761 287.685 146.694 315.49 146.694 343.824C146.694 362.362 154.638 380.368 168.938 393.344C167.613 398.906 166.819 404.467 166.819 410.027C166.819 447.894 197.538 476.231 233.024 476.231C240.172 476.231 247.058 475.173 253.943 472.788C265.859 484.441 282.278 491.854 300.286 491.854Z"/>
    </symbol>
  </svg>
  <svg class="board-traces" viewBox="0 0 1440 2400" preserveAspectRatio="xMidYMid slice" aria-hidden="true">
    <path class="trace" d="M0 180H160Q190 180 190 210V420Q190 450 220 450H390"/>
    <path class="trace hot" d="M0 220H120Q150 220 150 250V650Q150 680 180 680H390"/>
    <path class="trace" d="M1440 150H1270Q1240 150 1240 180V390Q1240 420 1210 420H1040"/>
    <path class="trace hot" d="M1440 580H1320Q1290 580 1290 610V940Q1290 970 1260 970H1110"/>
    <path class="trace" d="M0 1090H120Q150 1090 150 1120V1490Q150 1520 180 1520H330"/>
    <path class="trace fail" d="M1440 1260H1330Q1300 1260 1300 1290V1680Q1300 1710 1270 1710H1120"/>
    <path class="trace" d="M0 1960H230Q260 1960 260 1930V1840Q260 1810 290 1810H410"/>
    <path class="trace hot" d="M1440 2150H1190Q1160 2150 1160 2120V2020Q1160 1990 1130 1990H980"/>
    <circle class="via" cx="390" cy="450" r="6"/><circle class="via" cx="390" cy="680" r="6"/>
    <circle class="via" cx="1040" cy="420" r="6"/><circle class="via" cx="1110" cy="970" r="6"/>
    <circle class="via" cx="330" cy="1520" r="6"/><circle class="via" cx="1120" cy="1710" r="6"/>
  </svg>

  <div class="shell">
    <div class="review-strip">
      <span><strong>APR Mission Control</strong> · runtime-backed evidence interface</span>
      <div class="strip-statuses">
        <span class="micro-status" id="ready-status">Checking</span>
        <span class="micro-status good" id="verified-status">Verifier</span>
        <span class="micro-status" id="integrity-status">Integrity monitor</span>
      </div>
    </div>

    <header class="masthead">
      <div class="brand-lockup">
        <img class="brand-source" src="__OSA_BRAND_DATA__" width="864" height="1536" alt="OsaTechGPT · Proof Systems · Mission Control">
        <span class="brand-source-label">approved OsaTechGPT lockup</span>
      </div>
      <div class="runtime-stack" aria-label="Runtime providers">
        <div class="runtime-chip openai-chip"><svg class="openai-wordmark" role="img" aria-label="OpenAI"><use href="#openai-wordmark"></use></svg><small>official wordmark · provider</small></div>
        <div class="runtime-chip"><svg aria-hidden="true"><use href="#openai-blossom"></use></svg><div><div class="runtime-name">ChatGPT</div><small>official mark · operator</small></div></div>
        <div class="runtime-chip primary"><svg class="codex-mark" role="img" aria-label="Codex"><use href="#codex-app-mark"></use></svg><div><div class="runtime-name">Codex</div><small>official app mark · build runtime</small></div></div>
        <div class="marks-note">OpenAI, ChatGPT and Codex marks belong to OpenAI · APR <span id="runtime-version">v—</span></div>
      </div>
    </header>

    <main>
      <section class="hero">
        <div>
          <div class="eyebrow">Agent sandbox · verifiable execution</div>
          <h1>Run autonomous work. Verify what actually happened.</h1>
          <p class="lead">Execute an approved mission, inspect deterministic acceptance evidence, and let an independent verifier detect changes to artifacts, events, or critical metadata.</p>
        </div>
        <aside class="hero-proof" aria-label="Trust boundary">
          <div class="proof-line"><span>EXECUTION</span><strong>CONTROLLED</strong></div>
          <div class="proof-line"><span>PROOF</span><strong>LOCAL_VERIFIED</strong></div>
          <div class="proof-line"><span>ANCHOR</span><strong>UNANCHORED</strong></div>
        </aside>
      </section>

      <nav class="quick-nav" aria-label="Mission Control sections">
        <a href="#missions-section">Missions</a><span class="slash">/</span>
        <a href="#runs-section">Runs</a><span class="slash">/</span>
        <a href="#control-room">Control Room</a><span class="slash">/</span>
        <a href="#evidence">Latest Proof</a>
        <div class="nav-tools"><button class="icon-button" type="button" data-refresh aria-label="Refresh evidence">↻</button></div>
      </nav>

      <section class="control-room section-block" id="control-room">
        <div class="section-head">
          <div><div class="eyebrow">Live execution narrative</div><h2>Evidence Control Room</h2></div>
          <div class="section-note">The interface visualizes state. Proof Bundle data and independent verification remain the source of truth.</div>
        </div>
        <div class="flow-board" id="flow-board" data-state="idle" aria-label="Backend-driven proof flow">
          <svg class="flow-wires" viewBox="0 0 1000 278" preserveAspectRatio="none" aria-hidden="true">
            <path class="bus-base" d="M108 52V72H892V52"/>
            <path class="bus-base-thin" d="M108 72H892"/>
            <path class="bus-progress" d="M108 72H892"/>
            <path class="tamper-wire" d="M696 72V216H962"/>
            <circle class="flow-via" cx="108" cy="72" r="6"/><circle class="flow-via" cx="304" cy="72" r="6"/>
            <circle class="flow-via" cx="500" cy="72" r="6"/><circle class="flow-via" cx="696" cy="72" r="6"/>
            <circle class="flow-via" cx="892" cy="72" r="6"/><circle class="flow-via" cx="696" cy="216" r="6"/>
            <circle class="flow-packet" r="6"><animateMotion dur="2.4s" repeatCount="indefinite" path="M108 72H892"/></circle>
          </svg>
          <div class="flow-grid" id="flow-grid">
            <div class="flow-step" data-stage="ready"><div class="node-top"><span class="node-index">01</span><span class="node-state">waiting</span></div><div class="node-name">Mission manifest</div><div class="node-value" id="flow-ready-value">Checked-in manifest only</div></div>
            <div class="flow-step" data-stage="executing"><div class="node-top"><span class="node-index">02</span><span class="node-state">waiting</span></div><div class="node-name">Controlled execution</div><div class="node-value" id="flow-executing-value">Provider and backend pending</div></div>
            <div class="flow-step" data-stage="acceptance"><div class="node-top"><span class="node-index">03</span><span class="node-state">waiting</span></div><div class="node-name">Acceptance replay</div><div class="node-value" id="flow-acceptance-value">Deterministic checks pending</div></div>
            <div class="flow-step" data-stage="proof"><div class="node-top"><span class="node-index">04</span><span class="node-state">waiting</span></div><div class="node-name">Proof Bundle</div><div class="node-value" id="flow-proof-value">Hashes and Merkle root pending</div></div>
            <div class="flow-step" data-stage="verified"><div class="node-top"><span class="node-index">05</span><span class="node-state">waiting</span></div><div class="node-name">Independent verifier</div><div class="node-value" id="flow-verified-value">No verified bundle selected</div></div>
          </div>
          <div class="flow-context">
            <div class="context-cell"><small>Mission / source</small><span id="flow-source">No mission selected</span></div>
            <div class="context-cell"><small>Run / execution</small><span id="flow-run">No run selected</span></div>
            <div class="context-cell"><small>Cryptographic output</small><span id="flow-hash">No bundle hash</span></div>
          </div>
          <div class="tamper-branch" id="tamper-branch" aria-label="Disposable tamper copy flow">
            <div class="branch-chip">01 · Copy<strong>Disposable</strong></div>
            <div class="branch-chip">02 · Mutation<strong id="branch-case">Artifact</strong></div>
            <div class="branch-chip">03 · Verifier<strong>Recomputed</strong></div>
            <div class="branch-chip">04 · Result<strong id="branch-result">Failed</strong></div>
          </div>
        </div>
        <div class="integrity-alert" id="integrity-alert" aria-live="polite">
          <div>
            <div class="alert-kicker" id="alert-kicker">Integrity monitor</div>
            <div class="alert-title" id="alert-title">AWAITING EVIDENCE</div>
            <div class="alert-copy" id="alert-copy">Run an approved mission or inspect an existing Proof Bundle.</div>
          </div>
          <div class="alert-metrics">
            <div class="alert-metric"><small>CASE</small><span id="alert-case">NONE</span></div>
            <div class="alert-metric"><small>COPY</small><span id="alert-copy-status">—</span></div>
            <div class="alert-metric"><small>ORIGINAL</small><span id="alert-original">—</span></div>
          </div>
        </div>
      </section>

      <section class="stats" aria-label="System status">
        <div class="stat"><div class="stat-label">Missions</div><div class="stat-value" id="mission-count">—</div></div>
        <div class="stat"><div class="stat-label">Runs</div><div class="stat-value" id="run-count">—</div></div>
        <div class="stat"><div class="stat-label">gVisor</div><div class="stat-value" id="gvisor-status">—</div></div>
        <div class="stat"><div class="stat-label">Latest proof</div><div class="stat-value" id="proof-status">—</div></div>
      </section>

      <section class="content-section" id="missions-section">
        <div class="section-head"><div><div class="eyebrow">01 / Start</div><h2>Approved missions</h2></div><div class="section-note">Checked-in manifests only. No arbitrary commands or filesystem paths.</div></div>
        <div class="missions" id="missions"><div class="card skeleton">Loading manifests…</div></div>
      </section>

      <section class="content-section" id="runs-section">
        <div class="section-head"><div><div class="eyebrow">02 / Evidence</div><h2>Proof history</h2></div><div class="section-note">Newest evidence first</div></div>
        <div class="proof-console" id="runs"><div class="skeleton">Loading evidence…</div></div>
        <section class="card evidence" id="evidence"></section>
      </section>

      <div class="command-dock">
        <div class="dock-brand"><svg aria-hidden="true" viewBox="0 0 192 192" style="width:22px;height:22px;border-radius:6px;vertical-align:middle;margin-right:8px"><use href="#codex-app-mark"></use></svg>CODEX LABS</div>
        <div class="dock-command">osa@apr-mission-control:~$ verify --manifest-only</div>
        <div class="dock-power">OPENAI · CHATGPT · CODEX</div>
      </div>
    </main>

    <footer>The UI is a view of evidence, never the source of truth. LOCAL_VERIFIED proves internal consistency; UNANCHORED means no external trust authority has vouched for the bundle.</footer>
  </div>
  <div class="toast" id="toast" role="status" aria-live="polite"></div>

  <script>
    const token = __APR_CSRF_TOKEN__;
    const $ = (selector) => document.querySelector(selector);
    const esc = (value) => String(value ?? '').replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
    let busy = false;
    let selectedRun = null;

    function toast(message, error = false) {
      const node = $('#toast');
      node.textContent = message;
      node.className = 'toast show' + (error ? ' error' : '');
      window.setTimeout(() => node.className = 'toast', 4200);
    }

    async function api(path, options = {}) {
      const response = await fetch(path, options);
      const body = await response.json();
      if (!response.ok || !body.ok) throw new Error(body.error || `HTTP ${response.status}`);
      return body;
    }

    const flowStages = () => [...document.querySelectorAll('[data-stage]')];
    const shortHash = (value, length = 28) => value ? `${String(value).slice(0, length)}${String(value).length > length ? '…' : ''}` : 'not recorded';

    function setNodeState(node, state, label) {
      node.className = `flow-step ${state || ''}`.trim();
      node.querySelector('.node-state').textContent = label;
    }

    function setFlow(state, context = {}) {
      const board = $('#flow-board');
      const stages = flowStages();
      board.dataset.state = state;
      stages.forEach(stage => setNodeState(stage, '', 'waiting'));

      if (state === 'ready' || state === 'idle') {
        setNodeState(stages[0], state === 'ready' ? 'complete' : 'live', state === 'ready' ? 'available' : 'waiting');
      } else if (state === 'running') {
        setNodeState(stages[0], 'complete', 'validated');
        setNodeState(stages[1], 'live', 'executing');
      } else if (state === 'failed') {
        stages.slice(0, 4).forEach(stage => setNodeState(stage, 'complete', 'recorded'));
        setNodeState(stages[4], 'failed', 'failed');
      } else if (state === 'verified' || state === 'tamper-failed') {
        stages.forEach(stage => setNodeState(stage, 'complete', 'verified'));
      }

      if (context.source) $('#flow-source').textContent = context.source;
      if (context.run) $('#flow-run').textContent = context.run;
      if (context.hash) $('#flow-hash').textContent = context.hash;
    }

    function applyEvidenceFlow(detail) {
      const evidence = detail.evidence || {};
      const run = detail.summary || {};
      const provider = evidence.provider || {};
      const acceptance = evidence.acceptance || evidence.validation || {checks: []};
      const checks = acceptance.checks || [];
      const passed = checks.filter(check => check.passed).length;
      const artifacts = evidence.artifacts || [];
      const events = evidence.events || [];
      const integrity = evidence.integrity || {};
      const verified = run.proof_status === 'LOCAL_VERIFIED';

      setFlow(verified ? 'verified' : 'failed', {
        source: `${run.mission_id || 'mission'} · checked-in manifest`,
        run: `${run.run_id || 'run'} · ${run.backend || 'backend'}`,
        hash: `bundle ${shortHash(integrity.bundle_hash)}`,
      });
      $('#flow-ready-value').textContent = `${run.mission_id || 'mission'} · manifest accepted`;
      $('#flow-executing-value').textContent = `${provider.provider || run.provider || 'provider'} · ${provider.resolved_model || run.backend || 'runtime'}`;
      $('#flow-acceptance-value').textContent = `${passed}/${checks.length} deterministic checks · ${run.mission_status || 'recorded'}`;
      $('#flow-proof-value').textContent = `${artifacts.length} artifacts · ${events.length} chained events · ${shortHash(integrity.event_merkle_root, 15)}`;
      $('#flow-verified-value').textContent = `${run.proof_status || 'UNKNOWN'} · ${run.anchor_status || 'UNANCHORED'}`;
      if (checks.length && passed !== checks.length) {
        const acceptanceNode = document.querySelector('[data-stage="acceptance"]');
        setNodeState(acceptanceNode, 'warn', `${passed}/${checks.length} passed`);
      }
    }

    function setIntegrityFromRun(run) {
      const panel = $('#integrity-alert');
      panel.className = 'integrity-alert';
      if (!run) {
        setFlow('ready');
        $('#alert-kicker').textContent = 'Integrity monitor';
        $('#alert-title').textContent = 'AWAITING EVIDENCE';
        $('#alert-copy').textContent = 'Run an approved mission or inspect an existing Proof Bundle.';
        $('#alert-case').textContent = 'NONE';
        $('#alert-copy-status').textContent = '—';
        $('#alert-original').textContent = '—';
        return;
      }
      const verified = run.proof_status === 'LOCAL_VERIFIED';
      panel.classList.add(verified ? 'verified' : 'failed');
      setFlow(verified ? 'verified' : 'failed', {
        source: run.mission_id || 'recorded mission',
        run: run.run_id || 'recorded run',
      });
      $('#alert-kicker').textContent = verified ? 'Independent verifier' : 'Integrity anomaly detected';
      $('#alert-title').textContent = verified ? 'LOCAL_VERIFIED' : 'INTEGRITY FAILED';
      $('#alert-copy').textContent = verified
        ? 'Artifacts, events, acceptance evidence, Merkle root and bundle hash are internally consistent.'
        : (run.errors?.[0] || 'Independent verification detected inconsistent evidence.');
      $('#alert-case').textContent = verified ? 'BASELINE' : 'EVIDENCE';
      $('#alert-copy-status').textContent = verified ? 'VERIFIED' : 'FAILED';
      $('#alert-original').textContent = verified ? 'PRESERVED' : 'INSPECT';
    }

    function setTamperResult(result) {
      const panel = $('#integrity-alert');
      panel.className = 'integrity-alert failed';
      setFlow('tamper-failed');
      $('#alert-kicker').textContent = 'Tamper Lab · mutation detected';
      $('#alert-title').textContent = 'INTEGRITY FAILED';
      $('#alert-copy').textContent = result.errors?.[0] || 'The disposable copy no longer matches its recorded evidence.';
      $('#alert-case').textContent = String(result.case || 'UNKNOWN').toUpperCase();
      $('#alert-copy-status').textContent = result.status || 'FAILED';
      $('#alert-original').textContent = result.original_preserved ? 'PRESERVED' : 'CHANGED';
      $('#branch-case').textContent = String(result.case || 'unknown').toUpperCase();
      $('#branch-result').textContent = result.status || 'FAILED';
      $('#integrity-status').textContent = 'Integrity failed';
      $('#integrity-status').className = 'micro-status bad';
      panel.scrollIntoView({behavior: 'smooth', block: 'center'});
    }

    function missionCard(mission, gvisorReady, openaiConfigured) {
      if (!mission.valid) return `<article class="card"><div class="card-top"><div><div class="path">${esc(mission.path)}</div><h3>Invalid manifest</h3></div><span class="badge bad">INVALID</span></div><p class="path">${esc(mission.errors.join(' · '))}</p></article>`;
      const needsKey = mission.provider === 'openai' && !openaiConfigured;
      const blocked = (mission.backend === 'gvisor' && !gvisorReady) || needsKey;
      const security = mission.backend === 'gvisor' ? 'sandboxed' : (mission.provider === 'fixture' ? 'fixture · offline' : 'development only');
      const blockedLabel = needsKey ? 'OPENAI KEY ABSENT' : 'RUNSC UNAVAILABLE';
      return `<article class="card"><div class="card-top"><div><div class="path">${esc(mission.path)}</div><h3>${esc(mission.title || mission.mission_id)}</h3><div class="path">${esc(mission.mission_id)} · ${esc(mission.model || 'no model')}</div></div><span class="badge ${blocked ? 'warn' : 'ok'}">${esc(security)}</span></div><div class="meta"><div><span class="k">Provider</span><span class="v">${esc(mission.provider)}</span></div><div><span class="k">Network</span><span class="v">${esc(mission.network_mode)}</span></div><div><span class="k">Limit</span><span class="v">${esc(mission.timeout_seconds)} s</span></div></div><div class="actions"><button data-run="${esc(mission.path)}" ${blocked || busy ? 'disabled' : ''}>${blocked ? blockedLabel : 'Run verified demo'}</button><span class="hash">${esc(mission.spec_hash.slice(0, 22))}…</span></div></article>`;
    }

    function runRow(run) {
      const proofClass = run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad';
      const report = run.report_url ? `<a href="${esc(run.report_url)}" target="_blank" rel="noopener">Report ↗</a>` : '<span class="path">no report</span>';
      return `<article class="run"><div><div class="run-title">${esc(run.mission_id)}</div><div class="run-sub">${esc(run.started_at || run.run_id)} · ${esc(run.provider)} · ${esc(run.backend)}</div></div><span class="badge ${proofClass}">${esc(run.proof_status)}</span><span class="badge ${run.mission_status === 'PASSED' ? 'ok' : 'bad'}">${esc(run.mission_status)}</span><span class="badge warn">${esc(run.anchor_status)}</span><div class="actions">${report}<button class="verify" data-detail="${esc(run.run_id)}">Evidence</button><button class="verify" data-verify="${esc(run.run_id)}">Reverify</button></div></article>`;
    }

    function evidenceView(detail) {
      const evidence = detail.evidence;
      const run = detail.summary;
      const integrity = evidence.integrity || {};
      const provider = evidence.provider || {provider:'sandbox', resolved_model:'n/a', implementation_status:'legacy sandbox'};
      const acceptance = evidence.acceptance || evidence.validation || {checks:[]};
      const artifacts = (evidence.artifacts || []).map(artifact => `<li><span>${esc(artifact.path)} · ${esc(artifact.size)} B</span><code>${esc(artifact.sha256)}</code></li>`).join('') || '<li>No artifacts</li>';
      const checks = (acceptance.checks || []).map(check => `<li><span>${esc(check.id || check.name)} · ${esc(check.type || 'legacy')}</span><span class="${check.passed ? 'ok' : 'bad'}">${check.passed ? 'PASS' : 'FAIL'}</span></li>`).join('') || '<li>No checks</li>';
      const events = (evidence.events || []).map(item => `<li><span>${esc(item.index)} · ${esc(item.type)}</span><code>${esc(item.step_hash)}</code></li>`).join('') || '<li>No recorded events</li>';
      return `<div class="card-top"><div><div class="eyebrow">03 / Latest proof</div><h2>${esc(run.mission_id)}</h2><div class="path">${esc(run.run_id)}</div></div><span class="badge ${run.proof_status === 'LOCAL_VERIFIED' ? 'ok' : 'bad'}">${esc(run.proof_status)}</span></div><div class="evidence-grid"><div class="evidence-tile"><div class="k">Provider</div><div class="v">${esc(provider.provider)} · ${esc(provider.resolved_model)}</div></div><div class="evidence-tile"><div class="k">Merkle root</div><div class="v">${esc(integrity.event_merkle_root)}</div></div><div class="evidence-tile"><div class="k">Bundle hash</div><div class="v">${esc(integrity.bundle_hash)}</div></div></div><h3>Artifacts and hashes</h3><ul class="evidence-list">${artifacts}</ul><h3>Acceptance checks</h3><ul class="evidence-list">${checks}</ul><h3>Event replay</h3><ul class="evidence-list">${events}</ul><div class="tamper-lab"><div class="eyebrow">Tamper Lab · disposable copies</div><div class="tamper-actions"><button class="tamper" data-tamper="artifact" data-run-id="${esc(run.run_id)}">Tamper artifact</button><button class="tamper" data-tamper="event" data-run-id="${esc(run.run_id)}">Tamper event</button><button class="tamper" data-tamper="metadata" data-run-id="${esc(run.run_id)}">Tamper metadata</button><a href="${esc(run.bundle_url)}" target="_blank" rel="noopener">Proof Bundle ↗</a></div></div>`;
    }

    async function loadEvidence(runId, scroll = true) {
      const body = await api(`/api/runs/${encodeURIComponent(runId)}`);
      selectedRun = runId;
      const node = $('#evidence');
      node.innerHTML = evidenceView(body);
      node.className = 'card evidence show';
      setIntegrityFromRun(body.summary);
      applyEvidenceFlow(body);
      if (scroll) node.scrollIntoView({behavior:'smooth', block:'start'});
    }

    async function refresh() {
      try {
        const data = await api('/api/state');
        const ready = Boolean(data.doctor.available);
        const latest = data.runs[0];
        $('#runtime-version').textContent = `v${data.service.version}`;
        $('#mission-count').textContent = data.missions.filter(mission => mission.valid).length;
        $('#run-count').textContent = data.runs.length;
        $('#gvisor-status').textContent = ready ? 'READY' : 'OFFLINE';
        $('#gvisor-status').style.color = ready ? 'var(--green)' : 'var(--amber)';
        $('#proof-status').textContent = latest?.proof_status || 'NO RUNS';
        $('#proof-status').style.color = latest?.proof_status === 'LOCAL_VERIFIED' ? 'var(--green)' : (latest ? 'var(--red)' : 'inherit');
        $('#ready-status').textContent = ready ? 'Sandbox ready' : 'Fixture ready';
        $('#ready-status').className = 'micro-status good';
        $('#verified-status').textContent = latest?.proof_status || 'Verifier ready';
        $('#verified-status').className = `micro-status ${latest?.proof_status === 'FAILED' ? 'bad' : 'good'}`;
        $('#integrity-status').textContent = latest?.proof_status === 'FAILED' ? 'Integrity failed' : 'Integrity monitor';
        $('#integrity-status').className = `micro-status ${latest?.proof_status === 'FAILED' ? 'bad' : ''}`;
        $('#missions').innerHTML = data.missions.length ? data.missions.map(mission => missionCard(mission, ready, data.service.openai_configured)).join('') : '<div class="card empty">No manifests in the configured directory.</div>';
        $('#runs').innerHTML = data.runs.length ? data.runs.map(runRow).join('') : '<div class="empty">No runs yet. Start an approved mission above.</div>';
        setIntegrityFromRun(latest);
        if (!latest) {
          const validMissions = data.missions.filter(mission => mission.valid);
          setFlow(validMissions.length ? 'ready' : 'idle', {
            source: validMissions.length ? `${validMissions.length} approved manifest${validMissions.length === 1 ? '' : 's'}` : 'No approved manifest',
            run: 'No run selected',
            hash: 'No bundle hash',
          });
        }
        if (latest && !selectedRun) await loadEvidence(latest.run_id, false);
      } catch (error) {
        toast(error.message, true);
      }
    }

    document.addEventListener('click', async (event) => {
      const refreshButton = event.target.closest('[data-refresh]');
      const runButton = event.target.closest('[data-run]');
      const verifyButton = event.target.closest('[data-verify]');
      const detailButton = event.target.closest('[data-detail]');
      const tamperButton = event.target.closest('[data-tamper]');
      if (!refreshButton && !runButton && !verifyButton && !detailButton && !tamperButton) return;
      try {
        if (refreshButton) {
          await refresh();
          toast('Evidence state refreshed.');
        } else if (runButton) {
          if (busy) return;
          busy = true;
          setFlow('running', {
            source: `${runButton.dataset.run} · manifest validated`,
            run: 'API request in progress',
            hash: 'Proof Bundle not sealed yet',
          });
          $('#flow-ready-value').textContent = `${runButton.dataset.run} · manifest validated`;
          $('#flow-executing-value').textContent = 'Provider call and controlled materialization in progress';
          $('#flow-acceptance-value').textContent = 'Will begin after execution output is recorded';
          $('#flow-proof-value').textContent = 'Will seal only after deterministic acceptance';
          $('#flow-verified-value').textContent = 'Independent verification not started';
          runButton.disabled = true;
          runButton.textContent = 'Mission running…';
          const body = await api('/api/runs', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({mission_path:runButton.dataset.run})});
          selectedRun = null;
          toast(`Mission ${body.run.mission_id}: ${body.run.proof_status}`);
        } else if (verifyButton) {
          verifyButton.disabled = true;
          const body = await api('/api/verify', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({run_id:verifyButton.dataset.verify})});
          setIntegrityFromRun(body.run);
          toast(`Reverification: ${body.run.proof_status}`, body.run.proof_status !== 'LOCAL_VERIFIED');
        } else if (detailButton) {
          await loadEvidence(detailButton.dataset.detail);
        } else if (tamperButton) {
          tamperButton.disabled = true;
          const body = await api('/api/tamper', {method:'POST', headers:{'Content-Type':'application/json','X-APR-Token':token}, body:JSON.stringify({run_id:tamperButton.dataset.runId, case:tamperButton.dataset.tamper})});
          setTamperResult(body.result);
          toast(`${body.result.case} copy: ${body.result.status} · original preserved=${body.result.original_preserved}`, body.result.status !== 'FAILED');
        }
      } catch (error) {
        toast(error.message, true);
      } finally {
        busy = false;
        if (!tamperButton) await refresh();
      }
    });

    refresh();
  </script>
</body>
</html>'''


def render_mission_control(csrf_token: str) -> str:
    """Render the operator dashboard with a safely serialized CSRF token."""

    try:
        from .osa_brand_source import JPEG_BASE64

        brand_data_uri = f"data:image/jpeg;base64,{JPEG_BASE64}"
    except Exception:  # An optional visual asset must never take Mission Control down.
        try:
            encoded_brand = base64.b64encode(_OSA_BRAND_PATH.read_bytes()).decode("ascii")
            brand_data_uri = f"data:image/jpeg;base64,{encoded_brand}"
        except OSError:
            brand_data_uri = ""
    return (
        _DASHBOARD.replace("__APR_CSRF_TOKEN__", json.dumps(csrf_token))
        .replace("__OSA_BRAND_DATA__", brand_data_uri)
    )
