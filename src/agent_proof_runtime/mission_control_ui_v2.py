"""Final connected-PCB presentation layer for Mission Control.

This module intentionally wraps the existing renderer. It changes presentation only:
no mission, provider, proof, verifier, API, or persistence behavior is modified.
"""

from __future__ import annotations

from .mission_control_ui import render_mission_control as _render_base

_UI_V2_CSS = r"""

    /* Final Build Week UI lock: one connected PCB, not a collection of cards. */
    .review-strip {
      border-radius: 6px;
      border-color: rgba(70, 129, 132, .6);
      background: rgba(5, 18, 21, .34);
      backdrop-filter: blur(8px);
    }

    .masthead {
      position: relative;
      isolation: isolate;
      grid-template-columns: 188px minmax(0, 1fr);
      align-items: center;
      gap: 22px;
      min-height: 176px;
      padding: 10px 14px 6px;
      overflow: hidden;
    }
    .masthead::before,
    .masthead::after {
      content: "";
      position: absolute;
      z-index: 0;
      left: 154px;
      right: 18px;
      top: 88px;
      height: 2px;
      pointer-events: none;
    }
    .masthead::before {
      background: linear-gradient(90deg, #214e53 0%, #3f8f8d 35%, #2b6f73 72%, #214e53 100%);
      box-shadow: 0 -18px 0 -1px rgba(40, 90, 94, .72), 0 18px 0 -1px rgba(40, 90, 94, .58);
    }
    .masthead::after {
      width: 42%;
      right: auto;
      background: repeating-linear-gradient(90deg, transparent 0 12px, #4fe5dd 12px 17px, transparent 17px 27px);
      background-size: 27px 2px;
      animation: apr-top-bus 1.2s linear infinite;
    }
    @keyframes apr-top-bus { to { background-position-x: 27px; } }

    .brand-lockup {
      z-index: 2;
      width: 176px;
      height: 160px;
      overflow: visible;
    }
    .brand-mask {
      width: 152px;
      height: 152px;
      clip-path: polygon(24% 2%,76% 2%,98% 24%,98% 76%,76% 98%,24% 98%,2% 76%,2% 24%);
      border: 1px solid rgba(76, 151, 150, .52);
      background: rgba(3, 12, 15, .74);
      box-shadow: none;
    }
    .brand-mask::after { display: block; border-color: rgba(89, 177, 171, .18); }
    .brand-source {
      left: -6px;
      top: -60px;
      width: 864px;
      height: 1536px;
      filter: grayscale(.08) saturate(.64) contrast(1.24) brightness(.76);
    }
    .brand-circuit {
      display: block;
      left: 112px;
      width: 246px;
      opacity: .95;
      overflow: visible;
    }
    .brand-circuit path { stroke: #347c7d; stroke-width: 1.65; }
    .brand-circuit .signal { stroke: #52ddd6; stroke-width: 2; }
    .brand-circuit circle { stroke: #55aaa8; }

    .runtime-stack {
      z-index: 2;
      width: 100%;
      min-width: 0;
      height: 160px;
      overflow: visible;
    }
    .runtime-traces {
      inset: 0;
      width: 100%;
      height: 160px;
      opacity: 1;
    }
    .runtime-traces path { stroke: #39777b; stroke-width: 1.8; }
    .runtime-traces path.runtime-signal { stroke: #4fe5dd; stroke-width: 2.15; stroke-dasharray: 5 10; }
    .runtime-traces circle { fill: #061316; stroke: #5bc0bd; stroke-width: 1.6; }

    .runtime-openai-card {
      top: 43px;
      left: 1.5%;
      width: 154px;
      min-height: 70px;
      border-radius: 5px;
      border-color: #436d73;
      background: rgba(9, 27, 32, .72);
      box-shadow: none;
    }
    .runtime-gate {
      top: 58px;
      left: 29%;
      width: 52px;
      height: 44px;
      border-radius: 4px 17px 17px 4px;
      background: rgba(8, 39, 43, .88);
      box-shadow: none;
    }
    .model-core {
      left: 41%;
      top: 49px;
      bottom: auto;
      width: 72px;
      height: 62px;
      border-color: #42686d;
      background: rgba(9, 24, 28, .9);
      box-shadow: none;
    }
    .runtime-chip.codex-core {
      top: 28px;
      right: 16%;
      width: 104px;
      height: 104px;
      border: 6px double #47777d;
      border-radius: 5px;
      background: linear-gradient(145deg, rgba(18, 54, 61, .94), rgba(5, 18, 22, .98));
      box-shadow: none;
    }
    .agent-core {
      right: 1%;
      top: 57px;
      bottom: auto;
      width: 62px;
      height: 48px;
      border-color: #42666b;
      background: rgba(8, 22, 26, .9);
      box-shadow: none;
    }

    .hero {
      min-height: 190px;
      padding: 12px 14px 24px;
    }
    .hero h1 {
      max-width: 1000px;
      margin: 10px 0 12px;
      font-size: clamp(44px, 5.3vw, 70px);
    }
    .quick-nav {
      border-radius: 6px;
      background: rgba(5, 18, 21, .44);
    }

    #mission-studio {
      border-radius: 8px;
      border-color: rgba(69, 128, 132, .68);
      background:
        linear-gradient(90deg, rgba(255,255,255,.012) 1px, transparent 1px),
        linear-gradient(rgba(255,255,255,.012) 1px, transparent 1px),
        rgba(3, 13, 16, .56);
      background-size: 18px 18px, 18px 18px, auto;
    }
    #mission-studio .studio-form,
    #mission-studio .agent-zone,
    #mission-studio .trust-zone,
    #mission-studio .studio-timeline,
    #mission-studio .studio-result {
      border-radius: 5px;
      background-color: rgba(4, 15, 18, .42);
      box-shadow: none;
    }

    #mission-studio .studio-zones {
      grid-template-columns: minmax(0, 1fr) 232px;
      gap: 28px;
      overflow: visible;
    }
    #mission-studio .agent-zone,
    #mission-studio .trust-zone { position: relative; overflow: visible; }
    #mission-studio .agent-zone::after {
      content: "";
      position: absolute;
      z-index: 4;
      top: 52%;
      right: -30px;
      width: 30px;
      height: 3px;
      background: repeating-linear-gradient(90deg, #2f7375 0 8px, #64e6df 8px 13px, #2f7375 13px 22px);
      background-size: 22px 3px;
      animation: agent-bus .8s linear infinite;
    }
    #mission-studio .trust-zone::before {
      content: "";
      position: absolute;
      z-index: 5;
      left: -8px;
      top: calc(52% - 6px);
      width: 12px;
      height: 12px;
      border: 2px solid #65e4dd;
      border-radius: 50%;
      background: #061417;
    }
    #mission-studio .agent-pipeline::before {
      top: 16px;
      height: 3px;
      background: repeating-linear-gradient(90deg, #285c60 0 10px, #5fcfc9 10px 15px, #285c60 15px 27px);
      background-size: 27px 3px;
      opacity: .95;
    }
    #mission-studio:not([data-run-state="idle"]) .agent-pipeline::before { animation: agent-bus .85s linear infinite; }
    #mission-studio .studio-agent {
      border-radius: 4px;
      background: rgba(5, 18, 21, .36);
    }
    #mission-studio .studio-agent:not(:last-child)::after {
      top: 15px;
      left: 100%;
      width: 12px;
      height: 3px;
      background: #4da5a2;
    }
    #mission-studio .studio-agent .agent-index::before {
      position: relative;
      z-index: 3;
      box-shadow: 0 0 0 3px #061316;
    }
    #mission-studio .trust-gate {
      border-radius: 4px;
      border-color: #4ba89d;
      background: rgba(7, 35, 34, .54);
    }
    #mission-studio .studio-bottom::before {
      content: "";
      position: absolute;
      z-index: 0;
      left: 74%;
      top: -15px;
      width: 3px;
      height: 16px;
      background: repeating-linear-gradient(0deg, #2d6668 0 5px, #5edbd4 5px 9px, #2d6668 9px 14px);
    }
    #mission-studio .studio-bottom > * { position: relative; z-index: 1; }

    .control-room {
      border-radius: 8px;
      background: rgba(4, 16, 19, .5);
      box-shadow: none;
    }
    .flow-board {
      min-height: 236px;
      border-radius: 5px;
      background-color: rgba(3, 13, 16, .36);
    }
    .flow-wires { opacity: 1; }
    .bus-base { stroke: #39777a; stroke-width: 2.6; }
    .bus-base-thin { stroke: #2f666a; stroke-width: 1.35; stroke-dasharray: 5 7; }
    .bus-tap { stroke: #356d70; stroke-width: 1.45; }
    .bus-progress { stroke-width: 3; opacity: .22; }
    .flow-board[data-state="running"] .bus-progress,
    .flow-board[data-state="verified"] .bus-progress,
    .flow-board[data-state="failed"] .bus-progress,
    .flow-board[data-state="tamper-failed"] .bus-progress { opacity: 1; }
    .flow-grid { gap: 14px; padding-top: 38px; }
    .flow-step {
      min-height: 112px;
      border-radius: 4px;
      border-color: rgba(70, 117, 122, .42);
      background: rgba(5, 20, 23, .28) !important;
    }
    .flow-step:not(:last-child)::after {
      content: "";
      position: absolute;
      z-index: -1;
      top: -17px;
      left: 50%;
      width: calc(100% + 14px);
      height: 2px;
      background: #3b7779;
    }
    .flow-step::before {
      z-index: 3;
      width: 11px;
      height: 11px;
      border-width: 2px;
      box-shadow: 0 0 0 4px #061316;
    }

    .missions,
    #missions .card,
    .stats,
    .proof-console,
    .evidence,
    .command-dock {
      border-radius: 5px;
    }

    @media (max-width: 900px) {
      .masthead { grid-template-columns: 150px minmax(0,1fr); min-height: 168px; gap: 12px; }
      .brand-lockup { width: 146px; }
      .brand-mask { width: 136px; height: 136px; }
      .brand-circuit { left: 90px; width: 170px; }
      .runtime-openai-card { left: 0; width: 132px; }
      .runtime-gate { left: 31%; }
      .model-core { left: 45%; }
      .runtime-chip.codex-core { right: 14%; width: 88px; height: 88px; top: 36px; }
      .agent-core { right: 0; }
      #mission-studio .studio-zones { grid-template-columns: 1fr; gap: 14px; }
      #mission-studio .agent-zone::after { right: 50%; top: auto; bottom: -16px; width: 3px; height: 16px; }
      #mission-studio .trust-zone::before { left: calc(50% - 6px); top: -8px; }
    }

    @media (max-width: 640px) {
      .masthead { display: block; min-height: 316px; padding-top: 6px; }
      .masthead::before, .masthead::after { left: 72px; right: 12px; top: 150px; }
      .brand-lockup { height: 144px; }
      .runtime-stack { height: 154px; }
      .runtime-openai-card { left: 0; top: 40px; transform: scale(.84); transform-origin: left center; }
      .runtime-gate { left: 30%; transform: scale(.78); }
      .model-core { left: 45%; transform: scale(.82); }
      .runtime-chip.codex-core { right: 13%; transform: scale(.76); }
      .agent-core { right: 0; transform: scale(.78); }
      .hero { min-height: 0; padding-top: 2px; }
      .hero h1 { font-size: clamp(39px, 12vw, 56px); }
      .agent-pipeline { grid-template-columns: repeat(7, minmax(124px, 1fr)); overflow-x: auto; padding-bottom: 8px; }
      .flow-grid { grid-template-columns: repeat(5, minmax(150px,1fr)); overflow-x: auto; }
      .flow-wires { min-width: 760px; }
    }

    /* Flow-only patch: preserve the locked UI and expose one continuous execution route. */
    .masthead {
      align-items: center;
      overflow: visible;
    }
    .brand-lockup {
      display: grid;
      place-items: center;
      justify-self: center;
      align-self: center;
    }
    .masthead::after {
      width: auto;
      right: 18px;
    }

    /* Logo-only runtime rail: existing official marks, no additional labels. */
    .runtime-stack {
      position: relative;
      align-self: center;
      justify-self: center;
    }
    .runtime-traces { display: none; }
    .runtime-openai-card {
      top: 44px;
      left: 3%;
      display: flex;
      align-items: center;
      justify-content: flex-start;
      gap: 14px;
      width: 166px;
      min-height: 72px;
      padding: 0;
      border: 0;
      background: transparent;
      box-shadow: none;
    }
    .runtime-openai-card .openai-blossom { width: 46px; height: 46px; }
    .runtime-openai-card .openai-wordmark { width: 96px; height: 28px; }
    .runtime-openai-card span,
    .runtime-gate,
    .agent-core,
    .runtime-version-note { display: none; }
    .model-core {
      top: 52px;
      left: 52%;
      bottom: auto;
      width: 68px;
      height: 56px;
      border: 0;
      background: transparent;
      box-shadow: none;
    }
    .runtime-chip.codex-core {
      top: 43px;
      right: 4%;
      display: grid;
      place-items: center;
      width: 74px;
      height: 74px;
      padding: 0;
      border: 0;
      background: transparent;
      box-shadow: none;
    }
    .runtime-chip.codex-core::before,
    .runtime-chip.codex-core span,
    .runtime-chip.codex-core small { display: none; }
    .runtime-chip.codex-core .codex-mark { width: 54px; height: 54px; }
    .runtime-stack::before,
    .runtime-stack::after {
      content: "";
      position: absolute;
      z-index: 1;
      top: 80px;
      right: calc(4% + 36px);
      width: 3px;
      height: 112px;
      pointer-events: none;
    }
    .runtime-stack::before { background: #39777b; }
    .runtime-stack::after {
      background: repeating-linear-gradient(180deg, transparent 0 10px, #4fe5dd 10px 16px, transparent 16px 27px);
      background-size: 3px 27px;
      animation: apr-flow-down .9s linear infinite;
    }

    /* The visual order now follows execution: runtime -> approved mission -> agents -> trust gate. */
    #missions-section { order: 3; }
    #mission-studio { order: 4; }
    #control-room { order: 5; }
    #system-status { order: 6; }
    #runs-section { order: 7; }
    .command-dock { order: 8; }

    .hero,
    .quick-nav,
    #missions-section,
    #mission-studio,
    #mission-studio .studio-form,
    #mission-studio .studio-zones,
    #mission-studio .trust-zone { position: relative; overflow: visible; }

    .hero::after,
    .quick-nav::after,
    #missions-section::before,
    #missions-section::after,
    #mission-studio::before,
    #mission-studio .studio-form::after,
    #mission-studio .studio-zones::before,
    #mission-studio .trust-zone::after {
      content: "";
      position: absolute;
      z-index: 3;
      width: 3px;
      pointer-events: none;
      background-color: #39777b;
      background-image: repeating-linear-gradient(180deg, transparent 0 10px, #4fe5dd 10px 16px, transparent 16px 27px);
      background-size: 3px 27px;
      animation: apr-flow-down .9s linear infinite;
    }
    .hero::after { top: -10px; right: 7.5%; bottom: -10px; }
    .quick-nav::after { top: -12px; right: 7.5%; bottom: -30px; }
    #missions-section::before { top: -30px; right: 7.5%; bottom: 45%; }
    #missions-section::after { top: 55%; bottom: -30px; left: 50%; }
    #mission-studio::before { top: -30px; left: 50%; height: 30px; }
    #mission-studio .studio-form::after { bottom: -20px; left: 50%; height: 20px; }
    #mission-studio .studio-zones::before { top: -18px; left: 50%; height: 18px; }
    #mission-studio .trust-zone::after { bottom: -18px; left: 50%; height: 18px; }

    .missions::before,
    #mission-studio .agent-pipeline::before,
    #mission-studio .agent-zone::after,
    #mission-studio .studio-bottom::before {
      animation: agent-bus .8s linear infinite;
    }
    #mission-studio .studio-bottom::before {
      background: repeating-linear-gradient(0deg, #2d6668 0 5px, #5edbd4 5px 9px, #2d6668 9px 14px);
    }

    @keyframes apr-flow-down { to { background-position-y: 27px; } }

    @media (max-width: 900px) {
      .brand-lockup { margin-inline: auto; }
      #mission-studio .agent-zone::after {
        right: 50%;
        top: auto;
        bottom: -16px;
        width: 3px;
        height: 16px;
      }
      #mission-studio .trust-zone::after { left: 50%; }
    }

    @media (max-width: 640px) {
      .masthead { min-height: 304px; }
      .masthead::before,
      .masthead::after { top: 222px; left: 14px; right: 14px; }
      .runtime-stack {
        width: 100%;
        min-width: 0;
        height: 148px;
        margin: 0 auto;
        transform: none;
        transform-origin: center;
      }
      .brand-lockup::after {
        content: "";
        position: absolute;
        z-index: 1;
        top: 124px;
        right: -95px;
        width: 3px;
        height: 98px;
        pointer-events: none;
        background-color: #39777b;
        background-image: repeating-linear-gradient(180deg, transparent 0 10px, #4fe5dd 10px 16px, transparent 16px 27px);
        background-size: 3px 27px;
        animation: apr-flow-down .9s linear infinite;
      }
      .runtime-openai-card {
        top: 44px;
        left: 1%;
        gap: 7px;
        width: 124px;
        min-height: 60px;
        transform: none;
      }
      .runtime-openai-card .openai-blossom { width: 36px; height: 36px; }
      .runtime-openai-card .openai-wordmark { width: 78px; height: 24px; }
      .model-core {
        top: 48px;
        left: 52%;
        width: 54px;
        height: 52px;
        transform: translateX(-50%);
      }
      .runtime-chip.codex-core {
        top: 48px;
        right: 2%;
        width: 54px;
        height: 54px;
        transform: none;
      }
      .runtime-chip.codex-core .codex-mark { width: 46px; height: 46px; }
      .runtime-stack::before,
      .runtime-stack::after {
        top: 74px;
        right: calc(2% + 26px);
        height: 82px;
      }
      .hero::after,
      .quick-nav::after,
      #missions-section::before { right: 13%; }
      #missions-section { margin-top: 22px; }
    }

    @media (prefers-reduced-motion: reduce) {
      .masthead::after,
      .brand-lockup::after,
      .runtime-stack::after,
      .hero::after,
      .quick-nav::after,
      #missions-section::before,
      #missions-section::after,
      #mission-studio::before,
      #mission-studio .studio-form::after,
      #mission-studio .studio-zones::before,
      #mission-studio .agent-zone::after,
      #mission-studio .trust-zone::after,
      #mission-studio .agent-pipeline::before,
      #mission-studio .studio-bottom::before,
      .missions::before { animation: none !important; }
    }
"""


def render_mission_control_v2(csrf_token: str) -> str:
    """Render the existing dashboard with the final connected-PCB UI layer."""

    dashboard = _render_base(csrf_token)
    marker = "  </style>"
    if marker not in dashboard:
        raise RuntimeError("Mission Control stylesheet marker is missing")
    return dashboard.replace(marker, _UI_V2_CSS + marker, 1)
