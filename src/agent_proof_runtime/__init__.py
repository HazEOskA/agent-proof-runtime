"""Agent Proof Runtime public package."""

from .runtime import DemoRunResult, run_demo
from .validator import VerificationResult, verify_bundle

__all__ = ["DemoRunResult", "VerificationResult", "run_demo", "verify_bundle"]
__version__ = "0.1.0"
