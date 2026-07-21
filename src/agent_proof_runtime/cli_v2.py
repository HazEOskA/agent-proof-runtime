"""CLI entrypoint that activates the final Mission Control presentation layer."""

from __future__ import annotations

from typing import Sequence

from . import mission_control
from .cli import main as _base_main
from .mission_control_ui_demo import render_mission_control_demo


def main(argv: Sequence[str] | None = None) -> int:
    """Run APR while replacing only the Mission Control HTML renderer."""

    mission_control.render_mission_control = render_mission_control_demo
    return _base_main(argv)
