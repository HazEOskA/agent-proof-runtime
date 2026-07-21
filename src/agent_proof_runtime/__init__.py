"""Agent Proof Runtime public package."""

from .runtime import DemoRunResult, MissionRunResult, run_demo, run_mission
from .validator import VerificationResult, verify_bundle

# Mission Studio hotfix: the old 16 KiB CSS demo cap caused valid live CSS
# generations to fail before APR handoff. Use the manifest schema's maximum
# per-artifact allowance, which is effectively unbounded for model-generated CSS
# while keeping the runtime's global memory-safety boundary intact.
from .mission_studio_openai import ARTIFACT_LIMITS

ARTIFACT_LIMITS["site/styles.css"] = 1024 * 1024

__all__ = [
    "DemoRunResult",
    "MissionRunResult",
    "VerificationResult",
    "run_demo",
    "run_mission",
    "verify_bundle",
]
__version__ = "0.3.0"
