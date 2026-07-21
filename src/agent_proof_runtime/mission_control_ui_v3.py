"""Verified desktop mask alignment and animated signal flow for Mission Control."""

from __future__ import annotations

from .mission_control_ui_v2 import render_mission_control_v2 as _render_v2

_REDUCED_MOTION_KILL_SWITCH = r"""
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { animation: none !important; transition: none !important; }
    }
"""

_REDUCED_MOTION_WITH_ACTIVE_SIGNALS = r"""
    @media (prefers-reduced-motion: reduce) {
      html { scroll-behavior: auto; }
      *, *::before, *::after { transition: none !important; }
    }
"""

_UI_V3_CSS = r"""
    /* Move the existing OSA source 35px left from the reviewed effective baseline. */
    @media (min-width: 901px) {
      .brand-source {
        left: -43px;
        top: -62px;
      }
    }

    /* Keep the existing top signal moving in real browsers. */
    .masthead::after {
      animation: apr-top-bus 1.2s linear infinite !important;
      animation-play-state: running !important;
      will-change: background-position;
    }

    /* Continue that signal vertically through the current page flow. */
    main {
      position: relative;
    }
    main::before {
      content: "";
      position: absolute;
      z-index: 4;
      top: -88px;
      right: 18px;
      bottom: 0;
      width: 2px;
      pointer-events: none;
      background-color: #39777b;
      background-image: repeating-linear-gradient(
        180deg,
        transparent 0 10px,
        #4fe5dd 10px 16px,
        transparent 16px 27px
      );
      background-size: 2px 27px;
      animation: apr-main-flow-down .9s linear infinite !important;
      animation-play-state: running !important;
      will-change: background-position;
    }
    @keyframes apr-main-flow-down {
      from { background-position: 0 0; }
      to { background-position: 0 27px; }
    }

    @media (max-width: 640px) {
      main::before {
        top: -166px;
        right: 12px;
      }
    }
"""


def render_mission_control_v3(csrf_token: str) -> str:
    """Render Mission Control with the verified mask position and active flow."""

    dashboard = _render_v2(csrf_token)
    if _REDUCED_MOTION_KILL_SWITCH not in dashboard:
        raise RuntimeError("Mission Control reduced-motion rule is missing")
    dashboard = dashboard.replace(
        _REDUCED_MOTION_KILL_SWITCH,
        _REDUCED_MOTION_WITH_ACTIVE_SIGNALS,
        1,
    )

    marker = "  </style>"
    if marker not in dashboard:
        raise RuntimeError("Mission Control stylesheet marker is missing")
    return dashboard.replace(marker, _UI_V3_CSS + marker, 1)
