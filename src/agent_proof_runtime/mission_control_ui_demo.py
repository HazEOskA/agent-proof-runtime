"""Desktop demo polish layered on the current main Mission Control preview.

The current ``main`` renderer remains the source of truth. This module only injects
an additive presentation layer: no mission, provider, proof, verifier, API, state,
or persistence behavior is changed.
"""

from __future__ import annotations

from .mission_control_ui_v2 import render_mission_control_v2 as _render_main_preview


_DEMO_LOCK_CSS = r"""

    /* Desktop demo lock. The current main preview remains the source of truth. */
    @media (min-width: 901px) {
      body::before {
        opacity: .46;
        background-image:
          linear-gradient(90deg, transparent 0 11%, rgba(59, 125, 128, .18) 11% 11.18%, transparent 11.18% 52%, rgba(59, 125, 128, .14) 52% 52.16%, transparent 52.16%),
          linear-gradient(0deg, transparent 0 17%, rgba(59, 125, 128, .16) 17% 17.22%, transparent 17.22% 66%, rgba(59, 125, 128, .12) 66% 66.2%, transparent 66.2%),
          linear-gradient(90deg, rgba(50, 110, 114, .08) 1px, transparent 1px),
          linear-gradient(rgba(50, 110, 114, .07) 1px, transparent 1px);
        background-size: 320px 220px, 320px 220px, 32px 32px, 32px 32px;
        mask-image: linear-gradient(to bottom, black 0%, rgba(0,0,0,.9) 78%, transparent 100%);
      }

      .board-traces { opacity: .62; }
      .board-traces .trace.hot {
        stroke: #42d8d1;
        stroke-width: 1.7;
        stroke-dasharray: 8 18;
        animation-duration: 3.2s;
        filter: drop-shadow(0 0 3px rgba(66, 216, 209, .38));
      }

      .masthead {
        grid-template-columns: 184px minmax(0, 1fr);
        align-items: center;
        gap: 30px;
        min-height: 196px;
        padding: 10px 18px 18px;
        overflow: hidden;
      }
      .masthead::before,
      .masthead::after {
        top: auto;
        bottom: 12px;
        height: 3px;
      }
      .masthead::before {
        left: 92px;
        right: 34px;
        background: linear-gradient(90deg, #214e53, #438b8a 38%, #347679 72%, #214e53);
        box-shadow: 0 -11px 0 -1px rgba(42, 93, 97, .48);
      }
      .masthead::after {
        left: 92px;
        right: auto;
        width: 30%;
        background: repeating-linear-gradient(90deg, transparent 0 10px, #63eee6 10px 16px, transparent 16px 26px);
        background-size: 26px 3px;
        animation: apr-demo-top-bus 1.05s linear infinite;
        filter: drop-shadow(0 0 4px rgba(99, 238, 230, .42));
      }
      @keyframes apr-demo-top-bus { to { background-position-x: 26px; } }

      .brand-lockup {
        display: grid;
        place-items: center;
        width: 184px;
        height: 174px;
        overflow: visible;
      }
      .brand-lockup::after {
        content: "";
        position: absolute;
        z-index: 1;
        left: 50%;
        bottom: -4px;
        width: 3px;
        height: 26px;
        transform: translateX(-50%);
        background: repeating-linear-gradient(0deg, #2d6668 0 6px, #61e4dd 6px 10px, #2d6668 10px 16px);
        background-size: 3px 16px;
        animation: apr-demo-drop 1s linear infinite;
        filter: drop-shadow(0 0 4px rgba(97, 228, 221, .42));
      }
      @keyframes apr-demo-drop { to { background-position-y: 16px; } }

      .brand-mask {
        width: 164px;
        height: 164px;
        margin: 0 auto;
        border-color: rgba(87, 177, 173, .74);
        background: rgba(3, 12, 15, .82);
        box-shadow: inset 0 0 24px rgba(49, 151, 148, .08), 0 0 18px rgba(49, 151, 148, .08);
      }
      .brand-mask::after { border-color: rgba(101, 224, 215, .28); }
      .brand-circuit {
        left: 124px;
        top: 7px;
        width: 236px;
        height: 160px;
        opacity: .82;
      }
      .brand-circuit .signal {
        stroke: #61e4dd;
        stroke-dasharray: 7 13;
        animation: trace-flow 2s linear infinite;
        filter: drop-shadow(0 0 3px rgba(97, 228, 221, .38));
      }

      .runtime-stack {
        position: relative;
        z-index: 2;
        display: grid;
        grid-template-columns: minmax(176px, 1.16fr) minmax(148px, .92fr) minmax(148px, .92fr);
        align-items: center;
        gap: 24px;
        width: 100%;
        min-width: 0;
        height: 174px;
        padding: 0 8px 22px;
        overflow: visible;
        background:
          linear-gradient(180deg, transparent 0 73%, rgba(66, 139, 140, .54) 73% 75%, transparent 75%) 16.666% 0 / 2px 100% no-repeat,
          linear-gradient(180deg, transparent 0 73%, rgba(66, 139, 140, .54) 73% 75%, transparent 75%) 50% 0 / 2px 100% no-repeat,
          linear-gradient(180deg, transparent 0 73%, rgba(66, 139, 140, .54) 73% 75%, transparent 75%) 83.333% 0 / 2px 100% no-repeat,
          linear-gradient(90deg, #2f6669, #458d8b 50%, #2f6669) 0 calc(100% - 12px) / 100% 2px no-repeat;
      }
      .runtime-stack::after {
        content: "";
        position: absolute;
        z-index: 4;
        left: 0;
        bottom: 9px;
        width: 74px;
        height: 4px;
        border-radius: 99px;
        background: linear-gradient(90deg, transparent, #6af4ec 30% 70%, transparent);
        animation: apr-demo-packet 2.4s linear infinite;
        filter: drop-shadow(0 0 5px rgba(106, 244, 236, .7));
        pointer-events: none;
      }
      @keyframes apr-demo-packet {
        from { transform: translateX(-74px); }
        to { transform: translateX(calc(100vw - 360px)); }
      }

      .runtime-traces {
        position: absolute;
        z-index: 0;
        inset: 0 0 0;
        width: 100%;
        height: 174px;
        opacity: .74;
        pointer-events: none;
      }
      .runtime-traces path { stroke: #39777b; stroke-width: 1.7; }
      .runtime-traces path.runtime-signal {
        stroke: #62e9e1;
        stroke-width: 2.35;
        stroke-dasharray: 8 13;
        animation: trace-flow 1.8s linear infinite;
        filter: drop-shadow(0 0 3px rgba(98, 233, 225, .52));
      }
      .runtime-traces circle { fill: #061316; stroke: #64c8c4; stroke-width: 1.5; }

      .runtime-openai-card {
        position: static !important;
        display: contents !important;
      }
      .runtime-openai-card > div,
      .runtime-openai-card > .openai-blossom,
      .runtime-chip.codex-core {
        position: relative !important;
        inset: auto !important;
        top: auto !important;
        right: auto !important;
        bottom: auto !important;
        left: auto !important;
        z-index: 3;
        align-self: center;
        height: 148px;
        border: 1px solid rgba(73, 133, 137, .82);
        border-radius: 6px;
        background:
          linear-gradient(145deg, rgba(17, 47, 53, .88), rgba(4, 17, 21, .96));
        box-shadow: inset 0 0 0 1px rgba(120, 196, 194, .06), 0 12px 28px rgba(0,0,0,.22);
        clip-path: polygon(11% 0, 89% 0, 100% 11%, 100% 89%, 89% 100%, 11% 100%, 0 89%, 0 11%);
        opacity: 1;
      }
      .runtime-openai-card > div {
        order: 1;
        display: grid;
        place-items: center;
        width: 100%;
        min-width: 0;
        padding: 26px 22px;
      }
      .runtime-openai-card > .openai-blossom {
        order: 2;
        justify-self: center;
        width: 148px !important;
        height: 148px !important;
        padding: 39px;
        color: #eefafa;
      }
      .runtime-openai-card .openai-wordmark {
        display: block;
        width: min(132px, 100%) !important;
        height: 36px !important;
        color: #eefafa;
      }
      .runtime-openai-card span { display: none !important; }

      .runtime-chip.codex-core {
        order: 3;
        justify-self: center;
        display: grid;
        place-items: center;
        width: 148px;
        padding: 34px;
      }
      .runtime-chip.codex-core::before {
        inset: -9px;
        opacity: .58;
      }
      .runtime-chip.codex-core .codex-mark {
        width: 66px;
        height: 66px;
        border-radius: 14px;
      }
      .runtime-chip.codex-core span,
      .runtime-chip.codex-core small { display: none !important; }

      .runtime-gate,
      .model-core,
      .agent-core { display: none !important; }

      #mission-studio {
        position: relative;
        isolation: isolate;
        overflow: hidden;
        background:
          linear-gradient(90deg, rgba(255,255,255,.012) 1px, transparent 1px),
          linear-gradient(rgba(255,255,255,.012) 1px, transparent 1px),
          rgba(3, 13, 16, .58);
        background-size: 24px 24px, 24px 24px, auto;
      }
      #mission-studio::before {
        content: "";
        position: absolute;
        z-index: 0;
        inset: 0;
        pointer-events: none;
        opacity: .34;
        background:
          linear-gradient(90deg, transparent 0 8%, rgba(65, 133, 135, .32) 8% 8.16%, transparent 8.16% 58%, rgba(65, 133, 135, .22) 58% 58.16%, transparent 58.16%),
          linear-gradient(0deg, transparent 0 22%, rgba(65, 133, 135, .26) 22% 22.2%, transparent 22.2% 71%, rgba(65, 133, 135, .18) 71% 71.2%, transparent 71.2%);
        background-size: 360px 240px, 360px 240px;
      }
      #mission-studio > * { position: relative; z-index: 1; }

      #mission-studio .agent-pipeline::before {
        animation: agent-bus .82s linear infinite;
        filter: drop-shadow(0 0 3px rgba(95, 207, 201, .36));
      }
      #mission-studio .agent-zone::after {
        filter: drop-shadow(0 0 4px rgba(100, 230, 223, .42));
      }
      .bus-progress {
        opacity: .72;
        stroke: #61e4dd;
        stroke-dasharray: 10 18;
        animation: apr-demo-svg-flow 1.35s linear infinite;
        filter: drop-shadow(0 0 3px rgba(97, 228, 221, .42));
      }
      @keyframes apr-demo-svg-flow { to { stroke-dashoffset: -56; } }
      .flow-packet { filter: drop-shadow(0 0 4px rgba(104, 247, 154, .62)); }
    }
"""


def render_mission_control_demo(csrf_token: str) -> str:
    """Render the main preview and add the desktop-only demo polish layer."""

    dashboard = _render_main_preview(csrf_token)
    marker = "  </style>"
    if marker not in dashboard:
        raise RuntimeError("Mission Control stylesheet marker is missing")
    return dashboard.replace(marker, _DEMO_LOCK_CSS + marker, 1)
