"""Verified desktop mask alignment layer for Mission Control."""

from __future__ import annotations

from .mission_control_ui_v2 import render_mission_control_v2 as _render_v2

_UI_V3_CSS = r"""
    /* Move the existing OSA source 35px left from the reviewed effective baseline. */
    @media (min-width: 901px) {
      .brand-source {
        left: -43px;
        top: -62px;
      }
    }
"""


def render_mission_control_v3(csrf_token: str) -> str:
    """Render Mission Control with the verified desktop mask position."""

    dashboard = _render_v2(csrf_token)
    marker = "  </style>"
    if marker not in dashboard:
        raise RuntimeError("Mission Control stylesheet marker is missing")
    return dashboard.replace(marker, _UI_V3_CSS + marker, 1)
