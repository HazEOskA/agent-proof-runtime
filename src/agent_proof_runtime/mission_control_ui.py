"""Dependency-free Mission Control dashboard."""

from __future__ import annotations

import json


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
    .brand-lockup { display: flex; align-items: center; gap: 18px; min-width: 0; }
    .brand-mark {
      position: relative;
      width: 88px;
      aspect-ratio: 1;
      flex: 0 0 auto;
      display: grid;
      place-items: center;
      clip-path: polygon(50% 0, 90% 20%, 100% 68%, 50% 100%, 0 68%, 10% 20%);
      background: linear-gradient(145deg, #84fff5 0%, #1e777e 31%, #071216 62%, #1ad9cb 100%);
      filter: drop-shadow(0 0 18px rgba(54, 240, 228, .28));
    }
    .brand-mark::before {
      content: "";
      position: absolute;
      inset: 5px;
      clip-path: inherit;
      background: radial-gradient(circle at 50% 35%, #163f46, #061013 70%);
    }
    .brand-mark span {
      position: relative;
      color: #d8fffc;
      font: 900 25px/.78 var(--mono);
      letter-spacing: -.12em;
      text-align: center;
      text-shadow: 0 0 12px #21d8cf;
    }
    .brand-name { min-width: 0; }
    .brand-name .wordmark {
      font-size: clamp(28px, 4vw, 48px);
      line-height: .95;
      font-weight: 840;
      font-style: italic;
      letter-spacing: -.055em;
      white-space: nowrap;
      color: #b8c8cb;
      text-shadow: 0 2px #061013;
    }
    .brand-name .wordmark em { color: #2ab9ff; font-style: italic; text-shadow: 0 0 18px rgba(42,185,255,.32); }
    .brand-name .submark { margin-top: 8px; font: 700 11px/1.3 var(--mono); letter-spacing: .1em; color: #96adb1; }
    .brand-name .studio {
      display: inline-flex;
      margin-top: 8px;
      padding: 3px 13px;
      border: 1px solid #22525a;
      clip-path: polygon(8px 0, 100% 0, calc(100% - 8px) 100%, 0 100%);
      color: #5fa1d2;
      font: 700 10px/1 var(--mono);
      letter-spacing: .16em;
    }

    .runtime-stack { display: grid; grid-template-columns: repeat(3, auto); align-items: center; gap: 10px; }
    .runtime-chip {
      min-width: 74px;
      min-height: 62px;
      display: grid;
      place-items: center;
      padding: 8px 10px;
      border: 1px solid #2c4650;
      border-radius: 12px;
      background: linear-gradient(150deg, rgba(26,46,53,.95), rgba(7,16,20,.95));
      box-shadow: inset 0 1px rgba(255,255,255,.05), 0 10px 30px rgba(0,0,0,.25);
      font: 800 11px/1.25 var(--mono);
      text-align: center;
      color: #adc2c6;
    }
    .runtime-chip.primary { min-height: 82px; border-color: #337584; color: var(--cyan-soft); box-shadow: inset 0 0 25px rgba(54,240,228,.08), 0 0 18px rgba(54,240,228,.1); }
    .runtime-chip small { display: block; margin-top: 4px; color: #607c83; font-size: 9px; }

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

    .flow-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 18px; margin: 12px 0 16px; }
    .flow-step {
      position: relative;
      min-height: 72px;
      padding: 13px;
      border: 1px solid #315469;
      border-radius: 8px;
      background: linear-gradient(135deg, #183b4a, #172a42);
      box-shadow: inset 0 0 22px rgba(70,169,255,.07);
      color: #a8e8dd;
      font: 800 11px/1.35 var(--mono);
      text-transform: uppercase;
    }
    .flow-step:not(:last-child)::after {
      content: "";
      position: absolute;
      top: 50%;
      left: calc(100% + 1px);
      width: 18px;
      height: 2px;
      background: linear-gradient(90deg, var(--cyan), #1e5d63);
      box-shadow: 0 0 8px rgba(54,240,228,.5);
    }
    .flow-step:not(:last-child)::before {
      content: "";
      position: absolute;
      z-index: 1;
      top: calc(50% - 3px);
      right: -19px;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--cyan);
    }
    .flow-step span { display: block; margin-bottom: 8px; color: #5de2d5; }
    .flow-step.active { border-color: var(--green); box-shadow: inset 0 0 25px rgba(104,247,154,.1), 0 0 18px rgba(104,247,154,.08); }
    .flow-step.failed { border-color: var(--red); color: #ffabb1; background: linear-gradient(135deg, #35181d, #21131a); }

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
      .runtime-stack { justify-content: start; padding-left: 106px; }
      .hero { grid-template-columns: 1fr; }
      .hero-proof { justify-self: start; width: 100%; max-width: 620px; }
      .flow-grid { grid-template-columns: 1fr; gap: 8px; }
      .flow-step { min-height: 58px; }
      .flow-step:not(:last-child)::after { top: 100%; left: 25px; width: 2px; height: 8px; background: var(--cyan); }
      .flow-step:not(:last-child)::before { top: auto; bottom: -9px; left: 23px; right: auto; }
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
      .brand-mark { width: 66px; }
      .brand-mark span { font-size: 20px; }
      .brand-lockup { gap: 12px; }
      .brand-name .wordmark { font-size: clamp(25px, 9vw, 35px); }
      .brand-name .submark { font-size: 9px; }
      .runtime-stack { grid-template-columns: repeat(3, 1fr); padding-left: 0; }
      .runtime-chip { min-width: 0; min-height: 55px; font-size: 9px; }
      .runtime-chip.primary { min-height: 62px; }
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
        <div class="brand-mark" aria-label="OsaTechGPT"><span>OS<br>A</span></div>
        <div class="brand-name">
          <div class="wordmark">OsaTech<em>GPT</em></div>
          <div class="submark">PROOF SYSTEMS // MISSION CONTROL</div>
          <span class="studio">AI STUDIO</span>
        </div>
      </div>
      <div class="runtime-stack" aria-label="Runtime providers">
        <div class="runtime-chip">OPENAI<small>optional provider</small></div>
        <div class="runtime-chip primary">CODEX<small>build runtime</small></div>
        <div class="runtime-chip">APR<small id="runtime-version">v—</small></div>
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
        <div class="flow-grid" id="flow-grid">
          <div class="flow-step" data-stage="ready"><span>01</span>Mission ready</div>
          <div class="flow-step" data-stage="executing"><span>02</span>Executing</div>
          <div class="flow-step" data-stage="acceptance"><span>03</span>Acceptance</div>
          <div class="flow-step" data-stage="proof"><span>04</span>Building proof</div>
          <div class="flow-step" data-stage="verified"><span>05</span>Local verified</div>
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
        <div class="dock-brand">⬡ CODEX LABS</div>
        <div class="dock-command">osa@apr-mission-control:~$ verify --manifest-only</div>
        <div class="dock-power">⬡ POWERED BY CODEX</div>
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

    function setFlow(state) {
      const stages = [...document.querySelectorAll('[data-stage]')];
      stages.forEach(stage => stage.classList.remove('active', 'failed'));
      if (state === 'running') {
        stages.slice(0, 2).forEach(stage => stage.classList.add('active'));
      } else if (state === 'failed') {
        stages.slice(0, 4).forEach(stage => stage.classList.add('active'));
        stages[4].classList.add('failed');
      } else if (state === 'verified') {
        stages.forEach(stage => stage.classList.add('active'));
      } else {
        stages[0].classList.add('active');
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
      setFlow(verified ? 'verified' : 'failed');
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
      setFlow('failed');
      $('#alert-kicker').textContent = 'Tamper Lab · mutation detected';
      $('#alert-title').textContent = 'INTEGRITY FAILED';
      $('#alert-copy').textContent = result.errors?.[0] || 'The disposable copy no longer matches its recorded evidence.';
      $('#alert-case').textContent = String(result.case || 'UNKNOWN').toUpperCase();
      $('#alert-copy-status').textContent = result.status || 'FAILED';
      $('#alert-original').textContent = result.original_preserved ? 'PRESERVED' : 'CHANGED';
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
          setFlow('running');
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

    return _DASHBOARD.replace("__APR_CSRF_TOKEN__", json.dumps(csrf_token))
